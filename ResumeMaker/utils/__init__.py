from .logging_config import configure_logging, get_logger

__all__ = [
    configure_logging,
    get_logger,
]

# Configure logging to their preferences
configure_logging()
