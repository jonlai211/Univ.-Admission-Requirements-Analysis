import json
import os
import logging
import httpx
import asyncio
from dotenv import load_dotenv
from pathlib import Path
from src.university_map import MAP_UNIV
from src.question_map import MAP_QUESTION

load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_KEY")
GOOGLE_ENGINE_ID = os.getenv("GOOGLE_ENGINE_ID")
PROXY_SETTINGS = {
    "http://": "http://127.0.0.1:7890",
    "https://": "http://127.0.0.1:7890",
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def gen_query(univ_abbr, question_abbr):
    univ_name = MAP_UNIV[univ_abbr]
    question_name = MAP_QUESTION[question_abbr]
    query = f"{univ_name}:{question_name}"
    return query, univ_name, question_name


async def fetch_search(query, api_key=GOOGLE_KEY, search_engine_id=GOOGLE_ENGINE_ID, proxies=PROXY_SETTINGS, max_results=100):
    accumulated_results = []
    google_search_api_url = 'https://www.googleapis.com/customsearch/v1'
    total_results_fetched = 0

    async with httpx.AsyncClient(proxies=proxies, timeout=30) as client:
        for start_index in range(1, max_results + 1, 10):
            results_left_to_fetch = max_results - total_results_fetched
            num_results_to_fetch = min(results_left_to_fetch, 10)

            search_params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'start': start_index,
                'num': num_results_to_fetch
            }

            response = await client.get(google_search_api_url, params=search_params)
            if response.status_code == 200:
                search_data = response.json()
                for item in search_data.get('items', []):
                    filtered_result = {
                        'title': item.get('title'),
                        'link': item.get('link'),
                        'snippet': item.get('snippet')
                    }
                    accumulated_results.append(filtered_result)

                total_results_fetched += num_results_to_fetch
                if total_results_fetched >= max_results or 'nextPage' not in search_data.get('queries', {}):
                    break
            else:
                logging.error(f"Failed to fetch results: {response.status_code} {response.text}")

    return accumulated_results


def save_json(search_results, filename):
    project_root = Path(__file__).parent.parent
    file_path = project_root / 'output' / 'search' / f'{filename}.json'
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(search_results, file, ensure_ascii=False, indent=4)
        logging.info(f"Results successfully saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save results: {e}")


async def main():
    university_abbr = "mit"
    question_abbr = "select"

    query_text = gen_query(university_abbr, question_abbr)
    results = await fetch_search(query_text, max_results=10)
    filename = f'{university_abbr}_{question_abbr}'
    save_json(results, filename)


if __name__ == '__main__':
    asyncio.run(main())
