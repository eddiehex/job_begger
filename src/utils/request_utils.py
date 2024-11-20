import requests
import time
from utils.log_utils import get_logger

def fetch_page(url, max_retries=3, retry_delay=5):
    """
    Fetch HTML content from given URL with retry mechanism
    
    Args:
        url: Target URL
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        str: HTML content if successful, None if failed
    """
    logger = get_logger(__name__)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching URL: {url} (Attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check if response is HTML
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type.lower():
                logger.warning(f"Unexpected content type: {content_type}")
            
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Error fetching URL: {url}")
            logger.error(f"Exception: {str(e)}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Giving up.")
                return None
    
    return None 

def fetch_page_post(url, headers=None, data=None, max_retries=3, retry_delay=5):
    """
    Fetch content from given URL using POST request with retry mechanism
    
    Args:
        url: Target URL
        headers: Request headers
        data: POST data
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        str: Response content if successful, None if failed
    """
    logger = get_logger(__name__)
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Posting to URL: {url} (Attempt {attempt + 1}/{max_retries})")
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Error posting to URL: {url}")
            logger.error(f"Exception: {str(e)}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Giving up.")
                return None
    
    return None 