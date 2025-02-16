from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
from datetime import datetime
from utils.request_utils import fetch_page
from utils.log_utils import setup_logger, get_logger
from utils.format_utils import save_jobs_to_xml
import time

def parse_job_list(html_content):
    """Parse job listing information from HTML content"""
    logger = get_logger(__name__)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the job listings container
    content_div = soup.find('div', {'class': 'content'})
    if not content_div:
        logger.error("Could not find content div")
        return []
        
    jobs = []
    
    # Process each job listing
    for job_item in content_div.find_all('li'):
        try:
            # Extract date
            date_div = job_item.find('div', {'class': 'date'})
            if not date_div:
                continue
                
            day = date_div.find('span', {'class': 'day'}).text.strip()
            year = date_div.find('span', {'class': 'year'}).text.strip()
            publish_date = f"{year}.{day}"
            
            # Extract title and URL
            title_div = job_item.find('div', {'class': 'title1'})
            if not title_div or not title_div.find('a'):
                continue
                
            title_link = title_div.find('a')
            title = title_link.text.strip()
            url = f"https://career.nankai.edu.cn{title_link['href']}"
            
            # Extract company info
            company_div = job_item.find('div', {'class': 'company'})
            if not company_div:
                continue
                
            company_text = company_div.text.strip()
            company_parts = company_text.split('/')
            
            # Create job dict
            job = {
                'title': company_parts[0].strip(),
                'url': url,
                'publish_date': publish_date,
                'company': company_parts[0].strip(),
                'location': company_parts[1].strip() if len(company_parts) > 1 else '',
                'description': title,
                'type': '招聘信息'
            }
            
            # Add additional info if available
            if len(company_parts) > 2:
                job['position_type'] = company_parts[2].strip()
            if len(company_parts) > 3:
                job['education'] = company_parts[3].strip()
            if len(company_parts) > 4:
                job['salary'] = company_parts[4].strip()
            
            jobs.append(job)
            logger.debug(f"Added job: {job['title']}")
            
        except Exception as e:
            logger.error(f"Error parsing job item: {str(e)}")
            continue
    
    if not jobs:
        logger.warning("No jobs were found in the HTML content")
    else:
        logger.info(f"Found {len(jobs)} job listings")
        
    return jobs

def get_max_page(html_content):
    """Extract maximum page number from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    pagination = soup.find('div', {'class': 'page'})
    if not pagination:
        return 1
        
    # Find the last page number
    end_link = pagination.find('a', {'class': 'end'})
    if end_link:
        match = re.search(r'/p/(\d+)\.html', end_link['href'])
        if match:
            return int(match.group(1))
    
    return 1

# def save_jobs_to_xml(jobs, output_path, mode='w'):
#     """Save jobs to XML file"""
#     if mode == 'a' and output_path.exists():
#         # Load existing content
#         with open(output_path, 'r', encoding='utf-8') as f:
#             content = f.read()
#         soup = BeautifulSoup(content, 'lxml-xml')
#         jobs_elem = soup.find('jobs')
#     else:
#         # Create new XML structure
#         content = '<?xml version="1.0" encoding="UTF-8"?>\n<jobs>\n</jobs>'
#         soup = BeautifulSoup(content, 'lxml-xml')
#         jobs_elem = soup.find('jobs')

#     # Add new jobs
#     for job in jobs:
#         job_elem = soup.new_tag('job')
        
#         # Add basic info
#         for key in ['title', 'url', 'publish_date', 'company', 'type', 'location']:
#             if key in job:
#                 elem = soup.new_tag(key)
#                 elem.string = job[key]
#                 job_elem.append(elem)
        
#         # Add optional info
#         for key in ['position_type', 'education', 'salary']:
#             if key in job:
#                 elem = soup.new_tag(key)
#                 elem.string = job[key]
#                 job_elem.append(elem)
        
#         jobs_elem.append(job_elem)
#         jobs_elem.append(soup.new_string('\n'))

#     # Save to file
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(str(soup.prettify()))

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
    base_url = "https://career.nankai.edu.cn/correcruit/index/p/{}.html"
    
    # Setup output path
    output_dir = Path('data/xml')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'nankai_jobs.xml'
    
    # Load existing jobs
    existing_jobs = load_existing_jobs(output_path) if output_path.exists() else []
    existing_urls = {job['url'] for job in existing_jobs}
    
    # Start with page 1
    current_page = 1
    max_page = 2
    all_new_jobs = []
    
    while True:
        url = base_url.format(current_page)
        logger.info(f"Processing page {current_page}")
        
        # Fetch HTML content
        html_content = fetch_page(url)
        if not html_content:
            logger.error(f"Failed to fetch page {current_page}")
            break
            
        # Get max page number on first page
        if max_page is None:
            max_page = get_max_page(html_content)
            logger.info(f"Total pages: {max_page}")
            
        # Parse jobs
        new_jobs = [job for job in parse_job_list(html_content) 
                   if job['url'] not in existing_urls]
        
        if new_jobs:
            all_new_jobs.extend(new_jobs)
            existing_urls.update(job['url'] for job in new_jobs)
            logger.info(f"Found {len(new_jobs)} new jobs on page {current_page}")
        else:
            logger.info(f"No new jobs found on page {current_page}")
            
        # Break if we've reached the last page
        if current_page >= max_page:
            break
            
        current_page += 1
        time.sleep(2)  # Add delay between requests
        
    # Save all new jobs
    if all_new_jobs:
        save_jobs_to_xml(all_new_jobs, output_path, '南开大学', mode='a' if existing_jobs else 'w')

        logger.info(f"Saved {len(all_new_jobs)} new jobs to {output_path}")
    else:
        logger.info("No new jobs to save")

if __name__ == '__main__':
    main() 