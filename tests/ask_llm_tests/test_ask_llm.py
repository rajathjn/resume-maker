from unittest.mock import MagicMock, patch

import pytest

from ResumeMaker.ask_llm import AskLLM, OllamaServiceManager


@pytest.fixture
def mock_ollama_service_manager():
    """
    Fixture to provide a mocked instance of OllamaServiceManager.

    Returns:
        MagicMock: A mocked instance of OllamaServiceManager with predefined return values for start_service and stop_service methods.
    """
    ollama_service_manager = MagicMock(OllamaServiceManager)
    ollama_service_manager.start_service.return_value = True
    ollama_service_manager.stop_service.return_value = True
    return ollama_service_manager


@patch("ShortsMaker.ask_llm.AskLLM._load_llm_model")
def test_llm_model_loading(mock_load_llm_model, mock_ollama_service_manager, setup_file):
    AskLLM(config_file=setup_file, model_name="test_model")
    mock_load_llm_model.assert_called_once_with("test_model", 0)


@patch("ShortsMaker.ask_llm.AskLLM._load_llm_model")
@patch("ShortsMaker.ask_llm.OllamaServiceManager.stop_service")
@patch("ShortsMaker.ask_llm.subprocess.check_output")
@patch("ShortsMaker.ask_llm.subprocess.run")
def test_quit_llm_with_self_started_service(
    mock_load_llm_model,
    mock_stop_service,
    mock_check_output,
    mock_run,
    setup_file,
    mock_ollama_service_manager,
):
    mock_load_llm_model.return_value = None

    ask_llm = AskLLM(config_file=setup_file, model_name="test_model")
    ask_llm.self_started_ollama = True

    result = ask_llm.quit_llm()
    assert result is None
    mock_stop_service.assert_called_once()
