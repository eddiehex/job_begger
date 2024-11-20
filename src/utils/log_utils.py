import logging
from pathlib import Path
from datetime import datetime

def setup_logger(name=None):
    """Setup logger configuration
    
    Args:
        name: Optional logger name. If None, returns root logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path('src/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file with timestamp
    log_file = log_dir / f'crawler_{datetime.now().strftime("%Y%m%d")}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(name) if name else logging.getLogger()

def get_logger(name=None):
    """Get a logger instance
    
    Args:
        name: Optional logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name) if name else logging.getLogger() 