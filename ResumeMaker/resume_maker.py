import json
import subprocess
import tempfile
from pathlib import Path
from pprint import pformat

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from .ask_llm import AskLLM
from .prompts import JobDescription, JobSkills, job_description_prompt
from .utils import get_logger


class ResumeMaker:
    def __init__(self, cache_dir: str | Path = "cache", ollama_model: str = "llama3.1:latest"):
        cache_dir = Path(cache_dir)
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger()
        self.ask_llm = AskLLM(model_name=ollama_model)

    def get_info_from_job_description(
        self, input: str, return_raw_output: bool = False
    ) -> dict | BaseModel:
        job_description = self.ask_llm.invoke(
            input=input,
            prompt=job_description_prompt,
            OutParser=JobDescription,
            return_raw_output=return_raw_output,
        )
        job_skills = self.ask_llm.invoke(
            input=input,
            prompt=job_description_prompt,
            OutParser=JobSkills,
            return_raw_output=return_raw_output,
        )
        if return_raw_output:
            self.logger.info(f"return_raw_output is set to {return_raw_output}")
            self.logger.debug(f"Job description: {pformat(job_description)}")
            self.logger.debug(f"Job skills: {pformat(job_skills)}")
            return (job_description, job_skills)
        else:
            data = job_description.model_dump() | job_skills.model_dump()
            self.logger.info(
                f"return_raw_output is set to {return_raw_output}, Saving to {self.cache_dir}/job_description.yml"
            )
            with open(self.cache_dir / "job_description.json", "w") as f:
                json.dump(data, f, indent=4)
            return data

    def generate_resume(
        self,
        resume_data: dict | str | Path,
        job_description_json: str | Path = "cache/job_description.json",
    ) -> dict:
        job_description_json = Path(job_description_json)
        if not job_description_json.exists():
            self.logger.error(f"Job description file not found in {job_description_json}")
            self.logger.error(
                "Please generate the job description first using `get_info_from_job_description` method"
            )
            return {}
        self.logger.info(
            f"Using the job description from {job_description_json}, to generate the resume"
        )

        self.logger.info("Load the Resume data")
        resume_data = (
            resume_data
            if isinstance(resume_data, dict)
            else yaml.safe_load(Path(resume_data).read_text())
        )

        # TODO: Logic for improving the resume

        self.logger.info("Resume Data generated successfully")
        self.logger.info(f"Updated resume data is stored in {self.cache_dir}/resume.json")
        with open(self.cache_dir / "resume.json", "w") as f:
            json.dump(resume_data, f, indent=4)
        return resume_data

    def improvise_resume(self) -> dict:
        if not (self.cache_dir / "resume.json").exists():
            self.logger.error(f"Resume file not found in {self.cache_dir}/resume.json")
            self.logger.error("Please generate the resume first using `generate_resume` method")
            return {}

        if not (self.cache_dir / "job_description.json").exists():
            self.logger.error(
                f"Job description file not found in {self.cache_dir}/job_description.json"
            )
            self.logger.error(
                "Please generate the job description first using `get_info_from_job_description` method"
            )
            return {}

        self.logger.info(
            f"Using the resume data from {self.cache_dir}/resume.json, to improvise the resume"
        )
        resume_data = json.loads(Path(self.cache_dir / "resume.json").read_text())
        self.logger.info("Improvise the resume data")
        return self.generate_resume(resume_data)

    def build_resume(self, resume_data: dict | str | Path) -> bool:
        resume_data = (
            resume_data
            if isinstance(resume_data, dict)
            else yaml.safe_load(Path(resume_data).read_text())
        )

        # Set up Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "templates"),
            trim_blocks=True,
        )
        template = env.get_template("resume.tex.j2")

        # Render the template with the resume data
        rendered_resume = template.render(**resume_data)

        with open(self.cache_dir / "resume.tex", "w") as f:
            f.write(rendered_resume)

        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_dir = Path(tmpdirname)
            # convert to pdf
            subprocess.check_output(
                [
                    "pdflatex",
                    f"--aux-directory={temp_dir}",
                    "--job-name=resume",
                    f"{self.cache_dir / 'resume.tex'}",
                ],
                stderr=subprocess.STDOUT,
                text=True,
            )

        self.logger.info(f"Resume latex file generated successfully in {self.cache_dir}/resume.tex")
        return True

    def quit(self) -> None:
        self.ask_llm.quit_llm()

        # Delete all instance variables
        for attr in list(self.__dict__.keys()):
            try:
                self.logger.debug(f"Deleting {attr}")
                if attr == "logger":
                    continue
                delattr(self, attr)
            except Exception as e:
                self.logger.error(f"Error deleting {attr}: {e}")
        delattr(self, "logger")
        return
