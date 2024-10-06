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
        ## TODO : use consistent session?
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

"""
TODO: Add myntra processing to main. 
"""
class MyntraProcessor:
    def minimize_product(product):
        return {
            'original_website' : 'Myntra',
            'product_url' : 'https://myntra.com/' + product['landingPageUrl'],
            'product_id' : product['productId'],
            'product_name' : product['productName'],
            'rating' : product['rating'],
            'rating_count' : product['ratingCount'],
            'brand' : product['brand'],
            'primary_image' : product['searchImage'],
            'sizes' : product['sizes'],
            'gender' : product['gender'],
            'images' : [x['src'] for x in product['images'] if x['src']],
            'price' : product['price']
        }
        
    def get_all_products(self):
        all_data = []        
        for category in category_info.keys():
            print('Category : ', category)
            for file_ in tqdm(os.listdir(f'scraped-myntra/{category}')):
                file_path = f'scraped-myntra/{category}/{file_}'
                results = json.load(open(f'scraped-myntra/{category}/{file_}'))['searchData']['results']['products']
                all_data.extend([x for x in results])
        return all_data
        
    def deduplicate_products(self, all_data):
        added_product_ids = set()
        unique_data = []
        for data in tqdm(all_data):
            if data['productId'] in added_product_ids:
                continue
            added_product_ids.add(data['productId'])
            unique_data.append(data)
        return unique_data
    
    def processs(self):
        print('Processing & deduplicating products...')
        all_products = self.deduplicate_products(self.get_all_products())
        
        print('Writing full dump...')
        json.dump(all_products, open('scraped-myntra/all_products_full_dump.json', 'w'))
        
        print('Writing minimized dump...')
        minimized_products = [self.minimize_product(x) for x in all_products]
        json.dump(minimized_products, open('scraped-myntra/all_products_minimized_dump.json', 'w'))
        
        print('Writing image urls...')
        image_urls = [x['primary_image'] for x in minimized_products if x]
        open('scraped-myntra/image-urls.txt', 'w').write('\n'.join(image_urls))
        
        print(f"Wrote the following files to disk:")
        for filename in ['scraped-myntra/all_products_full_dump.json', 'scraped-myntra/all_products_minimized_dump.json', 'scraped-myntra/image-urls.txt']:
            print(f"{filename} : {os.path.getsize(filename) / 1e9:.2f} GB")

"""
TODO : Currently ordered_image_paths.json is written in encode_images.json. This is done post downloading the images,
so all images that were not download are not in the list. 

Create a binary to generate products df from json and order it and move the following function to that binary.
"""
def order_products_df():
    # read products_df and image_paths order. 
    products_df = pd.read_csv('myntra_scraped_data_20241005.csv')
    image_paths = json.load(open('ordered_image_paths.json'))
    image_paths_to_ix = {path : i for i, path in enumerate(image_paths)}

    # 1. ignore nan rows 2. drop duplicates 3. remove images not in image_path
    products_df = products_df[products_df['primary_image'].apply(lambda x: isinstance(x, str))]
    products_df = products_df.drop_duplicates(subset='image_path', keep='first')
    products_df = products_df[products_df['image_path'].isin(image_paths_to_ix)]
    
    ## Set ordered index. 
    ordered_index = pd.Index([image_paths_to_ix[path] for path in products_df['image_path']])

    products_df = products_df.set_index(ordered_index).sort_index()
    products_df = products_df.reset_index(drop=True)

    # delete image_path
    del products_df['image_path']
    if 'Unnamed: 0' in products_df.columns:
        del products_df['Unnamed: 0']
    products_df['index'] = products_df.index
    return products_df
        
        
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

# open('image_urls.txt', 'w').write('\n'.join(list(image_urls)))
    