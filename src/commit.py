import datetime

class Commit:

    def __init__(self, url : str, date : datetime, message : str = '', diff : str = ''):
        self.URL = url
        self.date = date
        self.message = message
        self.diff = diff

    def update(self, message : str, diff : str):
        self.message = message
        self.diff = diff