import asyncio
import csv
import logging

import httpx
import json
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

try:
    from .chat import chat
except ImportError:
    from chat import chat

load_dotenv()

FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
FIRECRAWL_APP = FirecrawlApp(api_key="fc-0a1a4b69aaaa4ff0947dd8bb52e08010")


def load_links(filename):
    project_root = Path(__file__).parent.parent
    file_path = project_root / 'output' / 'search' / f'{filename}.json'
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            links = [item['link'] for item in data if 'link' in item]
            return links
    except FileNotFoundError:
        # print(f"{file_path} was not found.")
        return []
    except json.JSONDecodeError:
        # print("Error decoding JSON.")
        return []


async def check_official(univ_name, search_links):
    prompt_check_official = f"""
    以下是一系列链接，请检查并返回所有属于{univ_name}的官方网站链接。{search_links}
    输出格式应为XML，每个链接作为一个单独的 <link> 元素，不要输出```xml等信息。如下所示：
    <links>
        <link>official link1</link>
        <link>official link2</link>
    </links>
    """
    response = await chat(prompt_check_official, ' ')
    official_links = parse_links(response)
    # print(f'Num: {len(official_links)}; Official links: {official_links}')

    return official_links


def parse_links(xml_data):
    try:
        root = ET.fromstring(xml_data)
        links = [link.text for link in root.findall('.//link')]
        return links
    except ET.ParseError as e:
        # print(f"Error parsing XML: {e}\n XML data: {xml_data}")
        return []


async def check_consistent(text_content, univ_name, question_name):
    prompt_check_consistent = f"""
    请阅读以下网页内容，并进行以下判断：
    1. 确认内容是否属于{univ_name}。
    2. 检查内容是否是为first-year applicant或者undergraduate相关的内容。
    3. 评估内容是否包含{question_name}。
    4. 确认网页的主体内容里没有标记该信息为已过时或存档（比如'archived'或'outdated'）。
    
    基于以上标准，如果内容满足上述所有的要求，则返回'是'；如果不符合其中任意一个要求，则返回'否'。同时提供简短的解释说明做出判断的理由。不要输出任何符号。
    网页内容如下：
    {text_content}
    """
    response = await chat(prompt_check_consistent, ' ')
    # print(response)
    result, explanation = parse_result(response)
    # print(f"Consistent: {result}. Explanation: {explanation}")

    return result, explanation


def parse_result(response):
    try:
        match = re.match(r"(是|否)\s*(.+)", response.strip(), re.DOTALL)
        if not match:
            # If no match, raise an exception
            raise ValueError(f"Parsing failed, response: {response}.")

        decision = "Yes" if match.group(1) == "是" else "No"
        explanation = match.group(2).strip().replace('\n', ' ')
        return decision, explanation

    except Exception as e:
        # print(f"Error occurred: {e}")
        return "No", "Parsing failed, the response format is incorrect."


def is_garbled(text):
    non_ascii = sum(1 for c in text if ord(c) > 127)
    total = len(text)
    if total == 0:
        return False
    return (non_ascii / total) > 0.2


async def crawl_webpage(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://www.google.com/',
        'Origin': 'https://www.google.com',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        timeout = httpx.Timeout(10.0, read=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()  # This will raise an HTTPStatusError for bad responses
            soup = BeautifulSoup(response.text, 'html.parser')
            prettified_html = soup.prettify()
            if is_garbled(prettified_html):
                raise ValueError("Detected garbled content, falling back to Firecrawl.")
            return prettified_html
    except (httpx.HTTPStatusError, httpx.ReadTimeout, httpx.RequestError, ValueError) as e:
        logging.info(f"Error or garbled content, using Firecrawl fallback: {e}")
        return await asyncio.to_thread(firecrawl, url)


def firecrawl(url):
    try:
        data = FIRECRAWL_APP.scrape_url(url=url)
        if data and 'content' in data:
            soup = BeautifulSoup(data['content'], 'html.parser')
            return soup.prettify()
        else:
            return "Firecrawl did not return usable content."
    except Exception as fe:
        return f"Firecrawl also failed: {fe}"


def save_html(html_content, filename):
    project_root = Path(__file__).parent.parent
    file_path = project_root / 'output' / 'scrape' / f'{filename}.html'
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(html_content)
        return "HTML content saved successfully."
    except IOError as e:
        return f"An error occurred while saving HTML: {e}"


def load_html(filename):
    project_root = Path(__file__).parent.parent
    file_path = project_root / 'output' / 'scrape' / f'{filename}.html'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return html_content
    except IOError as e:
        return f"Failed to load HTML content: {e}"


def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # 移除不需要的标签
    for element in soup(["script", "style", "header", "footer", "nav"]):
        element.decompose()
    # 获取纯文本内容
    text = soup.get_text()
    # 清洗和规范化文本
    lines = (line.strip() for line in text.splitlines())  # 分割文本到行，并去除首尾空白
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))  # 进一步分割每一行
    text = '\n'.join(chunk for chunk in chunks if chunk)  # 重新组合文本，去除空行
    # 使用正则表达式进一步清洗文本
    text = re.sub(r'&[a-z]+;', ' ', text)  # 替换HTML实体
    # print(f"HTML clean content: {text}")
    return text


def save_csv(univ, question, valid_links):
    project_root = Path(__file__).parent.parent
    file_path = project_root / 'output' / 'task_1.csv'
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        link_writer = csv.writer(csvfile)
        for index, link in enumerate(valid_links):
            link_writer.writerow([index, univ, question, link])


async def main():
    identifier = 3

    if identifier == 1:
        univ_name = "Massachusetts Institute of Technology"
        search_links = load_links("mit_select")
        official_links = await check_official(univ_name, search_links)
    elif identifier == 2:
        links = load_links("mit_1")
        print(links)
    elif identifier == 3:
        html_content = await crawl_webpage("https://finaid.umich.edu/types-aid/scholarships/undergraduate")
        save_html(html_content, 'umich_1')
        print(html_content)
    elif identifier == 4:
        text_content = """
        Undergraduate Admissions – MIT Facts
×
Admissions & Aid
Undergraduate Admissions
Undergraduate Admissions Overview
Undergraduate Tuition & Aid
Graduate Admissions
Graduate Admissions Overview
Graduate Tuition & Aid
People
Enrollment Statistics
Undergraduate Students
Graduate Students
Employees
Employees Overview
Faculty & Instructional Staff
Postdoctoral Scholars
Alumni
Alumni Overview
MIT Alumni Association
Awards & Honors
Education
Schools & College
Degrees & Majors
Academic & Campus Resources
Academic & Campus Resources Overview
MIT Libraries
Information Technology and Computing on Campus
Makerspaces
Open Learning
Life at MIT
MIT Campus
MIT Campus Overview
Sustainability
Arts at MIT
Athletics & Recreation
Fun & Culture
Research & Innovation
Research at MIT
Research Centers, Labs & Programs
Research Centers, Labs & Programs Overview
Centers, Labs & Institutes
Institute Initiatives
Prominent Programs
Key Local Collaborators
Lincoln Laboratory
MIT & Industry
Innovation & Entrepreneurship
Organization
Mission
Origins
Leadership
MIT & the Community
Resource Development
Operating Financials
Accreditation
Home
/
The
selection process
at MIT is student centered: each application is evaluated within its unique context. No school, state, or regional quotas are applied, and we do not consider legacy/alumni relations in our process. Selection is based on outstanding academic achievement as well as a strong match between the applicant and the Institute, including:
Alignment with MIT’s mission
Collaborative and cooperative spirit
Initiative
Risk taking
Hands-on creativity
Intensity, curiosity, and excitement
Balancing hard work with downtime
Majors & minors
58 undergraduate majors
59 undergraduate minors
50 departments and programs offering graduate degrees
1 pirate certificate
1 wellness certificate
Selected Class of 2027 Undergraduate Admissions Statistics
26,914
Applications for first-year admission
1,291
Offers of admission (4.8%)
1,092
First-year students enrolled
66%
Attended public high schools
49
US states represented
10%
International citizens from 59 countries
18%
Among the first-generation in their family to attend college
Forty-nine percent of students who enrolled are men, 48% are women, 4% are another gender identity, and 2% did not disclose their gender identity (students can select more than one).
For more information, visit
mitadmissions.org
.
        """
        univ_name = "Massachusetts Institute of Technology"
        question_name = "undergraduate admission requirements (selection criteria or selection process)"
        consistent, explanation = await check_consistent(text_content, univ_name, question_name)
    elif identifier == 5:
        html_content = load_html('mit_2')
        text = clean_html(html_content)
        univ_name = "Massachusetts Institute of Technology"
        question_name = "undergraduate admission requirements (selection criteria or selection process)"
        consistent, explanation = await check_consistent(text, univ_name, question_name)
    elif identifier == 6:
        html_content = await crawl_webpage("https://finaid.umich.edu/types-aid/scholarships/undergraduate")
        text = clean_html(html_content)
        # univ_name = "Massachusetts Institute of Technology, Major computer science"
        univ_name = "University of Michigan-Ann Arbor"
        question_name = "undergraduate admission requirements (selection criteria or selection process)"
        consistent, explanation = await check_consistent(text, univ_name, question_name)


if __name__ == '__main__':
    asyncio.run(main())
