
# coding: utf-8

# In[ ]:


# -*- coding: utf-8 -*- 
import urllib.request
import codecs
import time
from datetime import datetime as dt
from collections import Counter
from bs4 import BeautifulSoup
import pandas
import re

# 注意
# 1. ジャパンカップの日と有馬記念の日は11レースまでしか
# ないので、適当にスクリプトを書き換えて実行してください。
# 2. 「取消」「除外」「中止」「失格」などの事象については、
# 手動で除去してください。
# 3. 新馬戦の馬体重増減は「, - ,」となっているので、
# 「スペース、ハイフン、スペース」を除去してください。

for month in range(1,13):
        cal_html=urllib.request.urlopen("http://keiba.yahoo.co.jp/schedule/list/2016/?month="+str(month))
        cal_soup = BeautifulSoup(cal_html,"lxml")
        
        for atag in cal_soup.find_all("a",href=re.compile("/race/list/.*$")):
                race_src=atag.get("href")
                race_src=re.sub(r"/$","",race_src)
                race_src=re.sub(r"list","result",race_src)
                for race_no in range(1,13):
                        race="http://keiba.yahoo.co.jp"+str(race_src)+str(race_no).rjust(2,"0")
                        race_html=urllib.request.urlopen(race)
                        race_soup=BeautifulSoup(race_html,"lxml")

                        # 日付の取得
                        race_date=race_soup.find_all("h4")
                        race_date=re.sub(r"<[^>]*?>","",str(race_date))
                        race_date=re.sub(r"[年月]","/",str(race_date))
                        race_date=re.sub(r"[\[\]]","",str(race_date))
                        race_date=re.sub(r"日.*$","",str(race_date))
                        race_date=dt.strptime(race_date,"%Y/%m/%d")
                        race_date=re.sub(" 00:00:00","",str(race_date))
#                        print(race_date)

                        # 競馬場名の取得
                        race_course_num=race_src[15:17]
#                        print(race_course_num)
                        if race_course_num == "01":
                                race_course="札幌"
                        elif race_course_num == "02":
                                race_course="函館"
                        elif race_course_num == "03":
                                race_course="福島"
                        elif race_course_num == "04":
                                race_course="新潟"
                        elif race_course_num == "05":
                                race_course="東京"
                        elif race_course_num == "06":
                                race_course="中山"
                        elif race_course_num == "07":
                                race_course="中京"
                        elif race_course_num == "08":
                                race_course="京都"
                        elif race_course_num == "09":
                                race_course="阪神"
                        elif race_course_num == "10":
                                race_course="小倉"

#                        print(race_course)

                        # レース番号はrace_no

                        # レース名の取得
                        race_name=race_soup.find_all("h1",class_="fntB")
                        race_name=re.sub(r"<[^>]*?>","",str(race_name))
                        race_name=re.sub(r"[ \n\[\]]","",str(race_name))
                        # 大阪―ハンブルグカップ対策
                        race_name=re.sub(r"[—―]","-",str(race_name))
                        # 19XX-19XXsダービーメモリーズ対策
                        race_name=re.sub(r"〜","-",str(race_name))
                        # 重賞の回次を削除
                        race_name=re.sub(r"第.*?回","",str(race_name))
#                        print(race_name)

                        # コース区分・距離の取得
                        race_info=race_soup.find_all("p",class_="fntSS gryB",attrs={'id':'raceTitMeta'})
                        track=re.sub(r"\n","",str(race_info))
                        track=re.sub(r" \[.*","",str(track))
                        track=re.sub(r"[\[m]","",str(track))
                        track=re.sub("・外","",str(track))
                        track=re.sub("・内","",str(track))
                        track=re.sub(r"・"," ",str(track))
                        track=re.sub(r" ",",",str(track))
                        track=re.sub(r"<[^>]*?>","",str(track))
#                        print(track)

                        # 馬場状態の取得
                        cond=race_soup.find_all("img",attrs={'width':'25'})
                        cond=re.sub(r"\[<img alt=\"","",str(cond))
                        cond=re.sub(r"\" border.*$","",str(cond))
#                        print(cond)

                        # 賞金額の取得
                        prize=re.sub(r".*本賞金：","",str(race_info))
                        prize=re.sub(r"\n","",prize)
                        prize=re.sub(r"、.*","",prize)
                        prize=int(prize)
#                        print(prize)

                        # 出走馬の取得
                        horses=race_soup.find_all("a",href=re.compile("/directory/horse"))
                        horses=re.sub(r"<[^>]*?>","",str(horses))
                        horses=re.sub(r"[\[\]]","",str(horses))
                        horses=horses.split(", ")
                        horses_num=len(horses)

                        # 馬情報の取得
                        horse_info_all=race_soup.find_all("table",attrs={'id':'resultLs'})
                        for elem in horse_info_all:
                                horse_info=elem.find_all("td")
                                horse_info=re.sub(r"<[^>]*?>","",str(horse_info))
                                horse_info=re.sub(r"\([1-9]+?\)","",str(horse_info))
                                horse_info=re.sub("\(",", ",str(horse_info))
                                horse_info=re.sub("\)","",str(horse_info))
                                horse_info=re.sub("\+","",str(horse_info))
                                horse_info=re.sub("[☆★△▲]","",str(horse_info))
#                                horse_info=re.sub(" ","　",str(horse_info))
                                horse_info=re.sub(r"[\[\]]","",str(horse_info))
                                horse_info=re.sub(r"\n","",str(horse_info))

                                horse_info=horse_info.split(", ")
#                               print(str(horse_info[0:17]))
                                i=0
                                j=17
                                out=codecs.open("./jra_race_result_2016.csv","a","utf-8")
                                for num in range(1,horses_num+1):
                                        each_horse=horse_info[i:j]

                                        if each_horse[0]=="中止" or each_horse[0]=="取消" or each_horse[0]=="除外" or each_horse[0]=="失格":
                                                this_result=99
                                        else:
                                                this_result=int(each_horse[0])

                                        # 獲得賞金額の設定
                                        if this_result==1:
                                                this_prize=prize
                                        elif this_result==2:
                                                this_prize=prize*0.4
                                        elif this_result==3:
                                                this_prize=prize*0.25
                                        elif this_result==4:
                                                this_prize=prize*0.15
                                        elif this_result==5:
                                                this_prize=prize*0.1
                                        else:
                                                this_prize=0

                                        # タイムの秒換算
                                        counter=Counter(str(each_horse[6]))
                                        if counter['.'] == 0:
                                                horse_time=""
                                                horse_time_sec=""
                                        else:
                                                if counter['.'] == 1:
                                                        horse_time_orig=re.sub(r"$","0",str(each_horse[6]))
                                                        horse_time=dt.strptime(horse_time_orig,"%S.%f")
                                                        horse_time_sec=(horse_time.second+(horse_time.microsecond/1000000))
                                                else:
                                                        horse_time_orig=re.sub(r"^|$","0",str(each_horse[6]))
                                                        horse_time=dt.strptime(horse_time_orig,"%M.%S.%f")
                                                        horse_time_sec=(horse_time.minute*60)+horse_time.second+(horse_time.microsecond/1000000)

                                        each_horse[6]=horse_time_sec

                                        # 性別と馬齢の分離
                                        sex=re.sub(r"[0-9]","",str(each_horse[-13]))
                                        sex=re.sub(r"せん","セ",str(sex))
                                        age=re.sub(r"[牡牝せん]","",str(each_horse[-13]))
                                        each_horse[-13]=sex
                                        each_horse.insert(-12,age)
                                        each_horse=re.sub(r"'","",str(each_horse))
                                        each_horse=re.sub(r", ",",",str(each_horse))
                                        each_horse=re.sub(r"[\[\]]","",str(each_horse))

                                        # 調教評価の取得
                                        time.sleep(3)
                                        train_url="http://race.netkeiba.com/?pid=race_old&mode=oikiri&id=c20"+race[-10:]
                                        train_df=pandas.io.html.read_html(train_url)
                                        train_comment=train_df[0][3][1:]
                                        train_mark=train_df[0][4][1:]
                                        
                                        train_comment_list=[0]*len(train_comment)
                                        train_mark_list=[0]*len(train_mark)
                                        
                                        k=1
                                        for v in range(1,len(train_mark_list)+1):
                                                if train_comment[k] == None:
                                                        train_comment_list[int(v)-1]="NA"
                                                else:
                                                        train_comment_list[int(v)-1]=train_comment[k]

                                                if train_mark[k] == None:
                                                        train_mark_list[int(v)-1]="NA"
                                                else:
                                                        train_mark_list[int(v)-1]=train_mark[k]

                                                k+=1

                                        x=each_horse.split(",")[2]
                                        out.write(str(race_date)+","+race_course+","+str(race_no).rjust(2,"0")+","+race_name+","+track+","+cond+","+str(this_prize)+","+str(horses_num)+","+each_horse+","+str(train_comment_list[int(x)-1])+","+str(train_mark_list[int(x)-1])+"\n")
                                        print(str(race_date)+","+race_course+","+str(race_no).rjust(2,"0")+","+race_name+","+track+","+cond+","+str(this_prize)+","+str(horses_num)+","+each_horse+","+str(train_comment_list[int(x)-1])+","+str(train_mark_list[int(x)-1]))
                                        i=i+17
                                        j=j+17


                                out.close()

