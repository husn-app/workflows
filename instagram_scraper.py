import os
import requests
import argparse
import json
from tqdm import tqdm
import time
import urllib
from proxy_parser import get_spys_proxies
import random
from math import ceil 
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import brotli
from bs4 import BeautifulSoup
import re

def generate_random_ip():
    """Generates a random IPv4 address."""
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

def reboot_wifi():
    os.system("networksetup -setairportpower en0 off")
    time.sleep(6)
    os.system("networksetup -setairportpower en0 on")
    time.sleep(10)
    
ROOT_DIR = os.getcwd() + '/'
SCRAPED_DIR  = ROOT_DIR + 'scraped/instagram'
# SITE_URL = "https://www.instagram.com/"
HEADERS = { 
    # this is internal ID of an instagram backend app. It doesn't change often.
    "x-ig-app-id": "936619743392459",
    # use browser-like features
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "*/*",
    'Referer': 'https://www.instagram.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
    # "X-Forwarded-For": generate_random_ip(),
    # "X-Real-IP": generate_random_ip(),
    # "Client-IP": generate_random_ip()
}
SLEEP_TIME = 3
PROXY_FAIL_LIMIT = 5
WIFI_REBOOT_FREQ = 35
NO_OF_PROXIES_TRIED = 1

class InstagramScraper:
    def setup_dirs(self):
        if not os.path.exists(ROOT_DIR + 'scraped'):
            os.mkdir(ROOT_DIR + 'scraped')
        if not os.path.exists(SCRAPED_DIR):
            os.mkdir(SCRAPED_DIR)
        
        if not os.path.exists(SCRAPED_DIR + '/related_usernames'):
            os.mkdir(SCRAPED_DIR + '/related_usernames')
        
    def __init__(self, usernames, proxy, max_usernames_to_scrape=50):
        self.setup_dirs()
        self.scraped_usernames = set(os.listdir(SCRAPED_DIR))
        self.max_usernames_to_scrape = max_usernames_to_scrape
        self.usernames = usernames
        self.proxy = {
            "http": proxy,
        }
    
    def get_user_id_from_response(self, response):
        # try:
        #     if response.headers.get('Content-Encoding') == 'gzip':
        #         decoded_content = gzip.decompress(response.content).decode('utf-8')
        #     elif response.headers.get('Content-Encoding') == 'br':
        #         decoded_content = brotli.decompress(response.content).decode('utf-8')
        # except Exception:
        decoded_content = response.text
        soup = BeautifulSoup(decoded_content, 'html.parser')
        for script in soup.find_all('script'):
            if script.string and 'CurrentUserInitialData' in script.string:  # Target the correct script
                try:
                    match = re.search(r'"user_id":\s*"(.*?)"', script.string)
                    if match:
                        return match.group(1)
                except Exception as e:
                    print(f"Exception occured while fetching user_id from response: {e}")
        print(f"ERROR: No user_id string found in {response.url=}")
        return None

    def scrape_profile(self, username):
        try:
            resp = requests.get(
                f'https://www.instagram.com/{username}', headers=HEADERS, proxies=self.proxy)
            resp.raise_for_status()
            # print(f"{resp.status_code=}\n{resp.url=}\n{resp.headers.get('Content-Type')=}\n{resp.headers.get('Content-Encoding')=}")
            user_id = self.get_user_id_from_response(resp)
            if not user_id:
                print(f"ERROR fetching user_id for {username=} with {self.proxy['http']}")
                return False

            variables = {
                "id":user_id,
                "first":12
            }
            url = f'https://www.instagram.com/graphql/query/?doc_id=7950326061742207&variables={urllib.parse.quote(json.dumps(variables))}'
            time.sleep(random.uniform(2, 5))
            resp = requests.get(url, headers=HEADERS, proxies=self.proxy)
            # resp = requests.get(
            #     f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}', headers=HEADERS, proxies=self.proxy)
            if resp.status_code == 401:
                print(f'Error fetching {username} with {self.proxy["http"]}: {resp.status_code=}, {resp.reason=}, {resp.url=}\n{resp.request.headers=}\n{resp.request.path_url=}')
                print("Sleeping for 180s...\n")
                time.sleep(180)
                return False
                # reboot_wifi()
            if resp.status_code != 200:
                print(f'Error fetching {username} with {self.proxy["http"]}: {resp.status_code=}, {resp.reason=}, {resp.url=}\n{resp.request.headers=}\n{resp.request.path_url=}\n')
                return False
            
            profile_data = resp.json()
            if not 'display_url' in json.dumps(profile_data):
                print(f"'display_url' not found in the response for {username}")
                # reboot_wifi()
                return False
            
            with open(ROOT_DIR + f'scraped/instagram/{username}.json', 'w') as f:
                json.dump(profile_data, f)
            return True
        except Exception as e:
            print(f'Exception occurred while fetching {username}: {e}')
        return False
    
    def scrape_profile_with_insta_api(self, username = ""):
        username = self.usernames[0]
        file_path = ROOT_DIR + f'scraped/instagram/{username}.json'
        user_exists = True
        try:
            resp = requests.get(
                f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}', headers=HEADERS, proxies=self.proxy)
            resp.raise_for_status()
            profile_data = resp.json()
            if not 'display_url' in json.dumps(profile_data):
                print(f"'display_url' not found in the response for {username}. Restricted profile")
                return False, user_exists
            
            with open(file_path, 'w') as f:
                json.dump(profile_data, f)
            return True, user_exists
        except Exception as e:
            print(f'Exception occurred in insta_api while fetching {username}: {e}')
            if resp.status_code == 404:
                user_exists = False
        return False, user_exists
    
    def scrape_all_profiles(self):
        success_count, fail_count = 0, 0
        for username in self.usernames:
            if username not in self.scraped_usernames:
                if self.scrape_profile(username):
                    success_count += 1
                else:
                    fail_count += 1
                time.sleep(random.uniform(1.5, 3.8))
        return success_count, fail_count

def main():
    parser = argparse.ArgumentParser(description='Instagram Scraper')
    parser.add_argument('-f', '--usernames_file', type=str, help='Path to the text file containing usernames to scrape')
    parser.add_argument('-u', '--username', type=str, help='A single username to scrape')
    parser.add_argument('-t', '--threads', type=int, default=1000, help='Number of threads for downloading')
    args = parser.parse_args()

    usernames = []
    if args.usernames_file:
        with open(args.usernames_file, 'r') as file:
            usernames = [line.strip() for line in file.readlines()]
    if args.username:
        usernames.append(args.username)
    
    non_existing_usernames = []
    with open("non_existing_users.txt", "r") as file:
        non_existing_usernames = [line.strip() for line in file.readlines()]
    
    already_scraped_users = [filename[:-5] for filename in os.listdir(SCRAPED_DIR) if filename.endswith('.json')]
    usernames = list(set(usernames) - set(non_existing_usernames) - set(already_scraped_users))
    # usernames = [username for username in sorted(usernames) if f"{username}.json" not in os.listdir(SCRAPED_DIR)]
    # usernames = usernames[-2000:]

    proxy_list, _ = get_spys_proxies()
    random.shuffle(proxy_list)
    proxy_fail_count = [{proxy: 0} for proxy in proxy_list]
    usernames_per_proxy = ceil(len(usernames) / len(proxy_list))
    print(f"Scraping {len(usernames)} profiles using {len(proxy_list)} proxies with {usernames_per_proxy=}")
    
    # proxy_id = 0
    # cnt = 0
    # for user in usernames:
    #     proxies_attempted = 0
    #     while proxy_fail_count and proxies_attempted < NO_OF_PROXIES_TRIED:
    #         current_proxy = list(proxy_fail_count[proxy_id].keys())[0]
    #         scraper = InstagramScraper([user], current_proxy)
    #         _, fail_cnt = scraper.scrape_all_profiles()
    #         if fail_cnt:
    #             proxy_fail_count[proxy_id][current_proxy] += 1
    #             if proxy_fail_count[proxy_id][current_proxy] >= PROXY_FAIL_LIMIT:
    #                 del proxy_fail_count[proxy_id]
    #             else:
    #                 proxy_id = (proxy_id + 1) % len(proxy_fail_count)
    #         else:
    #             print(f"Successfully scraped {user}")
    #             proxy_id = (proxy_id + 1) % len(proxy_fail_count)
    #             break
    #         proxies_attempted += 1
    #     if not proxy_fail_count:
    #         print(f"ERROR fetching {user}. No user proxy left to retry")
    #         break
    #     if proxies_attempted == NO_OF_PROXIES_TRIED:
    #         print(f"Tried {NO_OF_PROXIES_TRIED} proxies. Skipping {user}.")
        
    #     cnt += 1
        # if cnt % WIFI_REBOOT_FREQ == 0:
        #     reboot_wifi()
    
    proxy_id = 0
    scrapers = []
    usernames_per_proxy = 1
    for i in range(0, len(usernames), usernames_per_proxy):
        scrapers.append(InstagramScraper(usernames[i : i + usernames_per_proxy], proxy_list[proxy_id]))
        proxy_id = (proxy_id + 1) % len(proxy_list)
    
    non_existing_users = []
    with ThreadPoolExecutor(max_workers=args.threads) as executor:  # Adjust max_workers as needed
        futures = {executor.submit(scraper.scrape_profile_with_insta_api): scraper for scraper in scrapers}
        for future in as_completed(futures):
            scraper = futures[future]
            try:
                success, user_exists = future.result(timeout=5)
                if not user_exists:
                    non_existing_users.append(scraper.usernames[0])
                print(f"{success=} for user:{scraper.usernames[0]} proxy: {scraper.proxy}")

            except Exception as e:
                print(f"Error during scraping with {scraper.proxy['http']}: {e}")

    with open("non_existing_users.txt", 'a') as f:
        f.writelines(user + '\n' for user in non_existing_users)
if __name__ == '__main__':
    main()
