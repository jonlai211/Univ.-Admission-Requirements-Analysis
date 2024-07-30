import json
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-0a1a4b69aaaa4ff0947dd8bb52e08010")

url1 = 'https://college.harvard.edu/admissions/apply/application-requirements'
url2 = 'https://college.harvard.edu/admissions'
url3 = 'https://college.harvard.edu/admissions/apply'
url4 = 'https://college.harvard.edu/admissions/apply/international-applicants'
url5 = 'https://college.harvard.edu/admissions/apply/first-year-applicants'
scraped_data = app.scrape_url(url5)

with open(f'harvard_5.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_data, f, ensure_ascii=False, indent=4)
