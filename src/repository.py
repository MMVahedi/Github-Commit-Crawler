import requests

class Repository:
    All_Repositories = []
    Github_URL = "https://github.com"

    def __init__(self, owner : str, name : str):
        self.owner = owner
        self.name = name
        self.is_ripo_valid()
        self.commits = []
        Repository.All_Repositories.append(self)

    def get_URL(self):
        return f'{Repository.Github_URL}/{self.owner}/{self.name}'

    def is_ripo_valid(self):
        if requests.get(self.get_url).status_code != 200:
            raise Exception('Invalid Repository!')