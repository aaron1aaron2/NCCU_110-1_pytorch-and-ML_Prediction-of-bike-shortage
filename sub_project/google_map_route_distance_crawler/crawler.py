# coding: utf-8
import re
import os
import csv
import math
import time
import tqdm
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

from IPython import embed

class crawler:
    def __init__(self, input_data, output_path, vehicle_type='car'):
        self.input_path = input_data # 原始檔的檔案名稱
        self.output_path = output_path

        # 可使用的交通工具
        self.vehicle_type_dt = {'car':'0', 'bike':'1', 'walk':'2', 'bus':'3'}
        self.vehicle_type = self.vehicle_type_dt[vehicle_type]

        self.error_path = os.path.join(output_path, 'error_url.txt')
        self.error_ls = []

    # 刪除起訖點為同一點的資料
    def load_data(self, data):
        df = pd.read_csv(data, encoding='utf-8', usecols=['start_coordinate', 'end_coordinate'])
        df = df[df['start_coordinate'] != df['end_coordinate']]
        df['route'] = df['start_coordinate']+'/'+df['end_coordinate']
        df['route'].drop_duplicates(inplace=True)

        print('target->{}'.format(df.shape[0]))
        print('check output file')

        if os.path.exists(self.output_path):
            if os.stat(self.output_path).st_size != 0:
                df_check = pd.read_csv(self.output_path, header=None)
                df = df[~df['route'].isin(df_check[0])]

        leftover_num = df.shape[0]

        if leftover_num == 0:
            print('Completed all goals')
            exit()
        else:
            print('leftover->{}'.format(leftover_num))

        return df['route'].values

    def launch_chrome(self):

        chrome_options = Options() #webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # 無視窗
        chrome_options.add_argument("--incognito") # 無痕
        chrome_options.add_argument('--disable-gpu')
        ua = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0"
        chrome_options.add_argument("user-agent={}".format(ua))

        try:
            browser = webdriver.Chrome(executable_path=self.chromedriver, options=chrome_options)
        except:
            browser = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options)

        browser.get('http://checkip.amazonaws.com/')
        soup = BeautifulSoup(browser.page_source, "html.parser")
        ip = soup.text.strip()

        print(f'current ip: {ip}')

        return browser

    # Google map爬蟲
    def route_crawler(self, browser, url):
        minute = []
        count = 0
        # 最多執行50次，沒有的話則輸出nan，並切換IP
        while not minute:
            time.sleep(0.5)
            count += 1

            # 重製 chrome driver
            if count == 10:
                browser.close()
                browser = self.launch_chrome()
                print(f'[Error] Restart chrome driver')
                    
            # 無法成功獲取的 url
            if count == 20:
                print(f'[Error] {url} not available')
                self.error_ls.append(url)
                break
            
            # 爬取資料
            try:
                embed()
                exit()
                browser.get(url) #最後一碼為0汽車、2走路
                _ = browser.find_element_by_xpath('//*[@id="section-directions-trip-travel-mode-0"]') #等到找到這個在往下
                
                soup = BeautifulSoup(browser.page_source, "html.parser")

                # 路徑
                routes = soup.find_all("h1", class_ = re.compile(".+trip.+"))
                routes = [i.text for i in routes if i.text.strip()!='']

                # 時間
                minute = soup.find_all("div", class_ = re.compile(".+trip.+"))
                minute = [(i.text, re.findall(r'\d+\D{,3}', i.text)) for i in minute if (len(i.text)<40) & (i.text.strip()!='')]
                minute = [[text, 'distance', [''.join(select_ls)]] if (text.find('公里') !=-1 | text.find('公尺')) else (
                                [text, 'trip duration', select_ls] if (text.find('預估行車時間') != -1) else (
                                [text, 'trip duration(Smooth)', select_ls] if (text.find('交通順暢') != -1) else
                                [text, 'unknow', select_ls]
                                )) for text, select_ls in minute if len(select_ls)!=0]

                # 整理輸出
                tmp = []
                rt_idx = -1
                for text, item_type, initial_value in minute:
                    if item_type == 'trip duration':
                        rt_idx += 1
                    if rt_idx >= len(routes):
                        tmp.append(['unknown', text, item_type, initial_value, url])
                    else:
                        tmp.append([routes[rt_idx], text, item_type, initial_value, url])

            except Exception as inst:
                print(type(inst))    # the exception instance
                print(inst.args)     # arguments stored in .args
                print(inst)   

        return browser, tmp

    def output_data(self, result):
        csvfile = open(self.output_path, 'a', newline='', encoding='utf-8')
        writer = csv.writer(csvfile)
        for i in result:
            combine = [coor_name] + i
            writer.writerow(combine)

        csvfile.close()

    def run(self):
        # 讀取資料
        df = self.load_data(self.input_path)

        browser = self.launch_chrome()
        browser.implicitly_wait(5) # 靜態等待 5 秒

        for v, coor_name in tqdm.tqdm(enumerate(df)):

            url = f'https://www.google.com.tw/maps/dir/{coor_name}/data=!3m1!4b1!4m2!4m1!3e{self.vehicle_type}'
            
            browser, result = self.route_crawler(browser, url)

            # 將每筆資料同步輸出
            if len(result) != 0:
                self.output_data(result)

        # 關閉瀏覽器
        browser.close()
        
        with open(self.error_path, 'w', encoding='utf-8') as f:
            f.writelines(self.error_ls)
            
        print(f'There are {len(self.error_ls)} times error in the process')
        print('Complete all tasks!')

if __name__ == "__main__":

    googlecrawler = crawler(
        input_data='data/route_bicycle_time/distance_table_half.csv', 
        output_path='data/route_bicycle_time'
        )
    googlecrawler.run()
