from flask import Flask, send_file
from pathlib import Path
import importlib
import logging
import sys

# Add src directory to Python path
sys.path.append('src')

from src.utils.log_utils import setup_logger

app = Flask(__name__)
logger = setup_logger('rss_server')

# School code mapping
SCHOOL_CODES = {
    'fudan': {'module': 'src.fudan_job_crawl', 'name': '复旦大学'},
    'sjtu': {'module': 'src.sjtu_job_crawl', 'name': '上海交通大学'},
    'tongji': {'module': 'src.tongji_job_crawl', 'name': '同济大学'},
    'hust': {'module': 'src.hust_job_crawl', 'name': '华中科技大学'},
    'nankai': {'module': 'src.nankai_job_crawl', 'name': '南开大学'},
    'dlut': {'module': 'src.dlut_job_crawl', 'name': '大连理工大学'}
}

def run_crawler(school_code):
    """Run the crawler for specified school"""
    try:
        # Import crawler module dynamically
        module = importlib.import_module(SCHOOL_CODES[school_code]['module'])
        # Run crawler
        module.main()
        return True
    except Exception as e:
        logger.error(f"Error running crawler for {school_code}: {str(e)}")
        return False

@app.route('/')
def index():
    """Show available RSS feeds"""
    links = []
    for code, info in SCHOOL_CODES.items():
        links.append(f'<li><a href="/rss/{code}">{info["name"]}</a></li>')
    
    html = f"""
    <h1>Available RSS Feeds</h1>
    <ul>
        {''.join(links)}
        <li><a href="/rss/all">All Schools</a></li>
    </ul>
    """
    return html

@app.route('/rss/<school_code>')
def get_rss(school_code):
    """Handle RSS request for a school"""
    if school_code not in SCHOOL_CODES:
        return f"Invalid school code: {school_code}", 404
        
    logger.info(f"RSS request received for {SCHOOL_CODES[school_code]['name']}")
    
    # Run crawler
    run_crawler(school_code)
    
    # Return XML file
    xml_path = Path('data/xml') / f'{school_code}_jobs.xml'
    if not xml_path.exists():
        return f"XML file not found for {school_code}", 404
        
    return send_file(
        xml_path,
        mimetype='application/xml',
        as_attachment=False,
        download_name=f'{school_code}_jobs.xml'
    )

@app.route('/rss/all')
def get_all_rss():
    """Run all crawlers and return list of XML files"""
    results = []
    for school_code in SCHOOL_CODES:
        success = run_crawler(school_code)
        results.append({
            'school': SCHOOL_CODES[school_code]['name'],
            'success': success
        })
    return {'results': results}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001) 