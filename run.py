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

def notify(title, msg,type_msg='success'):
    requests.post('https://api.mynotifier.app', 
      { "apiKey": '4205bdea-e8ed-429f-bad9-71406aa6017a',    
        "message": title,    
        "description": msg,    
        "type": type_msg, # info, error, warning or success
      })
    
def ada(nama,kelas,harga,tanggal,jam_berangkat,avail,dept,arvl):
    return f"{nama} - {kelas} {harga}. {tanggal} dan {jam_berangkat}. Berangkat {dept}, tujuan {arvl}. Sisa kursi: {avail}"
def habis(nama,tanggal):
    return f"{nama} habis untuk {tanggal}"
def gak_ada_samsek(tanggal,dept,arvl):
    return f"Kereta {tanggal} berangkat {dept} dengan tujuan {arvl} habis"
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

    #retry procedure 
    wait_dur=60*no_of_try
    no_of_try+=2
    print('nunggu',wait_dur,'seconds for try number',no_of_try)
    time.sleep(wait_dur)
def ring(ring_repeat):
  for _ in range(ring_repeat):
    playsound('sounds/mixkit-happy-bells-notification-937.wav')
    time.sleep(3)
def main(url,nama_kereta_lst,stops_name,prev_msgs,verbose=0): #names loop
  # print('masuk main')
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
                              'Banyak!'#df['Available Seats']
                                )
                              )
  time_str=f'access time: {access_time}.'

  # stops_name={key: 0 for key in nama_kereta_lst} #defaulted in the input

  for nama_kereta in nama_kereta_lst:
  # for nama_kereta in [name for name,stop in stops_name.items()  if stop==0]: #only 
    # print('\nnama kereta being looked at: ',nama_kereta)
    lst_of_schedules_for_said_name=df[df['Name'].str[:5].str.lower()==nama_kereta[:5].lower()]
    messages={}
    if len(lst_of_schedules_for_said_name) == 0:
       if verbose==1:
          print('Nama kereta yang dicari tidak ada')
    else: 
      for i,row in lst_of_schedules_for_said_name.iterrows(): #matching method needs serious care. first 5 leters accounting name as short as progo
          if row['Availability']>'0': #!!!!!!!!!!!!1
              messages[i]=ada(row['Name'],row['Class'],row['Price'],df.iloc[0,0],row['Departure Time'],row['Availability'],row['Departure Station'],row['Arrival Station'])
              # msg=f" sisa kursi: {row['Availability']}\n{row['Departure Station']}->{row['Arrival Station']}"              
              # notify(f'{nama_kereta.upper()} ADA COY',msg) #send msg to app

              #what happens if the said name is available (stop = 1)
              stops_name[nama_kereta]=1
    if stops_name[nama_kereta]==0:
        if verbose==1:
          print(f'''{time_str} {habis(nama_kereta,df.iloc[0,0])}''')
  if prev_msgs!=messages:
    if len(messages)==0 or messages=={0:'init'}:
      print(time_str+'\n'+gak_ada_samsek(row['Date'],row['Departure Station'],row['Arrival Station']))   
    elif len(messages)>0:
      ring(ring_repeat)
      print(time_str+' Tersedia:\n',messages) #only print
    prev_msgs=messages   
  n_name_stops=sum(stops_name.values())
  stop=1 if n_name_stops>=len(stops_name) else 0   

  return stop,stops_name,messages

#buat sekarang anggapannya, tiap list nama kereta dicari di setiap url
# parser = argparse.ArgumentParser(description='Reconstruct full URL from input URL and query parameters.')

# # Define command-line arguments
# parser.add_argument('urls',nargs='+',help='kai search results link (single value)')
# parser.add_argument('--train_name', '-o', nargs='+', default='', help='train name to look for (multiple values allowed. if none given, no specific notice would be given)')

# # Parse the command-line arguments
# args = parser.parse_args()

# # Access the values
# urls_arg = args.urls
# name_arg = args.train_name

# print(urls_arg,'_______end of arg')
# print(name_arg,'_______end of arg')

urls_arg=[input('úrl')]
name_arg=input('nama kereta (kosongin kl mau semua)').split(',')
# print('namearg',name_arg) 

warnings.simplefilter(action='ignore', category=FutureWarning)
ring_repeat=3 #no sound being 0
# print('úrls:',urls_arg)
urls_list=urls_arg
# urls =   {key: value for key, value in enumerate(urls_arg)} 
# print('urls dict',urls)
# urls={
#     'berangkat_26':"https://booking.kai.id/search?origination=u%2FdpZtuBY%2FMLjHWA6HQQyQ%3D%3D&destination=niaOzwDtEN%2B0isrzPdZtsg%3D%3D&tanggal=oQ7Kp43w21OuuPymVZs74elFtXmv%2FcOltT%2Bqy7fdmgQ%3D&adult=MnFy%2BP2MvzZq0fSHyM16Vw%3D%3D&infant=E%2FKDC%2BSur3Kyls7NptMgcg%3D%3D&book_type="
#    ,'pulang_28':"https://booking.kai.id/search?origination=VthgI41W1ksmuUuxhNY5yQ%3D%3D&destination=HGQWnwgcp1bxJ%2BJ7TFJ0UA%3D%3D&tanggal=d%2FeFm1UubAi2rFZSVBWxadkCqBmxyLC1GOGCy%2BXFT8Q%3D&adult=GTd27fsGEl79bnZL4lupig%3D%3D&infant=DwEeh8USIyXiqKqyFyF7jQ%3D%3D&book_type="
# }
# python run.py "https://booking.kai.id/search?origination=u%2FdpZtuBY%2FMLjHWA6HQQyQ%3D%3D&destination=niaOzwDtEN%2B0isrzPdZtsg%3D%3D&tanggal=oQ7Kp43w21OuuPymVZs74elFtXmv%2FcOltT%2Bqy7fdmgQ%3D&adult=MnFy%2BP2MvzZq0fSHyM16Vw%3D%3D&infant=E%2FKDC%2BSur3Kyls7NptMgcg%3D%3D&book_type=" -o progo bengawan
nama_kereta_dicari_lst=[name.title() for name in name_arg]
def cari_unique_name(url): #names loop
  # print('masuk main')
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
  return list(df['Name'].unique())
if name_arg==['']:
    nama_kereta_dicari_lst=cari_unique_name(urls_list[0])
    # print('karena kosong berarti masuk semua nama kereta:',nama_kereta_dicari_lst)
else:
   nama_kereta_dicari_lst=name_arg

stops_url={key: 0 for key in urls_list}
stops_name_ofurl={key: {key: 0 for key in nama_kereta_dicari_lst} for key in urls_list} #nama kereta dicari lst is gonna be unique for next iter, but for now this will do
prev_msgs={0:'init'}

while 1: #loop url
  for url in [url for url,stop in stops_url.items() if stop==0]: #only 
    # if stops_url[url]==0:
    stops_url[url],stops_name_ofurl[url],prev_msgs=main(url,nama_kereta_dicari_lst,stops_name_ofurl[url],prev_msgs)
    if url != list(stops_url.keys())[-1]: #if url was not last in list
      delay_each_url=5
      # print(f'loop for next url, wait for {delay_each_url} secs')
      time.sleep(5) #delay between each url
    # print(stops_name_ofurl[url])

  n_url_stops=sum(stops_url.values())
  # print('sudah berapa url yg selesai:',n_url_stops)
  if n_url_stops>=len(urls_list):
    break

  delay_between_sesh=30

  # print('\n')
  # print(f'loop for next sesh, wait for {delay_between_sesh} secs')
  for _ in tqdm(range(delay_between_sesh),leave=0): #delay between each session
    time.sleep(1) 

