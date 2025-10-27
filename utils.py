import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
import time
import random
from requests.exceptions import RequestException
from config import BASE_URL, HEADERS, MAX_LISTINGS, THREADS, RETRIES

# Safe GET with retries
def safe_get(session, url, timeout=15, retries=RETRIES):
    delay = 1
    for attempt in range(retries):
        try:
            resp = session.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except RequestException as e:
            print(f"⚠️ Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(delay + random.uniform(0, 1.5))
            delay *= 2
    print(f"❌ Failed to fetch {url} after {retries} attempts")
    return None

# Collect listing URLs
def get_listing_urls(keyword, max_listings=MAX_LISTINGS):
    urls = set()
    page_num = 1
    encoded_keyword = urllib.parse.quote_plus(keyword)
    with requests.Session() as session:
        while len(urls) < max_listings:
            search_url = f"{BASE_URL}{encoded_keyword}?page={page_num}"
            resp = safe_get(session, search_url)
            if not resp: break
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href*='/en/d/']")
            for link in links:
                href = link.get("href")
                full_url = urllib.parse.urljoin("https://www.local.ch", href)
                urls.add(full_url)
                if len(urls) >= max_listings: break
            page_num += 1
            time.sleep(random.uniform(0.8, 1.5))
    return list(urls)[:max_listings]

# Scrape individual listing
def scrape_listing(session, url):
    resp = safe_get(session, url)
    if not resp: return None
    soup = BeautifulSoup(resp.text, "html.parser")
    name = soup.find("h1").get_text(strip=True) if soup.find("h1") else "N/A"
    address = (soup.find("address") or soup.select_one("[data-testid='address']"))
    address = address.get_text(strip=True) if address else "N/A"
    phone = soup.select_one("a[href^='tel:']")
    phone = phone.get_text(strip=True) if phone else "N/A"
    email = soup.select_one("a[href^='mailto:']")
    email = email.get_text(strip=True) if email else "N/A"
    return {"Name": name, "Address": address, "Phone": phone, "Email": email, "URL": url}

# Parallel scraping
def scrape_all_listings(urls):
    results = []
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            future_to_url = {executor.submit(scrape_listing, session, url): url for url in urls}
            for future in as_completed(future_to_url):
                res = future.result()
                if res: results.append(res)
    return results

# Save to CSV
def save_to_csv(data, keyword):
    import csv, os
    os.makedirs("output", exist_ok=True)
    file_name = f"output/{keyword.replace(' ', '_')}_localch_results.csv"
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Name","Address","Phone","Email","URL"])
        writer.writeheader()
        writer.writerows(data)
    print(f"📁 Saved {len(data)} listings to {file_name}")
