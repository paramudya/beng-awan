import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings
import argparse
import playsound
from tqdm import tqdm

warnings.simplefilter(action='ignore', category=FutureWarning)

class KAITrainScraper:
    def __init__(self, urls, train_names, delay_between_sesh=30, ring_repeat=0):
        self.urls = urls
        self.train_names = [name.title() for name in train_names]
        self.delay_between_sesh = delay_between_sesh
        self.ring_repeat = ring_repeat
        self.prev_msgs = {0: 'init'}

    def notify(self, title, msg, type_msg='success'):
        requests.post('https://api.mynotifier.app', 
          { "apiKey": '4205bdea-e8ed-429f-bad9-71406aa6017a',    
            "message": title,    
            "description": msg,    
            "type": type_msg, # info, error, warning or success
          })

    def ada(self, nama, kelas, harga, tanggal, jam_berangkat, avail, dept, arvl):
        return f"{nama} - {kelas} {harga}. {tanggal} dan {jam_berangkat}. Berangkat {dept}, tujuan {arvl}. Sisa kursi: {avail}"

    def habis(self, nama, tanggal):
        return f"{nama} habis untuk {tanggal}"

    def gak_ada_samsek(self, tanggal, dept, arvl):
        return f"Kereta {tanggal} berangkat {dept} dengan tujuan {arvl} habis"

    def find_soup(self, url):
        no_of_try = 1
        while True:
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            title = soup.find_all('title', limit=1)[0].string
            train_elements = soup.find_all('div', class_='name')
            if not title.lower() == 'waiting page' or len(train_elements) > 0:
                return train_elements

            # retry procedure 
            wait_dur = 60 * no_of_try
            no_of_try += 1
            for _ in tqdm(range(100), desc=f'Try number {no_of_try}. Wait for {wait_dur} s...'):
                time.sleep(wait_dur / 100)

    def ring(self):
        for _ in range(self.ring_repeat):
            # playsound('sounds/mixkit-happy-bells-notification-937.wav')
            time.sleep(3)

    def cari_unique_name(self, elements):
        df = pd.DataFrame()
        for element in elements:
            train_info = pd.DataFrame({
                'Name': element.text.strip(),
            }, index=[0])
            df = pd.concat([df, train_info])
        return list(set(df['Name'].unique()))
    
    def main(self, elements, verbose=0):
        access_time = str(datetime.now())[:19]
        df = pd.DataFrame()
        for element in elements:
            train_info = pd.DataFrame({
                'Date': element.find_next(class_='date-start').text.strip(),
                'Name': element.text.strip(),
                'Class': element.find_next(class_='{kelas kereta}').text.strip(),
                'Departure Station': element.find_next(class_='station-start').text.strip(),
                'Departure Time': element.find_next(class_='time-start').text.strip(),
                'Arrival Station': element.find_next(class_='station-end').text.strip(),
                'Arrival Time': element.find_next(class_='time-end').text.strip(),
                'Price': element.find_next(class_='price').text.strip(),
                'Available Seats': element.find_next(class_='sisa-kursi').text.strip()
            }, index=[0])
            df = pd.concat([df, train_info])

        df['Price in Rp'] = df['Price'].str[3:-2].str.replace('.', '')
        df['Availability'] = np.where(df['Available Seats'] == 'Habis', '0',
                                      np.where(df['Available Seats'].str[:7] == 'Tersisa',
                                               df['Available Seats'].str[8:10].str.strip(),
                                               'Banyak!'))

        time_str = f'access time: {access_time}.'

        messages = {}
        for nama_kereta in self.train_names:
            lst_of_schedules_for_said_name = df[df['Name'].str[:5].str.lower() == nama_kereta[:5].lower()]
            if len(lst_of_schedules_for_said_name) == 0:
                if verbose == 1:
                    print('Nama kereta yang dicari tidak ada')
                # return messages
            else:
                for i, row in lst_of_schedules_for_said_name.iterrows():
                    if row['Availability'] > '0':
                        messages[row['Name']+row['Class']] = self.ada(row['Name'], row['Class'], row['Price'], df.iloc[0, 0],
                                               row['Departure Time'], row['Availability'], row['Departure Station'],
                                               row['Arrival Station'])

        if self.prev_msgs != messages:
            if len(messages) == 0 or messages == {0: 'init'}:
                print(time_str + '\n' + self.gak_ada_samsek(row['Date'], row['Departure Station'],
                                                             row['Arrival Station']))
            elif len(messages) > 0:
                self.ring()
                print(time_str + ' Tersedia:', *messages.values(),sep='\n')
            self.prev_msgs = messages

        return messages

    def run(self):
        for url in self.urls:
            while True:
                train_elements = self.find_soup(url)

                if self.train_names==['']:
                    self.train_names = self.cari_unique_name(train_elements)
                self.main(train_elements)
                for _ in tqdm(range(self.delay_between_sesh), leave=0,
                              desc=f'Delay between session. {self.delay_between_sesh}s wait'):
                    time.sleep(1)

def args():
    parser = argparse.ArgumentParser(description='Reconstruct full URL from input URL and query parameters.')

    parser.add_argument('urls', nargs='+', help='kai search results link (single value)')
    parser.add_argument('--train_name', '-o', nargs='+', default='',
                        help='train name to look for (multiple values allowed. if none given, no specific notice would be given)')

    args = parser.parse_args()

    return {'urls_arg': args.urls,
            'name_arg': args.train_name}

def user_input_prompt():
    urls_arg = [input('úrl: ')]
    name_arg = input('nama kereta (kosongin kl mau semua, pisahin pake koma kalau lebih dari 1)').split(',')
    return {'urls_arg': urls_arg,
            'name_arg': name_arg}

if __name__ == "__main__":
    # variables = args()
    variables = user_input_prompt()
    urls_arg, name_arg = variables['urls_arg'], variables['name_arg']

    scraper = KAITrainScraper(urls_arg, name_arg)
    scraper.run()