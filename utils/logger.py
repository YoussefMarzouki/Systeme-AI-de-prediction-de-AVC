from loguru import logger
from pathlib import Path
import sys

def setup_logger():
    logger.remove()
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    logger.add(sys.stdout, level="INFO")
    logger.add(log_path / "ai_module.log", rotation="1 MB", level="INFO")
    
    return logger

logger = setup_logger()
