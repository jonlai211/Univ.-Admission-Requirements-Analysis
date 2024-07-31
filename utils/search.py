import json
import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_KEY")
GOOGLE_ENGINE_ID = os.getenv("GOOGLE_ENGINE_ID")
PROXY_SETTINGS = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

university_map = {
    "mit": "Massachusetts Institute of Technology",
    "caltech": "California Institute of Technology",
    "upenn": "University of Pennsylvania",
    "nyu": "New York University",
    "umich": "University of Michigan-Ann Arbor",
    "uiuc": "University of Illinois at Urbana-Champaign",
    "bu": "Boston University",
    "usc": "University of Southern California"
}

question_map = {
    1: "undergraduate admission requirements selection criteria selection process",
    2: "required application materials for undergraduate admission",
    3: "undergraduate application timeline deadlines",
    4: "latest admitted undergraduate student statistics OR class profile"
}

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_query_text(university_abbr, question_id):
    university = university_map[university_abbr]
    question = question_map[question_id]
    return f"{university} {question}"


def fetch_google_search_results(query, api_key, search_engine_id, proxies, max_results=100):
    accumulated_results = []
    google_search_api_url = 'https://www.googleapis.com/customsearch/v1'
    total_results_fetched = 0

    try:
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

            response = requests.get(google_search_api_url, params=search_params, proxies=proxies, timeout=30)
            if response.status_code == 200:
                search_data = response.json()
                for item in search_data.get('items', []):
                    filtered_result = {
                        'title': item.get('title'),
                        'link': item.get('link'),
                        'snippet': item.get('snippet')
                    }
                    accumulated_results.append(filtered_result)

                if total_results_fetched >= max_results or 'nextPage' not in search_data.get('queries', {}):
                    break
            else:
                logging.error(f"Failed to fetch results: {response.status_code} {response.text}")
                break

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")

    return accumulated_results


def save_results_to_json(search_results, filename_query):
    directory = 'output/search'
    filename = f'{directory}/{filename_query.replace(" ", "_")}.json'

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(search_results, file, ensure_ascii=False, indent=4)
        logging.info(f"Results successfully saved to {filename}")
    except Exception as e:
        logging.error(f"Failed to save results: {e}")


if __name__ == '__main__':
    university_abbr = "mit"
    question_id = 4
    query_text = generate_query_text(university_abbr, question_id)
    print(query_text)
    results = fetch_google_search_results(query_text, GOOGLE_KEY, GOOGLE_ENGINE_ID, PROXY_SETTINGS, 10)
    print(results)
    save_results_to_json(results, f"{university_abbr}_{question_id}")
