
# coding: utf-8

# In[2]:


# 必要なインポートを実施
# スクレイピング用フレームワーク
from bs4 import BeautifulSoup
# リクエスト取得ライブラリ
import requests
# お馴染みPandas
import pandas as pd
# お馴染みSeriesとDataFrame
from pandas import Series,DataFrame
from datetime import datetime as dt
# 正規表現ライブラリ
import re
# データフレームを綺麗に表示させるためのライブラリ
from IPython.display import display, HTML


# In[3]:


# 競馬情報の取得をWebスクレイピングで実施
HOME_URL = 'https://www.nankankeiba.com/'
PLACE = '川崎'

# URLからコンテンツを取得する
def url_to_soup(url):
    req = requests.get(url)
    return BeautifulSoup(req.content, 'html.parser')

# 各馬の過去１０レースリンクを取得(出走表のページを設定)
def horse_page_link(url):
    soup = url_to_soup(url)
    link_list = [HOME_URL + x.get('href') for x in soup.find_all('a', class_='tx-mid tx-low') ]
    return link_list

hors_page_link_list = horse_page_link(HOME_URL + 'race_info/2018082321060403.do')
print(len(hors_page_link_list))


# In[25]:


# HTMLのタグを排除する正規表現
p = re.compile(r"<[^>]*?>")

tag_to_text = lambda x: p.sub("", x).split('\n') 
split_tr = lambda x: str(x).split('</tr>')

# tableタグを取得し、trタグでsqlitする
def get_previous_race_row(soup):
    race_table = soup.select("table.tb01")[2]
    return [tag_to_text(x)  for x in split_tr(race_table)]

# 各馬の過去10レースを取得し、データフレームに入れ込む
def horse_data(url):
    soup = url_to_soup(url)

    # 過去のレースデータ
    pre_race_data = get_previous_race_row(soup)
    df = pd.DataFrame(pre_race_data)[1:][[2,3,10,11,13,14,15,19,23]].dropna().rename(columns={
        2:'date', 3:'place', 10:'len', 11:'wether', 13:'rank', 14:'popularity', 15:'time',19:'weight',23:'money'})
    horse_name = soup.find('h2', id='tl-prof').get_text()
    return horse_name, df


# In[27]:


# 馬場状態のカラム内容を文字列によって変更する
def add_soil_columns(row):
    if row['wether'][-2:] =='/重':
        row['soil'] = 3
    elif row['wether'][-2:] =='稍重':
        row['soil'] = 2
    elif row['wether'][-2:] =='/良':
        row['soil'] = 1
    elif row['wether'][-2:] =='不良':
        row['soil'] = 4
    else :
        row['soil'] = 0
    return row

# 天気のカラム内容を文字列によって変更する
# def add_wether_columns(row):
#     if row['wether'].startswith('晴'):
#         row['wetherNum'] = 1
#     elif row['wether'].startswith('曇'):
#         row['wetherNum'] = 2
#     elif row['wether'].startswith('雨'):
#         row['wetherNum'] = 3
#     else : row['wetherNum'] = 0
#     return row
def add_wether_columns(row):
        row['sunny'] = 1 if row['wether'].startswith('晴') else 0
        row['cloudy'] = 1 if row['wether'].startswith('曇') else 0
        row['rainny'] = 1 if row['wether'].startswith('雨') else 0
        return row
    

# レースデータのカラムを加工
def add_race_data(df):
    df_ =pd.DataFrame()
    for idx, row in df.iterrows():
        if row['popularity'] == '':
            continue

        # 馬場状態
        row = add_soil_columns(row)
        row = add_wether_columns(row)

        row['money']=int(row['money'].replace(',','')) 
        row['horse_cnt'] = int(row['popularity'].split('/')[1])
        row['result_rank'] = int(row['popularity'].split('/')[0])
        row['len'] = int(row['len'][0:4])
        row['popularity'] = int(row['rank'])
        row['weight'] = int(row['weight'])

        # 　競馬場の一致
        row['same_place'] = 1 if row['place'].startswith(PLACE)  else 0

        # タイム(秒)
        try:
            time = dt.strptime(row['time'], '%M:%S.%f')
            row['sec'] = time.minute*60 + time.second + time.microsecond/1000000 
        except ValueError:
            time = dt.strptime(row['time'], '%S.%f')
            row['sec'] = time.second + time.microsecond/1000000

        row['sec'] = int(row['sec']) 

        df_ = df_.append(row, ignore_index=True)
    return df_

df_list = []
# 取得した出走馬の過去レースをデータフレームに格納
for url_link in hors_page_link_list:
    name, df = horse_data(url_link)
    df = add_race_data(df)
    display(df)
    df_list.append(df)
    


# In[15]:


# 該当のレース結果データを取得
def result_data(url):
    soup = url_to_soup(url)

    # 土の状態
    condition = soup.find(id="race-data02").get_text().replace('\n','').split(';')[1].split('　')[2][0:2]

    # レースの長さ
    race_len = int(soup.find(id="race-data01-a").get_text().replace('\n','').split('　')[3].replace(',','')[1:4])

    # 1位の馬番
    p = re.compile('<td class="al-center">')
    hukusyo_list = []
    hukusyo_list.append(int(p.sub("", str(soup.find_all('tr', class_='bg-1chaku')[0]).split('</td>')[2]).replace('\n','') ))

    # レース日
    race_date_str = soup.find(id="race-data01-a").get_text().replace('\n','').split(';')[0].split('日')[0]
    race_date = dt.strptime(race_date_str, '%Y年%m月%d')
    return hukusyo_list, condition, race_len, race_date

a, b, c, d = result_data('https://www.nankankeiba.com/result/2018082321060403.do')
print(d)
print(a)
print(b)
print(c)
# df = horse_data('https://www.nankankeiba.com/result/2018082321060403.do', d)
# df = add_race_data(df)


# In[16]:


def add_grade(df):
    df_grade =pd.DataFrame()
    for idx, row in df.iterrows():
        if row['rank'] == '':
            continue
        row = add_wether_columns(row)
        horse_cnt = row['popularity'].split('/')[0]
        popularity = row['popularity'].split('/')[1]
        # 出走頭数 + ランク()
        row['grade'] = int(horse_cnt) - (int(row['rank']) - 1) + int(popularity)/4 + int(row[TODAY_WETHER]) * 1
        df_grade = df_grade.append(row, ignore_index=True)
    return df_grade


# In[29]:


def horse_index(url):
    soup = url_to_soup(url)
    pre_race_data = get_previous_race_row(soup)
    df = pd.DataFrame(pre_race_data)[1:][[10,11,13,14]].dropna().rename(columns={10:'len', 11:'wether', 13:'rank', 14:'popularity'})
    df = add_grade(df)
    print(df)
    horse_name = soup.find('h2', id='tl-prof').get_text()
    return horse_name, df['grade'].mean()


# In[30]:


def ture_data(url):
    soup = url_to_soup(url)
    return p.sub("", str(soup.find_all('tr', class_='bg-1chaku')[0]).split('</td>')[3]).replace('\n','')


# In[31]:


def main(race_url):
    links = horse_page_link(race_url)
    for link in links:
        horse_name,  grade = horse_index(link)
        print(horse_name+ ':  ' + str(grade))


# In[32]:


def pre_race_analysis(race_page):
    links = horse_page_link(race_page)
    max_grade = 0
    first_horse = ''
    for link in links:
        horse_name,  grade = horse_index(link)
        if grade > max_grade:
            max_grade = grade
            first_horse = horse_name
    
    result = ture_data(race_page.replace('race_info', 'result'))
    
    print('-------------------------------------')
    if first_horse == result:
        print('*********** correct !! ***********')
    print(f'predict -> {first_horse} : {max_grade}')
    print(f'true -> {result}')
    print('-------------------------------------')


# In[34]:


TODAY_WETHER = 'rainny'
race_page ='https://www.nankankeiba.com/race_info/2018052320040310.do'
pre_race_analysis(race_page)

