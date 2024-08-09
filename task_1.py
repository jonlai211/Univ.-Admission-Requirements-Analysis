import asyncio
import logging
from pathlib import Path
from utils import chat, load_links, check_official, crawl_webpage, clean_html, check_consistent, gen_query, \
    search, save_json, save_csv


# Configure logging
log_directory = Path(__file__).resolve().parent / 'logs'
log_directory.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
logging.basicConfig(level=logging.DEBUG,  # Change to DEBUG to see all messages
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_directory / 'task_1.log'),
                        logging.StreamHandler()
                    ])

logging.info("Logging system initialized")

univ = "mit"
question = "stats"


async def main():
    query, univ_name, question_name = gen_query(univ, question)
    results = await search(query)
    filename = f"{univ}_{question}"
    save_json(results, filename)

    search_links = load_links(filename)
    logging.info(f"Num: {len(search_links)}; Search links: {search_links}")
    official_links = await check_official(univ_name, search_links)

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
    asyncio.run(main(), debug=True)
