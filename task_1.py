import argparse
import asyncio
import logging
from pathlib import Path
from utils import chat, load_links, check_official, crawl_webpage, clean_html, check_consistent, gen_query, \
    search, save_json, save_csv

log_directory = Path(__file__).resolve().parent / 'logs'
log_directory.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_directory / 'task_1.log'),
                        logging.StreamHandler()
                    ])
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.info("Logging system initialized")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process university and question information.')
    parser.add_argument('--univ', default='mit')
    parser.add_argument('--question', default='select')

    args = parser.parse_args()
    return args.univ, args.question


async def main(univ, question):
    query, univ_name, question_name = gen_query(univ, question)
    results = await search(query)
    filename = f"{univ}_{question}"
    save_json(results, filename)

    search_links = load_links(filename)
    logging.info(f"Num: {len(search_links)}; Search links: {search_links}")
    official_links = await check_official(univ_name, search_links)
    logging.info(f"Num: {len(official_links)}; Official links: {official_links}")

    valid_links = []

    for link in official_links:
        html_content = await crawl_webpage(link)
        if not html_content.startswith("Failed"):
            cleaned_text = clean_html(html_content)
            consistent, explanation = await check_consistent(cleaned_text, univ_name, question_name)
            if consistent == "Yes":
                valid_links.append(link)
                logging.info(f"Consistent: {consistent}; Link: {link}; Reason: {explanation}")
            else:
                logging.info(f"Consistent: {consistent}; Link: {link}; Reason: {explanation}")
        else:
            logging.warning(f"Failed to retrieve content from {link}")

    if valid_links:
        logging.info(f"Num: {len(valid_links)}; Valid links: {valid_links}")
        save_csv(univ, question, valid_links)
    else:
        logging.info("No valid links found that meet both criteria.")


if __name__ == '__main__':
    univ, question = parse_arguments()
    asyncio.run(main(univ, question), debug=True)
