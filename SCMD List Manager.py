import subprocess
from bs4 import BeautifulSoup
import requests
import json
import re
from typing import List, Optional, Dict, Any

class SteamWorkshopDownloader:
    
    # Manage and download items from the Steam Workshop.
    
    def __init__(self, data_path: str = './data/data.json', download_path: str = './data/download.json'):
        
        # Initialise the Downloader with paths to configuration files.
        
        # :param data_path: Path to the data configuration file.
        # :param download_path: Path to the download configuration file.
        
        self.data_path = data_path
        self.download_path = download_path
        self.data = self.load_json(self.data_path)  # Load data configuration
        self.download = self.load_json(self.download_path)  # Load download configuration
        self.appcondition = 'https://steamcommunity.com/app/'
        self.itemcondition = 'https://steamcommunity.com/sharedfiles/filedetails/?id='
        self.collectioncondition = 'https://steamcommunity.com/workshop/browse/?section=collections&appid='
        self.scriptadd = ''  # Initialize the script addition string

    def load_json(self, path: str) -> Optional[Dict[str, Any]]:
        
        # Load JSON data from a file.
        
        # :param path: Path to the JSON file.
        # :return: JSON data as a dictionary or None if file not found.
        
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: File at {path} not found.")
            return None

    def handle_error_3(self):
        
        # Handle error 3 by printing a message and exiting the program.
        
        print('SCMD List Manager & SCMD Workshop Downloader made by Berdy Alexei\nERROR 3: SCMD List Manager should only be opened when called by SCMD Workshop Downloader\n<<Open SCMD Workshop Downloader instead>>')
        input('\n\n### Press Enter to close this window ###\n\n')
        exit()

    def classify_links(self, links: List[str]) -> (List[str], List[str], int, int):
        
        # Classify links into items and collections.
        
        # :param links: List of links to classify.
        # :return: Lists of items and collections, and counts of successful and error classifications.
        
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
        
        # Analyze items to extract game IDs and workshop item IDs.
        
        # :param items: List of item links.
        # :return: Lists of game IDs and workshop item IDs, and a count of errors.
        
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
        
        # Generate the script for downloading workshop items.
        
        # :param gIDi: List of game IDs.
        # :param wIDi: List of workshop item IDs.
        # :param repeat: Number of times to repeat the download.
        # :param bscim: Boolean to determine if BSIM treatment is needed.
        # :return: The generated script as a string.
        
        scriptadd = ''
        for wIDc in range(len(wIDi)):
            scriptadd += f' +workshop_download_item {gIDi[wIDc]} {wIDi[wIDc]} validate'
            if bscim:
                for _ in range(repeat):
                    scriptadd += f' +workshop_download_item {gIDi[0]} {wIDi[wIDc]} validate'
                print(f'BSIM Treatment given to item #{wIDc + 1} repeated {repeat} time/s.')
        return scriptadd

    def run(self):
        
        # Main execution method to run the downloader.
        
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
        
        # Write the generated script to a file.
        
        # :param script: The script to write.
        # :param datetime: The datetime string to use in the filename.
        
        with open(f'./generated scripts/script {datetime}.bat', 'w') as writer:
            writer.write(script)
        print(f'Script generated as: script {datetime}.bat')

    def execute_script(self, script: str):
        
        # Execute the generated script.
        #
        # :param script: The script to execute.
        
        try:
            print('Download started\n')
            subprocess.call(script)
        except FileNotFoundError:
            print('\nERROR 0: Too many elements tried to be downloaded. Close this Window and try again introducing less.\n')

    def save_json(self, data: Any, path: str):
        #
        # Save data to a JSON file.
        #
        # :param data: The data to save.
        # :param path: The path to the JSON file.
        #
        with open(path, 'w') as f:
            json.dump(data, f)

if __name__ == "__main__":
    downloader = SteamWorkshopDownloader()
    downloader.run()
