from pathlib import Path
import logging
import sys

try:
    # pyrefly: ignore [missing-import]
    import colorlog
    USE_COLOR = True 
except ImportError:
    USE_COLOR = False 
    
try:
    from config import LOG_LEVEL, LOG_DIR
except ImportError:
    LOG_LEVEL = "INFO"
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)

def get_logger(name: str)-> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    level = getattr(logging,LOG_LEVEL.upper(),logging.INFO)
    logger.setLevel(level)
    
    if USE_COLOR:
        fmt= colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | %(name)-25s | %(message)s",
            datefmt = "%H:%M:%S",
            log_colors = {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors = {},
            style = '%',
        )
    else:
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt = "%H:%M:%S"
        )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    file_path = LOG_DIR / "medbot.log"
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)
    
    return logger

if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")   