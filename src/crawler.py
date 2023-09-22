import multiprocessing, random, requests, logging, datetime
from bs4 import BeautifulSoup
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse 
from repository import Repository
from commit import Commit
 
class MultiThreadedCrawler:

    github_url = "https://github.com/"

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
        try:
            response = self.session.get(url)
            return response.status_code, response.text
        except Exception as e:
            return -1, e
    
    def run_web_crawler(self):
        commits = self.find_repo_commits_links()
        # self.fill_queue(commits)
        while True:
            try:
                print("\n Name of the current executing process: ",
                      multiprocessing.current_process().name, '\n')
                target_url = self.crawl_queue.get(timeout=60)
                if target_url not in self.scraped_pages:
                    print("Scraping URL: {}".format(target_url))
                    self.current_scraping_url = "{}".format(target_url)
                    self.scraped_pages.add(target_url)
                    job = self.pool.submit(self.scrape_page, target_url)
                    job.add_done_callback(self.post_scrape_callback)
 
            except Empty:
                return
            except Exception as e:
                print(e)
                continue

    def find_repo_commits_links(self):
        starting_commit_page_url = self.repo.get_URL() + f'/commits/{self.repo.branch}'
        status_code, content = self.scrape_page(starting_commit_page_url)
        if status_code != 200:
            # TODO: handle error
            raise NotImplemented()
        commit_list_page = BeautifulSoup(content, "xml")
        button = self.get_button(commit_list_page)
        commits = self.parse_commits(commit_list_page)

        while not button.has_attr("disabled"):
            status_code, content = self.scrape_page(starting_commit_page_url)
            commit_list_page = BeautifulSoup(content, "xml") 
            commits += self.get_commits_links(commit_list_page)
            button = self.get_button(commit_list_page)
        
        return commits

    def get_button(self, commit_list_page):
        button = commit_list_page.find_all('a', class_='btn BtnGroup-item')
        return button[-1]

    def parse_commits(self, commit_list_page):
        timeline_items = commit_list_page.find_all("div", class_="TimelineItem-body")
        commits = []
        for item in timeline_items:
            list_items = item.find_all('li')
            for li in list_items:
                url = self.get_commit_url_from_list_item(li)
                data = self.get_commit_date_from_list_item(li)
        return list_items 

    def get_commit_url_from_list_item(self, item):
        relative_url = item.attrs['data-url']
        relative_url = '/'.join(relative_url.split('/')[1:-1])   # Remove extra parts
        return self.github_url + relative_url

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



    def scrape_info(self, html):
        soup = BeautifulSoup(html, "html5lib")
        web_page_paragraph_contents = soup('p')
        text = ''
        for para in web_page_paragraph_contents:
            if not ('https:' in str(para.text)):
                text = text + str(para.text).strip()
        print(f'\n <---Text Present in The WebPage is --->\n', text, '\n')
        return
 
    def post_scrape_callback(self, res):
        result = res.result()
        if result and result.status_code == 200:
            self.parse_links(result.text)
            self.scrape_info(result.text)
 

 

 
    def info(self):
        print('\n Seed URL is: ', self.seed_url, '\n')
        print('Scraped pages are: ', self.scraped_pages, '\n')
 
 
if __name__ == '__main__':
    repo = Repository('mybatis','mybatis-3')
    cc = MultiThreadedCrawler(repo, 1)
    print(cc.branch_name)