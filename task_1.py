import asyncio
from utils import chat, load_links, check_official, crawl_webpage, clean_html, check_consistent, gen_query, \
    fetch_search, save_json

univ = "mit"
question = "select"


async def main():
    query, univ_name, question_name = gen_query(univ, question)
    results = await fetch_search(query, max_results=10)
    filename = f"{univ}_{question}"
    save_json(results, filename)

    search_links = load_links(filename)
    official_links = await check_official(univ_name, search_links)

    valid_links = []

    for link in official_links:
        html_content = await crawl_webpage(link)
        if not html_content.startswith("Failed"):  # Ensure the page was retrieved successfully
            cleaned_text = clean_html(html_content)
            consistent, explanation = await check_consistent(cleaned_text, query)
            if consistent == "Yes":
                valid_links.append(link)
                print(f"Link: {link} is both official and consistent.")
            else:
                print(f"Link: {link} is official but not consistent. Reason: {explanation}")
        else:
            print(f"Failed to retrieve content from {link}")

    if valid_links:
        print(f"Num: {len(valid_links)}; Valid links: {valid_links}")
    else:
        print("No valid links found that meet both criteria.")


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
