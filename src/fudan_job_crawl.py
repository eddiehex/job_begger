from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
from datetime import datetime
from utils.request_utils import fetch_page_post
from utils.log_utils import setup_logger, get_logger
from utils.format_utils import save_jobs_to_xml
import time

def parse_job_list(json_content):
    """Parse job listing information from JSON content"""
    logger = get_logger(__name__)
    
    try:
        data = json.loads(json_content)
        if data['code'] != 0:
            logger.error(f"API returned error code: {data['code']}")
            return []
            
        jobs_data = data['data']['list']
        jobs = []
        
        for job_item in jobs_data:
            try:
                # Convert timestamp to date
                publish_date = datetime.fromtimestamp(
                    int(job_item['addtime'])
                ).strftime('%Y-%m-%d')
                
                job = {
                    'title': job_item['title'].strip(),
                    'company': job_item['com_id_name'].strip(),
                    'publish_date': publish_date,
                    'location': job_item.get('province_id_name', ''),
                    'type': '招聘信息',
                    'url': f"https://career.fudan.edu.cn/detail/enrollment/{job_item['id']}"
                }
                
                # Add remarks if available
                if job_item.get('remarks'):
                    job['description'] = job_item['remarks'].strip()
                
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
        
#         # Add all job fields
#         for key, value in job.items():
#             elem = soup.new_tag(key)
#             elem.string = value
#             job_elem.append(elem)
        
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
    
    # API URL
    url = "https://career.fudan.edu.cn/mobile.php/enrollment/getlist"
    
    # Request headers
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://career.fudan.edu.cn',
        'Referer': 'https://career.fudan.edu.cn/Zhaopin/zhaopinList.html?type=1&page=1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'auth': 'Baisc MTAyNDY6MTAyNDY=',
    }
    
    # Request data
    data = {
        'type': '1',
        'school_id': '5f431052-b4af-0969-a37a-955f7903c8d5',
        'page': '1',
        'size': '20',
        'login_user_id': '1',
        'login_admin_school_code': '10246',
        'login_admin_school_id': '5f431052-b4af-0969-a37a-955f7903c8d5'
    }
    
    # Setup output path
    output_dir = Path('data/xml')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'fudan_jobs.xml'
    
    # Load existing jobs
    existing_jobs = load_existing_jobs(output_path) if output_path.exists() else []
    existing_urls = {job['url'] for job in existing_jobs}
    
    all_new_jobs = []
    current_page = 1
    
    while current_page <= 2:
        logger.info(f"Processing page {current_page}")
        
        # Update page number in request data
        data['page'] = str(current_page)
        
        # Fetch JSON content
        json_content = fetch_page_post(url, headers=headers, data=data)
        if not json_content:
            logger.error(f"Failed to fetch page {current_page}")
            break
            
        # Parse jobs
        new_jobs = [job for job in parse_job_list(json_content) 
                   if job['url'] not in existing_urls]
        
        if not new_jobs:
            logger.info(f"No new jobs found on page {current_page}")
            break
            
        all_new_jobs.extend(new_jobs)
        existing_urls.update(job['url'] for job in new_jobs)
        logger.info(f"Found {len(new_jobs)} new jobs on page {current_page}")
        
        current_page += 1
        time.sleep(2)  # Add delay between requests
        
    # Save all new jobs
    if all_new_jobs:
        save_jobs_to_xml(all_new_jobs, output_path, '复旦大学', mode='a' if existing_jobs else 'w')

        logger.info(f"Saved {len(all_new_jobs)} new jobs to {output_path}")
    else:
        logger.info("No new jobs to save")

if __name__ == '__main__':
    main() 