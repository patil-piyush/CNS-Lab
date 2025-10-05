import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Step 1: Load URLs from a text file
def load_urls(filename="urls.txt"):
    with open(filename, "r") as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls

# Step 2: Worker function to fetch URL and extract title
def fetch_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for bad status codes
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "No title found"
        return {"url": url, "title": title}
    except Exception as e:
        return {"url": url, "error": str(e)}

# Step 3–5: Run worker pool and collect results
def scrape_urls(urls, max_workers=5):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            results.append(future.result())
    return results

# Step 6: Output to console and JSON file
def save_results(results, filename="results.json"):
    # Print results in console
    for result in results:
        if "title" in result:
            print(f"{result['url']} → {result['title']}")
        else:
            print(f"{result['url']} → ERROR: {result['error']}")

    # Save results to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"\nResults saved to {filename}")

# === Main Execution ===
if __name__ == "__main__":
    urls = load_urls("urls.txt")   # Step 1
    results = scrape_urls(urls)    # Step 3–5
    save_results(results)          # Step 6
