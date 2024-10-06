"""
TODO: Add imports & make it into a proper runnable file. 
"""

class InstagramScraper:
    def setup_dirs(self):
        if not os.path.exists(ROOT_DIR + 'scraped'):
            os.mkdir(ROOT_DIR + 'scraped')
        if not os.path.exists(ROOT_DIR + 'scraped/instagram'):
            os.mkdir(ROOT_DIR + 'scraped/instagram')
        
        if not os.path.exists(ROOT_DIR + 'related_usernames'):
            os.mkdir(ROOT_DIR + 'scraped/instagram/related_usernames')
        
    def __init__(self, usernames_to_scrape, max_usernames_to_scrape=1000):      
        self.scraped_usernames = set(os.listdir(ROOT_DIR + 'scraped/instagram'))
        self.usernames_to_scrape = []
        self.max_usernames_to_scrape = max_usernames_to_scrape
        
        self.headers ={
            # this is internal ID of an instegram backend app. It doesn't change often.
            "x-ig-app-id": "936619743392459",
            # use browser-like features
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
        }
        
        self.profile_url = 'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'

        
    ## Scrapes profile and saves it. 
    ## Returns usernames of related public profiles. 
    def scrape_profile(self, username):
        try:
            resp = requests.get(url.format(username=username), headers=self.headers, timeout=5)
            assert resp.status_code == 200, f'Failed to fetch {username} : {response.content}'
        except Exception as e:
            print(e)
            return []
        related_usernames = [x['node']['username'] for x in resp.json()['data']['user']['edge_related_profiles']['edges'] if not x['node']['is_private']]
        