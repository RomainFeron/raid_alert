import logging
import requests
from bs4 import BeautifulSoup
from .boss import Boss


class BossChecker:

    def __init__(self, url='https://l2unity.net/data/x10/boss'):
        self.url = url
        self.bosses = {}
        self.data = []
        self.updates = []
        for boss in self.data:
            self.bosses[boss[0]] = Boss(name=boss[0], level=boss[1],
                                        status=boss[2], spawn_date=boss[3])

    def get_boss_status(self):
        self.data = []
        page = requests.get(self.url)
        parsed_page = BeautifulSoup(page.text, 'lxml')
        try:
            table = parsed_page.find_all('table')[0]
        except IndexError:
            logging.warning('Error parsing the boss table: not table found')
            return
        try:
            for row in table.find_all('tr')[1:]:
                if len(row) == 4:
                    fields = [field.text.strip() for field in row.find_all('td')]
                    self.data.append(fields)
                    if fields[0] not in self.bosses:
                        self.bosses[fields[0]] = Boss(name=fields[0], level=fields[1],
                                                      status=fields[2], spawn_date=fields[3])
        except IndexError:
            logging.warning('Error parsing the boss table: not table rows')
            return

    def update(self):
        self.updates = []
        self.get_boss_status()
        for boss_data in self.data:
            self.bosses[boss_data[0]].update(boss_data)
            if self.bosses[boss_data[0]].has_spawned:
                self.updates.append(self.bosses[boss_data[0]])
            if self.bosses[boss_data[0]].has_died:
                self.updates.append(self.bosses[boss_data[0]])
