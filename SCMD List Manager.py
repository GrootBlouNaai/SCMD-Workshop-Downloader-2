import subprocess
from bs4 import BeautifulSoup
import requests
import json
import re
from typing import List, Optional, Dict, Any

class SteamWorkshopDownloader:
    def __init__(self, data_path: str = './data/data.json', download_path: str = './data/download.json'):
        self.data_path = data_path
        self.download_path = download_path
        self.data = self.load_json(self.data_path)
        self.download = self.load_json(self.download_path)
        self.appcondition = 'https://steamcommunity.com/app/'
        self.itemcondition = 'https://steamcommunity.com/sharedfiles/filedetails/?id='
        self.collectioncondition = 'https://steamcommunity.com/workshop/browse/?section=collections&appid='
        self.scriptadd = ''

    def load_json(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: File at {path} not found.")
            return None

    def handle_error_3(self):
        print('SCMD List Manager & SCMD Workshop Downloader made by Berdy Alexei\nERROR 3: SCMD List Manager should only be opened when called by SCMD Workshop Downloader\n<<Open SCMD Workshop Downloader instead>>')
        input('\n\n### Press Enter to close this window ###\n\n')
        exit()

    def classify_links(self, links: List[str]) -> (List[str], List[str], int, int):
        items, collections = [], []
        successcount, errorcount = 0, 0
        for coln, link in enumerate(links):
            print(f'Classifying links: {coln + 1} of {len(links)}')
            try:
                soup = BeautifulSoup(requests.get(link).text, 'html.parser')
                collectiondetector = sum(1 for a in soup.find_all('a') if self.collectioncondition in str(a.get('href')))
                if collectiondetector < 1:
                    items.append(link)
                else:
                    collections.append(link)
                successcount += 1
            except Exception as e:
                print(f"Error classifying link {link}: {e}")
                errorcount += 1
        return items, collections, successcount, errorcount

    def analyze_items(self, items: List[str]) -> (List[str], List[str], int):
        gIDi, wIDi = [], []
        errorcount = 0
        for coln, item in enumerate(items):
            print(f'Analyzing items links: {coln + 1} of {len(items)}')
            try:
                soup = BeautifulSoup(requests.get(item).text, 'html.parser')
                for link in soup.find_all('a'):
                    if self.appcondition in str(link.get('href')):
                        duo = str(link.get('href'))
                        break
                gIDi.extend(re.findall('\d+', str(duo)))
                wIDi.extend(re.findall('\d+', str(item)))
            except Exception as e:
                print(f"Error analyzing item {item}: {e}")
                errorcount += 1
        return gIDi, wIDi, errorcount

    def generate_script(self, gIDi: List[str], wIDi: List[str], repeat: int, bscim: bool) -> str:
        scriptadd = ''
        for wIDc in range(len(wIDi)):
            scriptadd += f' +workshop_download_item {gIDi[wIDc]} {wIDi[wIDc]} validate'
            if bscim:
                for _ in range(repeat):
                    scriptadd += f' +workshop_download_item {gIDi[0]} {wIDi[wIDc]} validate'
                print(f'BSIM Treatment given to item #{wIDc + 1} repeated {repeat} time/s.')
        return scriptadd

    def run(self):
        if not self.download:
            self.handle_error_3()

        repeat = self.data["repeat"]
        mode = self.data["mode"]
        bscim = self.data["bscim"]

        if mode in [1, 3, 5]:
            items, collections, successcount, errorcount = self.classify_links(self.download['list'])
            gIDi, wIDi, item_errors = self.analyze_items(items)
            errorcount += item_errors
            self.scriptadd = self.generate_script(gIDi, wIDi, repeat, bscim)

            if (errorcount > 0 and successcount == 0) or successcount == 0:
                print('ERROR 2: All introduced links are wrong')
                print('<< Having a bad Internet connection can also make this error to happen. Try again later. >>')
            else:
                script = self.download["script"] + self.scriptadd
                datetime = self.download["datetime"]
                self.save_json('', self.download_path)
                if mode in [3, 5]:
                    self.write_script(script, datetime[0])
                if mode in [1, 5]:
                    self.execute_script(script)
        else:
            print('Analysing links... (Single-mode)')
            try:
                soup = BeautifulSoup(requests.get(self.download["list"][0]).text, 'html.parser')
                for link in soup.find_all('a'):
                    if self.appcondition in str(link.get('href')):
                        applink = str(link.get('href'))
                        break
                gIDi = re.findall('\d+', str(applink))
                wIDi = re.findall('\d+', str(self.download["list"]))
                self.scriptadd = self.generate_script(gIDi, wIDi, repeat, bscim)
                script = self.download["script"] + self.scriptadd
                if mode in [2, 4]:
                    self.write_script(script, self.download["datetime"][0])
                if mode in [0, 4]:
                    self.execute_script(script)
            except Exception as e:
                print(f"ERROR 1: The first link entered is incorrect: {e}")
                print('<< Having a bad Internet connection can also make this error to happen. Try again later. >>')

        self.save_json('', self.download_path)

    def write_script(self, script: str, datetime: str):
        with open(f'./generated scripts/script {datetime}.bat', 'w') as writer:
            writer.write(script)
        print(f'Script generated as: script {datetime}.bat')

    def execute_script(self, script: str):
        try:
            print('Download started\n')
            subprocess.call(script)
        except FileNotFoundError:
            print('\nERROR 0: Too many elements tried to be downloaded. Close this Window and try again introducing less.\n')

    def save_json(self, data: Any, path: str):
        with open(path, 'w') as f:
            json.dump(data, f)

if __name__ == "__main__":
    downloader = SteamWorkshopDownloader()
    downloader.run()
