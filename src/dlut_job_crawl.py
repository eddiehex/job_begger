from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
from datetime import datetime
from utils.request_utils import fetch_page
from utils.log_utils import setup_logger, get_logger
import time

def parse_job_list(json_content):
    """Parse job listing information from JSON content"""
    logger = get_logger(__name__)
    
    try:
        data = json.loads(json_content)
        jobs_data = data.get('newsDTOS', [])
        jobs = []
        
        for job_item in jobs_data:
            try:
                job = {
                    'title': job_item['title'].strip(),
                    'id': job_item['id'],
                    'publish_date': job_item['publishDate'],
                    'recruiter_date': job_item['recruiterDate'],
                    'type': '招聘信息',
                    'url': f"https://job.dlut.edu.cn/portals/detail.html?id={job_item['id']}",
                    'views': str(job_item['pv'])
                }
                
                jobs.append(job)
                logger.debug(f"Added job: {job['title']}")
                
            except Exception as e:
                logger.error(f"Error parsing job item: {str(e)}")
                continue
                
        logger.info(f"Found {len(jobs)} job listings")
        return jobs
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return []

def save_jobs_to_xml(jobs, output_path, mode='w'):
    """Save jobs to XML file"""
    if mode == 'a' and output_path.exists():
        # Load existing content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'lxml-xml')
        jobs_elem = soup.find('jobs')
    else:
        # Create new XML structure
        content = '<?xml version="1.0" encoding="UTF-8"?>\n<jobs>\n</jobs>'
        soup = BeautifulSoup(content, 'lxml-xml')
        jobs_elem = soup.find('jobs')

    # Add new jobs
    for job in jobs:
        job_elem = soup.new_tag('job')
        
        # Add all job fields
        for key, value in job.items():
            elem = soup.new_tag(key)
            elem.string = value
            job_elem.append(elem)
        
        jobs_elem.append(job_elem)
        jobs_elem.append(soup.new_string('\n'))

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))

def load_existing_jobs(output_path):
    """Load existing jobs from XML file"""
    if not output_path.exists():
        return []
        
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'lxml-xml')
    existing_jobs = []
    
    for job_elem in soup.find_all('job'):
        job = {}
        for elem in job_elem.children:
            if elem.name:  # Skip NavigableString objects
                job[elem.name] = elem.text
        existing_jobs.append(job)
        
    return existing_jobs

def main():
    # Setup logging
    logger = setup_logger(__name__)
    
    # Base URL
    base_url = "https://job.dlut.edu.cn/portals/ZCMoreNews"
    
    # Request headers
    headers = {
        'Accept': '*/*',
        'Referer': 'https://job.dlut.edu.cn/portals/newslist.html?newsColumn=08',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # Setup output path
    output_dir = Path('data/xml')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'dlut_jobs.xml'
    
    # Load existing jobs
    existing_jobs = load_existing_jobs(output_path) if output_path.exists() else []
    existing_urls = {job['url'] for job in existing_jobs}
    
    all_new_jobs = []
    max_pages = 2
    
    for page in range(max_pages):
        logger.info(f"Processing page {page + 1}/{max_pages}")
        
        # Construct URL with parameters
        url = f"{base_url}?name=&startDate=&endDate=&page={page}&size=15"
        
        # Fetch JSON content
        json_content = fetch_page(url)
        if not json_content:
            logger.error(f"Failed to fetch page {page + 1}")
            break
            
        # Parse jobs
        new_jobs = [job for job in parse_job_list(json_content) 
                   if job['url'] not in existing_urls]
        
        if not new_jobs:
            logger.info(f"No new jobs found on page {page + 1}")
            break
            
        all_new_jobs.extend(new_jobs)
        existing_urls.update(job['url'] for job in new_jobs)
        logger.info(f"Found {len(new_jobs)} new jobs on page {page + 1}")
        
        time.sleep(2)  # Add delay between requests
        
    # Save all new jobs
    if all_new_jobs:
        save_jobs_to_xml(all_new_jobs, output_path, 
                        mode='a' if existing_jobs else 'w')
        logger.info(f"Saved {len(all_new_jobs)} new jobs to {output_path}")
    else:
        logger.info("No new jobs to save")

if __name__ == '__main__':
    main() 