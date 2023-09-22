import multiprocessing, random, requests, logging
from bs4 import BeautifulSoup
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse 
 
class MultiThreadedCrawler:

    github_url = "https://github.com/"

    user_agents = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1", 
        "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"
    ]

    def __init__(self, owner_name : str, repository_name : str, num_workers : int = 10):
        self.owner_name = owner_name
        self.repository_name = repository_name
        self.repository_url = f'{self.github_url}{owner_name}/{repository_name}'
        self.pool = ThreadPoolExecutor(max_workers=num_workers)
        self.crawl_queue = Queue()
        self.session = requests.Session()
        self.branch_name = self.find_branch_name()


    def find_branch_name(self):
        ripo_page = self.get_repo_page()
        soup = BeautifulSoup(ripo_page, "xml")
        branch_select_menu = soup.find_all(
            name = 'details',
            attrs = {
                'id' : 'branch-select-menu'
            }
        )[0]
        branch_name = branch_select_menu.find_all(
            name = 'span',
            attrs = {
                'class' : 'css-truncate-target'
            }
        )[0].get_text()
        return branch_name

    def get_repo_page(self):
        status_code, content = self.scrape_page(self.repository_url)
        if status_code != 200:
            # TODO: handle error
            raise NotImplemented()
        return content

    def scrape_page(self, url):
        self.session.headers.update({'user-agent': random.sample(self.user_agents, 1)[0]})
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
        starting_commit_page_url = self.repository_url + f'/commits/{self.branch_name}'
        status_code, content = self.scrape_page(starting_commit_page_url)
        if status_code != 200:
            # TODO: handle error
            raise NotImplemented()
        commit_list_page = BeautifulSoup(content, "xml")
        button = self.get_button(commit_list_page)
        commits = self.get_commits_links(commit_list_page)

        while button.has_attr("disabled"):
            status_code, content = self.scrape_page(starting_commit_page_url)
            commit_list_page = BeautifulSoup(content, "xml") 
            commits += self.get_commits_links(commit_list_page)
            button = self.get_button(commit_list_page)
        
        return commits

    def get_button(self, commit_list_page):
        button = commit_list_page.find_all('a', class_='btn BtnGroup-item')
        return button[-1]

    def get_commits_links(commit_list_page):
        timeline_items = commit_list_page.find_all("div", class_="TimelineItem-body")
        commits = []
        for item in timeline_items:
            month, day, year = item.find_all("h2")[0].get_text().replace(',', '').split()[-3:]
            item_commits = item.find_all("p", class_="mb-1")
            relative_links = list(
                map(
                    lambda x:
                        x.find('a', class_="Link--primary text-bold js-navigation-open markdown-title"), 
                        item_commits
                )
            )
            commits.append({
                'date' : (month, day, year),
                'relative_links' : relative_links
            })
        return commits


    def parse_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        Anchor_Tags = soup.find_all('a', href=True)
        for link in Anchor_Tags:
            url = link['href']
            if url.startswith('/') or url.startswith(self.root_url):
                url = urljoin(self.root_url, url)
                if url not in self.scraped_pages:
                    self.crawl_queue.put(url)
 
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
    cc = MultiThreadedCrawler('mybatis','mybatis-3',1)
    print(cc.branch_name)
    




# import requests
# from bs4 import BeautifulSoup

# # class commit:
# #     def __init__(self) -> None:
# #         self.ripo = 
# #         self.message = 
# #         self.data = 
# #         self.link = 
# #         self.diff = 
# #         pass

# def find_commits_of_given_ripo(url):
#     res = requests.get(url, timeout=(3, 30))
#     soup = BeautifulSoup(res.text, "xml")
#     timeline_items = soup.find_all("div", class_="TimelineItem-body")
#     for item in timeline_items:
#         month, day, year = item.find_all("h2")[0].get_text().replace(',', '').split()[-3:]
#         commits = item.find_all("p", class_="mb-1")
#         link_to_commits = list(map(lambda x: x.find('a', class_="Link--primary text-bold js-navigation-open markdown-title"), commits))
    



# url = "https://github.com/mybatis/mybatis-3/commits/master"
# find_commits_of_given_ripo(url)

# <a class="Link--primary text-bold js-navigation-open markdown-title" href="/ityouknow/spring-boot-examples/commit/8897031cb6026de6d3366a482564e1ddfd465765">Merge pull request</a>