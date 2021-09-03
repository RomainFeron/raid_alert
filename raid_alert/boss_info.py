import json
import re
import requests
from bs4 import BeautifulSoup
from .commons import load_json_to_dict


BOSS_LIST_URL = 'https://l2unity.net/data/x10/boss'
BASE_URL = 'https://l2.dropspoil.com'
QUERY_URL = BASE_URL + '/?s={query}'
MAP_BASE_URL = BASE_URL + '/loc/{boss_id}/{boss_name}.html'
BOSS_ID_REGEX = r'/npc/(\d+)/(.+)\.html'
MINIM_NUMBER_REGEX = r'\(\d+\) \((\d+)-(\d+)\)'
GOOD_DROPS_FILE_PATH = 'config/drops.json'
GOOD_DROPS_TABLE = load_json_to_dict(GOOD_DROPS_FILE_PATH)
BOSS_FIX_FILE_PATH = 'config/boss_fix.json'
BOSS_FIX = load_json_to_dict(BOSS_FIX_FILE_PATH)


def get_boss_list():
    '''
    '''
    boss_list = {}
    page = requests.get(BOSS_LIST_URL)
    parsed_page = BeautifulSoup(page.text, 'lxml')
    table = parsed_page.find_all('table')[0]
    for row in table.find_all('tr')[1:]:
        if len(row) == 4:
            fields = [field.text.strip() for field in row.find_all('td')]
            boss_list[fields[0]] = fields[1]
    return boss_list


def check_boss(boss, level, good_drops_table=GOOD_DROPS_TABLE, boss_fix=BOSS_FIX):
    '''
    '''
    levels_fix = boss_fix['levels']
    if boss in levels_fix:
        level = str(levels_fix[boss])
    names_fix = boss_fix['names']
    if boss in names_fix:
        boss = names_fix[boss]
    boss_info = {'name': boss, 'map_url': None, 'drops': [], 'adds': [0, 0]}
    page = requests.get(QUERY_URL.format(query=boss))
    parsed_page = BeautifulSoup(page.text, 'lxml')
    entries = parsed_page.find_all('td')
    for i, entry in enumerate(entries):
        info_url, map_url = None, None
        entry_text = entry.text.strip().lower()
        if entry_text == boss.lower():
            lvl = entries[i + 1].text.strip()
            if lvl != level:
                continue
            info_url = BASE_URL + entry.a['href']
            parsed_line = re.search(BOSS_ID_REGEX, info_url)
            boss_id = parsed_line.group(1)
            boss_name = parsed_line.group(2)
            map_url = MAP_BASE_URL.format(boss_id=boss_id, boss_name=boss_name)
            boss_info['map_url'] = map_url
        if not (info_url and map_url):
            continue
        info_page = requests.get(info_url)
        parsed_info_page = BeautifulSoup(info_page.text, 'lxml')
        entries = parsed_info_page.find_all('td')
        first_row = entries[0]
        fields = first_row.find_all('a')
        for field in fields[1:]:
            minion_name = field.text.strip()
            if minion_name == '':
                continue
            regex_results = re.search(MINIM_NUMBER_REGEX, field.next_sibling.strip())
            if regex_results:
                min_adds, max_adds = regex_results.group(1), regex_results.group(2)
                boss_info['adds'][0] += int(min_adds)
                boss_info['adds'][1] += int(max_adds)
        for entry in entries:
            entry = entry.text.upper()
            for good_drop in good_drops_table:
                if good_drop in entry:
                    boss_info['drops'].append(GOOD_DROPS_TABLE[good_drop])
    return boss_info


def get_boss_info(boss_info_file_path):
    '''
    '''
    boss_list = get_boss_list()
    boss_info = {}
    for i, boss in enumerate(boss_list):
        print(f'{boss} [{i + 1}/{len(boss_list)}]')
        boss_info[boss] = check_boss(boss, boss_list[boss])
    with open(boss_info_file_path, 'w') as boss_info_file:
        json.dump(boss_info, boss_info_file)
