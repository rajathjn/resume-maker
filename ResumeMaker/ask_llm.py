import logging
import platform
import subprocess
import time

import ollama
import psutil
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from .utils import get_logger


class OllamaServiceManager:
    """
    Manages the Ollama service, including starting, stopping, and checking its status.

    Attributes:
        system (str): The operating system the service is running on (e.g., "windows", "linux").
        process (subprocess.Popen | None): The process object for the running Ollama service.
        ollama (module): The ollama module.
        logger (logging.Logger): The logger instance for the class.
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes the OllamaServiceManager.

        Args:
            logger (logging.Logger | None, optional): An optional logger instance. If not provided, a default logger is created. Defaults to None.
        """
        self.system = platform.system().lower()
        self.process = None
        self.ollama = ollama

        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.name = "OllamaServiceManager"
        self.logger.info(f"Ollama service ollama_service_manager initialized on {self.system}")

    def start_service(self) -> bool:
        """
        Starts the Ollama service.

        Returns:
            bool: True if the service started successfully, False otherwise.

        Raises:
            Exception: If there is an error starting the service.
        """
        self.logger.info("Starting Ollama service")
        try:
            if self.system == "windows":
                ollama_execution_command = ["ollama app.exe", "serve"]
            else:
                ollama_execution_command = ["ollama", "serve"]
            self.process = subprocess.Popen(
                ollama_execution_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Wait a moment for the service to start
            time.sleep(2)

            # Check if the service started successfully
            if self.process.poll() is None:
                self.logger.info("Ollama service started successfully")
                return True
        except Exception as e:
            self.logger.error(f"Error starting Ollama service: {str(e)}")
            raise e
            return False

    def stop_service(self) -> bool:
        """
        Stops the Ollama service.

        Returns:
            bool: True if the service stopped successfully, False otherwise.
        """
        try:
            if self.process:
                if self.system == "windows":
                    # For Windows
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "ollama app.exe"], capture_output=True, text=True
                    )
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True, text=True
                    )
                else:
                    # For Linux/MacOS
                    self.process.terminate()
                    self.process.wait(timeout=5)
                del self.process
                self.process = None
                self.logger.info("Ollama service stopped successfully")
                return True
            else:
                self.logger.warning("Ollama service either started by user or has already stopped")
                return False

        except Exception as e:
            print(f"Error stopping Ollama service: {str(e)}")
            return False

    @staticmethod
    def is_ollama_running():
        """
        Checks if any Ollama process is currently running.

        Returns:
            bool: True if an Ollama process is running, False otherwise.
        """
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                if "ollama" in proc.info["name"].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def is_service_running(self) -> bool:
        """
        Checks if the Ollama service managed by this instance is running.

        Returns:
            bool: True if the service is running, False otherwise.
        """
        if self.process and self.process.poll() is None:
            return True
        if self.is_ollama_running():
            return True
        return False

    def get_running_models(self):
        """
        Gets a list of the currently running models on Ollama.

        Returns:
            list: The models running in ollama service.
        """
        return self.ollama.ps()

    def stop_running_model(self, model_name: str):
        """
        Stops a specific model that is running in Ollama.

        Args:
            model_name (str): The name of the model to stop.

        Returns:
            bool: True if the model was stopped successfully, False otherwise.
        """
        try:
            stop_attempt = subprocess.check_output(
                ["ollama", "stop", model_name], stderr=subprocess.STDOUT, text=True
            )
            self.logger.info(
                f"Ollama service with {model_name} stopped successfully: {stop_attempt}"
            )
            return True
        except Exception as e:
            self.logger.warning(f"Failed to stop {model_name}")
            self.logger.warning(
                "Either the model was already stopped, or the Ollama service is already stopped"
            )
            self.logger.error(f"Error stopping Ollama service: {str(e)}")
            return False

    def get_llm_model(self, model_name: str):
        """
        Downloads a specific LLM model using Ollama.

        Args:
            model_name (str): The name of the model to download.
        """
        return self.ollama.pull(model_name)

    def get_list_of_downloaded_files(self) -> list[str]:
        """
        Retrieves a list of models that have been downloaded by Ollama.

        Returns:
            list[str]: A list of the names of the downloaded models.
        """
        model_list = []
        try:
            model_list = list(self.ollama.list())  # list[tuple[model, list[models]]]
            model_list = [i.model for i in model_list[0][1]]
        except Exception as e:
            self.logger.error(f"Error getting list of downloaded files: {str(e)}")
        return model_list


class AskLLM:
    """
    A class to interact with a Large Language Model (LLM) using Ollama.

    This class handles loading, querying, and managing the LLM, including
    starting and stopping the Ollama service if necessary.
    """

    def __init__(
        self,
        model_name: str = "llama3.1:latest",
        temperature: float = 0,
    ) -> None:
        """
        Initializes the AskLLM instance.

        Args:
            config_file (Path | str): The path to the configuration file.
            model_name (str, optional): The name of the LLM model to use. Defaults to "llama3.1:latest".
            temperature (float, optional): The temperature parameter for the LLM. Defaults to 0.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the configuration file is not a YAML file.
        """
        self.logger = get_logger(__name__)

        self.self_started_ollama: bool = False
        self.ollama_service_manager = OllamaServiceManager(logger=self.logger)
        self.model_name = model_name
        self.model_temperature = temperature
        self.llm: ChatOllama = self._load_llm_model(self.model_name, self.model_temperature)
        self.structured_llm = None

    def _load_llm_model(self, model_name: str, temperature: float) -> ChatOllama:
        """
        Loads the specified LLM model.

        Starts the Ollama service if it's not already running, and downloads the model if it's not already downloaded.

        Args:
            model_name (str): The name of the model to load.
            temperature (float): The temperature parameter for the LLM.

        Returns:
            ChatOllama: The loaded ChatOllama instance.
        """
        if not self.ollama_service_manager.is_service_running():
            self.logger.warning("Ollama service is not running. Attempting to start it.")
            self.ollama_service_manager.start_service()
            self.self_started_ollama = True
            self.logger.warning(f"Self started ollama service: {self.self_started_ollama}")
        self.logger.info("Ollama service found")

        if model_name not in self.ollama_service_manager.get_list_of_downloaded_files():
            self.logger.info(f"Downloading model {model_name}")
            self.ollama_service_manager.get_llm_model(model_name)
            self.logger.info(f"Model {model_name} downloaded")
        else:
            self.logger.info(f"Model {model_name} already downloaded")

        return ChatOllama(model=model_name, temperature=temperature)

    def invoke(
        self,
        input: str,
        prompt: ChatPromptTemplate,
        OutParser: BaseModel,
        return_raw_output: bool = True,
    ) -> dict | BaseModel:
        """
        Invokes the LLM with the given input text and returns a structured output.

        This method uses a predefined prompt to query the LLM and expects a response that conforms to the YoutubeDetails schema.

        Args:
            input_text (str): The input text to send to the LLM.

        Returns:
            dict | BaseModel: A dictionary or a BaseModel instance containing the LLM's response.
        """
        prompt.messages.append(HumanMessage(content=input))
        self.structured_llm = self.llm.with_structured_output(
            OutParser, include_raw=return_raw_output
        )
        return self.structured_llm.invoke(prompt.messages)

    def quit_llm(self):
        """
        Shuts down the LLM and the Ollama service if it was started by this instance.

        This method stops any running models, and if the Ollama service was started by this
        instance, it stops the service as well. Finally, it deletes the instance variables to
        clean up.
        """
        self.ollama_service_manager.stop_running_model(self.model_name)
        if self.self_started_ollama:
            self.ollama_service_manager.stop_service()
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
