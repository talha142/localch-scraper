from utils import get_listing_urls, scrape_all_listings, save_to_csv

if __name__ == "__main__":
    keyword = input("Enter search keyword (e.g. 'restaurants in Zurich'): ").strip()
    urls = get_listing_urls(keyword)
    print(f"🟢 Collected {len(urls)} listing URLs.")

    results = scrape_all_listings(urls)
    print(f"🟢 Scraped details for {len(results)} listings.")

    save_to_csv(results, keyword)
