import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings
import argparse
#buat sekarang anggapannya, tiap list nama kereta dicari di setiap url
parser = argparse.ArgumentParser(description='Reconstruct full URL from input URL and query parameters.')

# Define command-line arguments
parser.add_argument('urls',nargs='+',help='kai search results link (single value)')
parser.add_argument('--train_name', '-o', nargs='+', default='', help='train name to look for (multiple values allowed. if none given, no specific notice would be given)')

# Parse the command-line arguments
args = parser.parse_args()

# Access the values
urls_arg = args.urls
name_arg = args.train_name

print(urls_arg,'_______end of arg')
print(name_arg,'_______end of arg')

warnings.simplefilter(action='ignore', category=FutureWarning)
ring_repeat=5

url=urls_arg
# urls =   {key: value for key, value in enumerate(urls_arg)} 
# print('urls dict',urls)
# urls={
#     'berangkat_26':"https://booking.kai.id/search?origination=u%2FdpZtuBY%2FMLjHWA6HQQyQ%3D%3D&destination=niaOzwDtEN%2B0isrzPdZtsg%3D%3D&tanggal=oQ7Kp43w21OuuPymVZs74elFtXmv%2FcOltT%2Bqy7fdmgQ%3D&adult=MnFy%2BP2MvzZq0fSHyM16Vw%3D%3D&infant=E%2FKDC%2BSur3Kyls7NptMgcg%3D%3D&book_type="
#    ,'pulang_28':"https://booking.kai.id/search?origination=VthgI41W1ksmuUuxhNY5yQ%3D%3D&destination=HGQWnwgcp1bxJ%2BJ7TFJ0UA%3D%3D&tanggal=d%2FeFm1UubAi2rFZSVBWxadkCqBmxyLC1GOGCy%2BXFT8Q%3D&adult=GTd27fsGEl79bnZL4lupig%3D%3D&infant=DwEeh8USIyXiqKqyFyF7jQ%3D%3D&book_type="
# }

# nama_kereta_dicari='Bengawan'
nama_kereta_dicari_lst=[name.title() for name in name_arg]



def notify(title, msg,type_msg='success'):
    requests.post('https://api.mynotifier.app', 
      { "apiKey": '4205bdea-e8ed-429f-bad9-71406aa6017a',    
        "message": title,    
        "description": msg,    
        "type": type_msg, # info, error, warning or success
      })
    
def ada(nama,kelas,tanggal,avail,dept,arvl):
    return f"{nama} ({kelas}) untuk {tanggal} sisa kursi: {avail}\n{dept}->{arvl}"
def habis(nama,tanggal):
    return f"{nama} habis untuk {tanggal}"
def find_soup(url):
  no_of_try=1
  while 1:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    title=soup.find_all('title', limit=1)[0].string
    train_elements=soup.find_all('div', class_='name')
    # print(train_elements)
    if not title.lower() == 'waiting page' or len(train_elements)>0: #bikin komponen
        return train_elements
     
    wait_dur=60*no_of_try
    no_of_try+=2
    print('nunggu',wait_dur,'seconds for try number',no_of_try)
    time.sleep(wait_dur)
  
def main(url,nama_kereta_lst,stops_name={key: 0 for key in nama_kereta_lst}):
  stop=0
  print('masuk main')
  access_time=str(datetime.now())[:19]
  train_elements=find_soup(url)       
  df=pd.DataFrame()
  for element in train_elements:
      # if train_name in element.text:
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
          df=pd.concat([df,train_info])
          
  df['Price in Rp']=df['Price'].str[3:-2].str.replace('.','')
  df['Availability']=np.where(df['Available Seats']=='Habis', '0',
                      np.where(df['Available Seats'].str[:7]=='Tersisa',
                              df['Available Seats'].str[8:10].str.strip(),
                              df['Available Seats']
                                )
                              )
  time_str=f'access time: {access_time}.'

  # stops_name={key: 0 for key in nama_kereta_lst}
  # for nama_kereta in nama_kereta_lst:
  for nama_kereta in [name for name,stop in stops_name.items()  if stop==0]: #only 
    for i,row in df[df['Name'].str[:5].str.lower()==nama_kereta[:5]].iterrows(): #matching method needs serious care. first 5 leters accounting name as short as progo
        if row['Availability']>'0': #!!!!!!!!!!!!1
            print(f'{time_str} TERSEDIA. {msg}') 
            msg=f" sisa kursi: {row['Availability']}\n{row['Departure Station']}->{row['Arrival Station']}"              
            # notify(f'{nama_kereta.upper()} ADA COY',ada(row['Name'],row['Class'],df.iloc[0,0],row['Availability'],row['Departure Station'],row['Arrival Station']))
            print(row)  
            
            i_ring=0
            while i_ring<ring_repeat:
              playsound('sounds/mixkit-happy-bells-notification-937.wav')
              time.sleep(10)
            #what happens if the said name is available (stop = 1)
            stops_name[nama_kereta]=1

    if stop==0:
        print(f'''{time_str} {habis(nama_kereta,df.iloc[0,0])}''')
  return stop

stops_url={key: 0 for key in urls_list}
while 1: #loop url
  for url in [url for url,stop in stops_url.items()  if stop==0]: #only 
    # if stops_url[url]==0:
    if 
    stops_url[url],stops_name=main(url,nama_kereta_dicari_lst,stops_name)
    time.sleep(60) #delay between each url

  if sum(stops_url.values())<len(urls_list):
    break
  time.sleep(300) #delay between each session