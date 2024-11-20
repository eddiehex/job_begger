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
    
    # Find all tables with class 'fdhy_tb002'
    tables = soup.find_all('table', {'class': 'fdhy_tb002'})
    logger.info(f"Found {len(tables)} tables with class 'fdhy_tb002'")
    
    # The job listings should be in the last table
    if not tables:
        logger.error("Error: Could not find any tables")
        return []
        
    # Get the last table which contains job listings
    job_table = tables[-1]
    jobs = []
    
    # Process each row in the table
    for row in job_table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) != 2:  # Skip rows that don't have exactly 2 columns
            continue
            
        job_col = cols[0]
        date_col = cols[1]
        
        # Skip header row
        if '发布时间' in date_col.text:
            continue
            
        # Extract job link and title
        job_link = job_col.find('a', href=re.compile(r'/zpinfo1/.*\.htm'))
        if not job_link:
            continue
            
        # Extract date (remove square brackets)
        date_match = re.search(r'\[(.*?)\]', date_col.text.strip())
        if not date_match:
            continue
            
        job = {
            'title': job_link.get('title', '').strip(),
            'url': f"https://job.hust.edu.cn{job_link['href']}",
            'publish_date': date_match.group(1),
            'type': '招聘信息'  # Default type
        }
        
        # Extract job type from the category link
        type_link = job_col.find('a', href=re.compile(r'/searchJob\.jspx'))
        if type_link:
            job['type'] = type_link.text.strip('[]')
            
        jobs.append(job)
        logger.debug(f"Added job: {job['title']}")
        
    if not jobs:
        logger.warning("No jobs were found in the HTML content")
    else:
        logger.info(f"Found {len(jobs)} job listings")
        
    return jobs

def get_max_page(html_content):
    """Extract maximum page number from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    pagination = soup.find('ul', {'class': 'pagination'})
    if not pagination:
        return 1
        
    # Find all page links
    page_links = pagination.find_all('a', href=re.compile(r'searchJob_\d+\.jspx'))
    if not page_links:
        return 1
        
    # Extract page numbers and find the maximum
    page_numbers = []
    for link in page_links:
        match = re.search(r'searchJob_(\d+)\.jspx', link['href'])
        if match:
            page_numbers.append(int(match.group(1)))
            
    return max(page_numbers) if page_numbers else 1

def load_existing_jobs(output_path):
    """Load existing jobs from XML file"""
    if not output_path.exists():
        return []
        
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'lxml-xml')
    existing_jobs = []
    
    for job_elem in soup.find_all('job'):
        job = {
            'title': job_elem.find('title').text,
            'url': job_elem.find('url').text,
            'type': job_elem.find('type').text,
            'publish_date': job_elem.find('publish_date').text
        }
        existing_jobs.append(job)
        
    return existing_jobs

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
        
#         title_elem = soup.new_tag('title')
#         title_elem.string = job['title']
#         job_elem.append(title_elem)
        
#         url_elem = soup.new_tag('url')
#         url_elem.string = job['url']
#         job_elem.append(url_elem)
        
#         type_elem = soup.new_tag('type')
#         type_elem.string = job['type']
#         job_elem.append(type_elem)
        
#         date_elem = soup.new_tag('publish_date')
#         date_elem.string = job['publish_date']
#         job_elem.append(date_elem)
        
#         jobs_elem.append(job_elem)
#         jobs_elem.append(soup.new_string('\n'))

#     # Save to file
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(str(soup.prettify()))

def main():
    # Setup logging
    logger = setup_logger(__name__)
    
    # Base URL
    base_url = "https://job.hust.edu.cn/searchJob_{}.jspx?fbsj=&q=&type=2"
    
    # Setup output path
    output_dir = Path('data/xml')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'hust_jobs.xml'
    
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
        save_jobs_to_xml(all_new_jobs, output_path, '华中科技大学', mode='a' if existing_jobs else 'w')

        logger.info(f"Saved {len(all_new_jobs)} new jobs to {output_path}")
    else:
        logger.info("No new jobs to save")

if __name__ == '__main__':
    main()
