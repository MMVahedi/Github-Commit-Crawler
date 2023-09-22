import requests
from commit import Commit
from bs4 import BeautifulSoup


class Repository:
    All_Repositories = []
    Github_URL = "https://github.com"

    def __init__(self, owner : str, name : str):
        self.owner = owner
        self.name = name
        status_code, text = self.fetch_repo_page()
        self.is_ripo_valid(status_code)
        self.page = BeautifulSoup(text, "lxml")
        self.branch = self.get_branch_name()
        self.commits = []
        Repository.All_Repositories.append(self)

    def get_URL(self):
        return f'{Repository.Github_URL}/{self.owner}/{self.name}'

    def is_ripo_valid(self, status_code):
        if status_code != 200:
            raise Exception('Invalid Repository!')
        
    def fetch_repo_page(self):
        page = requests.get(self.get_URL())
        return page.status_code, page.text

    def get_branch_name(self):
        branch_select_menu = self.page.find_all(
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
    
    def add_commit(self, commit : Commit):
        self.commits.append(commit)