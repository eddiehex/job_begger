from email.utils import formatdate
from bs4 import BeautifulSoup
from datetime import datetime
def save_jobs_to_xml(jobs, output_path, school_name, mode='w'):
    """Save jobs to XML file in RSS format"""
    if mode == 'a' and output_path.exists():
        # Load existing content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'xml')
        channel = soup.find('channel')
        # Update lastBuildDate
        last_build_date = soup.find('lastBuildDate')
        if last_build_date:
            last_build_date.string = formatdate(localtime=True)
    else:
        # Create new RSS structure
        soup = BeautifulSoup('', 'xml')
        
        # Add RSS root element
        rss = soup.new_tag('rss', version="2.0")
        soup.append(rss)
        
        # Add channel element
        channel = soup.new_tag('channel')
        rss.append(channel)
        
        # Add channel metadata
        title = soup.new_tag('title')
        title.string = f"{school_name}招聘信息"
        channel.append(title)
        
        link = soup.new_tag('link')
        link.string = "https://example.com/jobs"
        channel.append(link)
        
        description = soup.new_tag('description')
        description.string = f"{school_name}招聘信息RSS订阅"
        channel.append(description)
        
        language = soup.new_tag('language')
        language.string = 'zh-cn'
        channel.append(language)
        
        pub_date = soup.new_tag('pubDate')
        pub_date.string = formatdate(localtime=True)
        channel.append(pub_date)
        
        last_build_date = soup.new_tag('lastBuildDate')
        last_build_date.string = formatdate(localtime=True)
        channel.append(last_build_date)

    # Add new jobs as items
    for job in jobs:
        item = soup.new_tag('item')
        
        # Add title
        title = soup.new_tag('title')
        title.string = job['title']
        item.append(title)
        
        # Add link
        link = soup.new_tag('link')
        link.string = job['url']
        item.append(link)
        
        # Add description
        description = soup.new_tag('description')
        description.string = job.get('description', job['title'])
        item.append(description)
        
        # Add pubDate
        pub_date = soup.new_tag('pubDate')
        # Convert job's publish_date to RFC 2822 format
        try:
            date_obj = datetime.strptime(job['publish_date'], '%Y-%m-%d')
            pub_date.string = formatdate(float(date_obj.timestamp()), localtime=True)
        except:
            pub_date.string = formatdate(localtime=True)
        item.append(pub_date)
        
        # Add guid
        guid = soup.new_tag('guid')
        guid.string = job['url']
        item.append(guid)
        
        # Add category
        category = soup.new_tag('category')
        category.string = job.get('type', '招聘信息')
        item.append(category)
        
        channel.append(item)

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))