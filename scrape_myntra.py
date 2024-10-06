"""
Example Command : python scrape_myntra.py --start_page=1 --end_page=5000 --sleep_time=0.2 --category=womens-western-wear

NOTE
1. Currently the script is run for each category parallely in a different terminal. 
2. Also the category count and hence the number of pages to scrape has to be added manually.
TODO: remove this in future since we can get total count by requesting the first page of the category.
3. For categories with many products like womens-western-wear, we scrape it in chunks of 5000 pages, parallely from different terminals.
TODO: Use the same script to scrape whole myntra. Spin off multiple subprocess for the purpose of scraping. 
TODO: Look into aria2c to scrape webpages as well. 


Scraping Images:
aria2c \
--continue=true \
--max-connection-per-server=16 \ 
--split=1 \
--max-concurrent-downloads=500 \
--max-overall-download-limit=0 \
--max-download-limit=0 \
--input-file=image_urls.txt \
--dir=images2 \
--console-log-level=warn \
--summary-interval=0

Command for downloading files. 
500 connections support 1500 files/s. 20 connections support 200.
Scraping with concurrency=500 finishes in <= 30mins. 
TODO : Integrate scraping images using aria2c into the same binary. 
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import os
import argparse
from tqdm import tqdm


category_info = {
    "womens-western-wear": {'type': 'women', 'count': 578132},
    "fusion-wear": {'type': 'women', 'count': 545062},
    "women-plus-store": {'type': 'women', 'count': 126473},
    "women-sportswear-clothing": {'type': 'women', 'count': 34907},
    "men-topwear": {'type': 'men', 'count': 405240},
    "men-ethnic-wear": {'type': 'men', 'count': 71085},
    "men-bottomwear": {'type': 'men', 'count': 99391},
    # "men-plus-size": {'type': 'men', 'count': 5880},
}



class MyntraScraper:
    def __init__(self, start_page=1, end_page=6338, category=None, sleep_time=0.4):
        print(f'StartPage : {start_page} \nEndPage : {end_page} \nCategory : {category} \nSleep Time : {sleep_time}')

        self.start_page, self.end_page, self.sleep_time = start_page, end_page, sleep_time
        self.headers={"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
        self.scrape_url = f'https://www.myntra.com/{category}'
        self.root_dir = f'scraped-myntra/{category}'
        
        ## Initiate root dir.
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir, exist_ok=True)
        
    def parseData(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')

        for script in scripts:
            # print(script)
            if 'window.__myx = ' in script.text:
                json_str = script.text.split('window.__myx = ')[1]
                return json.loads(json_str)
            
    def saveData(self, page, scraped_json):
        with open(f'{self.root_dir}/{page}.json', 'w') as f:
            json.dump(scraped_json, f)
            
    def scrape_page(self, page):
        url = f'{self.scrape_url}?p={page}'
        return requests.get(f'{self.scrape_url}?p={page}', headers=self.headers)
        
    def scrape_all(self):
        for page in tqdm(range(self.start_page, self.end_page + 1)):
            if os.path.exists(f'{self.root_dir}/{page}.json'):
                continue
            # print("Scraping: ", page)
            resp = self.scrape_page(page)
            scraped_json = self.parseData(resp)
            # print(scraped_json)
            self.saveData(page, scraped_json)
            # print("Saved:    ", page)
            time.sleep(self.sleep_time)
            
class MyntraProcessor:            
    def get_scraped_products(self):
        SELECTED_PRODUCT_KEYS = ['landingPageUrl', 'productId', 'product', 'productName', 'rating', 'ratingCount',
        'isFastFashion', 'brand', 'searchImage', 'sizes', 'gender', 'primaryColour', 'additionalInfo', 'category',
        'price', 'articleType', 'subCategory', 'masterCategory']

        all_products = []
        for file in os.listdir('scraped'):
            try:
                data = json.loads(open(f'scraped/{file}').read())
                products = data['searchData']['results']['products']
                filtered_product = [{key: product[key] for key in SELECTED_PRODUCT_KEYS} for product in products]
                all_products.extend(filtered_product)
            except Exception as e:
                print(f'Failed {file} : {e}')
        return all_products

    def write_to_csv(self, filename):
        scraped_products = get_scraped_products()
        pd.DataFrame(scraped_products).to_csv(filename)
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Arguments for Myntra Scraper.")
    parser.add_argument('--start_page', type=int, required=False, default=1, help="Start Page")
    parser.add_argument('--end_page', type=int, required=False, help="End Page")
    parser.add_argument('--category', type=str, required=True, help="Category")
    parser.add_argument('--sleep_time', type=float, required=False, default=0.4, help="sleep time")
    
    args = parser.parse_args()
    
    assert args.category in category_info, f'Category : {category} not valid.'
    
    end_page = args.end_page or (category_info[args.category]['count'] // 50 + 1)
        
    myntra_scraper = MyntraScraper(start_page=args.start_page, end_page=end_page, category=args.category, sleep_time=args.sleep_time)
    myntra_scraper.scrape_all()

    