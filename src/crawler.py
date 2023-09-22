import random, requests, logging, re
from bs4 import BeautifulSoup
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse 
from repository import Repository
from commit import Commit
from datetime import datetime
 
class MultiThreadedCrawler:

    User_Agents = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1", 
        "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"
    ]

    def __init__(self, repository : Repository, num_workers : int = 10):
        self.repo = repository
        self.pool = ThreadPoolExecutor(max_workers = num_workers)
        self.crawl_queue = Queue()
        self.session = requests.Session()

    def scrape_page(self, url):
        self.session.headers.update({'user-agent': random.sample(self.User_Agents, 1)[0]})
        response = self.session.get(url)
        return response
    
    def run_web_crawler(self):
        self.fill_queue()
        while True:
            try:
                target_url = self.crawl_queue.get(timeout=5).URL
                job = self.pool.submit(self.scrape_page, target_url)
                job.add_done_callback(self.post_scrape_callback)

            except Empty:
                return
            
            except Exception as e:
                print(e)
                continue

    def fill_queue(self):
        starting_commit_page_url = self.repo.get_URL() + f'/commits/{self.repo.branch}'
        response = self.scrape_page(starting_commit_page_url)

        if response.status_code != 200:
            # TODO: handle error
            raise NotImplemented()
        
        commit_list_page = BeautifulSoup(response.text, "lxml")
        button = self.get_button(commit_list_page)
        self.parse_links(commit_list_page)

        while button != None:
            next_url = button.attrs['href']
            response = self.scrape_page(next_url)

            if response.status_code != 200:
                # TODO: handle error
                raise NotImplemented()

            commit_list_page = BeautifulSoup(response.text, "lxml") 
            self.parse_links(commit_list_page)
            button = self.get_button(commit_list_page)

    def get_button(self, commit_list_page):
        button = commit_list_page.find_all('a', class_='btn BtnGroup-item')
        if len(button) == 0 or button[-1].get_text() != 'Older':
            return None
        return button[-1]

    def parse_links(self, commit_list_page):
        timeline_items = commit_list_page.find_all("div", class_="TimelineItem-body")
        for item in timeline_items:
            list_items = item.find_all('li')
            for li in list_items:
                url = self.get_commit_url_from_list_item(li)
                date = self.get_commit_date_from_list_item(li)
                self.crawl_queue.put(Commit(url, date))

    def get_commit_url_from_list_item(self, item):
        p = item.find('p', class_ = 'mb-1')
        link = p.find('a')
        relative_url = link.attrs['href']
        return Repository.Github_URL + relative_url

    def get_commit_date_from_list_item(self, item):
        text = item.find('relative-time', class_='no-wrap').attrs['datetime']
        date = {
            'year': text[:4],
            'month': text[5:7], 
            'day': text[8:10],
            'hour': text[11:13], 
            'minutes': text[14:16], 
            'seconds': text[17:19]
        }
        return datetime(*list(map(int,date.values())))


    def post_scrape_callback(self, res):
        result = res.result()
        if result.status_code == 200:
            self.parse_commit(result.text)
        else:
            # TODO: handle error
            raise NotImplemented
        
    def parse_commit(self, text):
        page = BeautifulSoup(text, 'lxml')
        message = self.get_message(page)
        diff = self.get_diff(page)

    def get_message(self, page):
        # Commits Can also have description and branch
        return page.find('div', {'class':['commit-title', 'markdown-title']}).get_text()

    def get_diff(self, page):
        diff_bar = page.find('div', class_= 'js-diff-progressive-container')
        diff_items = diff_bar.findChildren('div', recursive=False)
        diff_items_filtered = list(filter(
            lambda item: (item.attrs['data-file-deleted'] == 'false') and (item.attrs['data-tagsearch-lang'] == 'Python'), 
            diff_items
        ))
        diff_string = ''
        for item in diff_items_filtered:
            path = item.attrs['data-tagsearch-path']
            diff_string += self.get_diff_string(item)
        return diff_string
        

    def get_diff_string(self, item):
        # TODO: I have ignored blob code (@@ ---- @@) and no-nl-marker (no entry sign) and context rows (rows that dont have + or - tag)
        code_cell = item.find('div', class_ = 'js-file-content Details-content--hidden position-relative')
        code_table = code_cell.find('table')
        table_body = code_table.find('tbody')
        table_rows = table_body.find_all('tr', class_ = 'show-top-border')
        table_rows_code_column = list(map(lambda x : x.find_all('td')[-1].find('span'), table_rows))
        codes = []
        actions_symbols = []
        for row in table_rows_code_column:
            symbol = row.attrs['data-code-marker']
            if symbol != ' ':
                actions_symbols.append(symbol)
                code = row.get_text()
                codes.append(code)    
        diff_string = ''
        for symbol, code in zip(actions_symbols, codes):
            if symbol != 'c':
                diff_string += f'{symbol} {code}\n'
        return diff_string

    # def info(self):
    #     print('\n Seed URL is: ', self.seed_url, '\n')
    #     print('Scraped pages are: ', self.scraped_pages, '\n')
 
repo = Repository('MMVahedi','Github-Commit-Crawler')
cc = MultiThreadedCrawler(repo, 1)
cc.run_web_crawler()