from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

job_description_prompt = ChatPromptTemplate(
    messages=[
        SystemMessage("You are a world class algorithm for extracting information."),
        SystemMessage(
            "Be short and concise. Be articulate, no need to be verbose and justify your answer."
        ),
        SystemMessage("Extract the following information from the job posting:\n"),
    ],
)


# Pydantic JobDescription
class JobDescription(BaseModel):
    """Description of a job posting"""

    company: str = Field(description="Name of the company that has the job opening")
    job_title: str = Field(description="Job title")
    team: str = Field(
        description="Name of the team within the company. Team name should be Not Found if it's not known.",
    )
    job_summary: str = Field(description="Brief summary of the job, not exceeding 100 words")
    salary: str = Field(
        description="Salary amount or range. Salary should be Not Found if it's not known.",
    )
    duties: list[str] = Field(
        default=[],
        description="The role, responsibilities and duties of the job as an list, not exceeding 500 words",
    )
    qualifications: list[str] = Field(
        default=[],
        description="The qualifications, skills, and experience required for the job as an list, not exceeding 500 words",
    )
    is_fully_remote: str = Field(
        description="Does the job have an option to work fully (100%) remotely or if relocation is available? Hybrid or partial remote is marked as `False`. Use `None` if the answer is not known.",
    )


class JobSkills(BaseModel):
    """Skills from a job posting"""

    technical_skills: list[str] = Field(
        default=[],
        description="An list of technical skills, including programming languages, technologies, and tools.",
        examples="[Python, MS Office, Machine learning, Marketing, Optimization, GPT]",
    )
    non_technical_skills: list[str] = Field(
        default=[],
        description="An list of non-technical Soft skills.",
        examples="[Communication, Leadership, Adaptability, Teamwork, Problem solving, Critical thinking, Time management]",
    )
    certifications: list[str] = Field(
        default=[],
        description="An list of certifications, licenses, and qualifications required for the job.",
        examples="[PMP, AWS Certified Solutions Architect, Google Analytics, Scrum Master, Six Sigma]",
    )
    experience: str = Field(
        default=[],
        description="The work experience required for the job.",
        examples="5+ years of experience in software development",
    )
    languages: list[str] = Field(
        default=[],
        description="An list of languages required for the job.",
        examples="[English, Spanish, French, German, Chinese, Japanese]",
    )
