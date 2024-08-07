import asyncio
import httpx
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from .chat import chat


def load_links(filename):
    project_root = Path(__file__).parent.parent
    file_path = project_root / 'output' / 'search' / f'{filename}.json'
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            links = [item['link'] for item in data if 'link' in item]
            return links
    except FileNotFoundError:
        print(f"{file_path} was not found.")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON.")
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
    print(f'Num: {len(official_links)}; Official links: {official_links}')

    return official_links


def parse_links(xml_data):
    try:
        root = ET.fromstring(xml_data)
        links = [link.text for link in root.findall('.//link')]
        return links
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}\n XML data: {xml_data}")
        return []


async def check_consistent(text_content, requirement):
    prompt_check_consistent = f"""
    根据以下网站文本内容，判断是否包含以下学校和问题的要求：{requirement}。请简单回答"是"或"否"并简短解释您的判断理由。不要输出任何符号。
    {text_content}
    """
    response = await chat(prompt_check_consistent, ' ')
    result, explanation = parse_result(response)
    print(f"Consistent: {result}. Explanation: {explanation}")

    return result, explanation


def parse_result(response):
    try:
        match = re.match(r"(是|否)\s*(.*)", response.strip())
        if not match:
            # If no match, raise an exception
            raise ValueError(f"Parsing failed, response: {response}.")

        decision = "Yes" if match.group(1) == "是" else "No"
        explanation = match.group(2).strip()
        return decision, explanation

    except Exception as e:
        print(f"Error occurred: {e}")
        return "No", "Parsing failed, the response format is incorrect."


async def crawl_webpage(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        timeout = httpx.Timeout(10.0, read=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup.prettify()
            else:
                return f"Failed to retrieve the webpage, status code: {response.status_code}"
    except httpx.ReadTimeout:
        return "Request timed out while trying to reach the server."
    except httpx.RequestError as e:
        return f"An error occurred while requesting {url}: {str(e)}"


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


async def main():
    identifier = 1

    if identifier == 1:
        univ_name = "Massachusetts Institute of Technology"
        search_links = load_links("mit_4")
        official_links = await check_official(univ_name, search_links)
    elif identifier == 2:
        links = load_links("mit_1")
        print(links)
    elif identifier == 3:
        html_content = await crawl_webpage("https://oge.mit.edu/graduate-admissions/applications/procedures/")
        save_html(html_content, 'mit_2')
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
        requirement = "MIT, undergraduate admission requirements selection criteria selection process"
        consistent, explanation = await check_consistent(text_content, requirement)
    elif identifier == 5:
        html_content = load_html('mit_2')
        text = clean_html(html_content)
        requirement = "MIT, undergraduate admission requirements selection criteria selection process"
        consistent, explanation = await check_consistent(text, requirement)


if __name__ == '__main__':
    asyncio.run(main())
