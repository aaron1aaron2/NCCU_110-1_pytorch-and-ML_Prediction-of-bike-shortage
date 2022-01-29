# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  2021.12.20
Last update: 2022.1.24
"""
import re
import os
import csv
import time
import tqdm
import random
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

class crawler:
    def __init__(self, input_data, output_path, vehicle_type='car', rest_freq=50):
        self.input_path = input_data # 原始檔的檔案名稱
        self.output_path = output_path

        # 可使用的交通工具
        self.vehicle_type_dt = {'car':'0', 'bike':'1', 'walk':'2', 'bus':'3'}
        self.vehicle_type = self.vehicle_type_dt[vehicle_type]

        self.error_path = os.path.join(os.path.dirname(output_path), 'error_url.txt')
        self.error_ls = []

        self.rest_freq = rest_freq
        self.rest_sec_range = [10, 80]

        self.max_retry_time = 10 # 最大失敗次數
        self.reboot_driver_time = 2 # 每失敗 n 次重新動 chrome driver

    # 刪除起訖點為同一點的資料
    def _load_data(self, data):
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
            # exit()
            return None
        else:
            print('leftover->{}'.format(leftover_num))

        return df['route'].values

    def _launch_chrome(self):
        chrome_options = Options() #webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # 無視窗
        chrome_options.add_argument("--incognito") # 無痕
        chrome_options.add_argument('--disable-gpu')
        ua = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0"
        chrome_options.add_argument("user-agent={}".format(ua))

        try:
            browser = webdriver.Chrome(executable_path=self.chromedriver, options=chrome_options)
        except:
            browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        browser.get('http://checkip.amazonaws.com/')
        soup = BeautifulSoup(browser.page_source, "html.parser")
        ip = soup.text.strip()

        print(f'current ip: {ip}')

        browser.implicitly_wait(5) # 靜態等待 5 秒

        return browser

    # Google map爬蟲
    def _route_crawler_step(self, browser, url):
        minute = []
        count = 0

        while not minute:
            time.sleep(1)
            count += 1

            # 重製 chrome driver
            if count%self.reboot_driver_time == 0:
                browser.close()
                browser = self._launch_chrome()
                print(f'[Error] Restart chrome driver')

            # 無法成功獲取的 url
            if count%self.max_retry_time == 0:
                print(f'[Error] {url} not available')
                self.error_ls.append(url)
                break
            
            # 爬蟲擷取區塊 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            try:
                browser.get(url) #最後一碼為0汽車、2走路

                _ = browser.find_element(By.XPATH, f'//*[@id="section-directions-trip-travel-mode-0"]')
                # _ = browser.find_element_by_xpath('//*[@id="section-directions-trip-travel-mode-0"]') #等到找到這個在往下

                soup = BeautifulSoup(browser.page_source, "html.parser")

                # 路徑
                routes = soup.find_all("h1", id = re.compile(".+directions-trip.+"))

                routes = [[i.text, i.parent.parent.text.strip()] for i in routes]

                # 時間
                if self.vehicle_type == '0':
                    # car
                    routes_set = [([(rt, text, s.strip())
                                    for s in text.split('  ') if (len(s)>5)]) 
                                        for rt,text in routes]
                    minute = [
                        [rt, sub_txt, 'distance', re.search('\d+\.?\d? \w+', sub_txt)[0], text] if (sub_txt.find('公里') !=-1 | sub_txt.find('公尺')) else (
                        [rt, sub_txt, 'trip duration', re.search('\d+ \w+', sub_txt)[0], text] if (sub_txt.find('預估行車時間') != -1) else (
                        [rt, sub_txt, 'trip duration(Smooth)', re.search('\d+ \w+', sub_txt)[0], text] if (sub_txt.find('交通順暢') != -1) else
                        [rt, sub_txt, 'unknow', '', text]
                                    )) for route in  routes_set for rt, text, sub_txt in route if sub_txt.find('途經')==-1]
                
                elif self.vehicle_type == '1':
                    # bike
                    dt_extract = lambda text: re.search('\d+\.?\d? (公里|公尺)', text)
                    time_extract = lambda text: re.search('(\d+ 小時 )?\d+ 分', text)

                    minute = [
                        [rt, 'distance', dt_extract(text)[0], text] if ((i == 0) & (dt_extract(text) != None)) else (
                        [rt, 'trip duration', time_extract(text)[0], text] if (time_extract(text) != None) else (
                        )) for rt, text in routes for i in range(2)
                    ]

                else:
                    minute = routes

                # 整理輸出
                minute = [i+[url] for i in minute]

            except Exception as inst:
                print(type(inst))    # the exception instance
                print(inst.args)     # arguments stored in .args
                print(inst)   
            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        return browser, minute

    def _output_data(self, result, name):
        csvfile = open(self.output_path, 'a', newline='', encoding='utf-8')
        writer = csv.writer(csvfile)
        for i in result:
            combine = [name] + i
            writer.writerow(combine)

        csvfile.close()

    @staticmethod
    def _rest_countdown(wait_sec):
        print('\nresting...')
        while wait_sec:
            mins, secs = divmod(wait_sec, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print(timer, end="\r")
            time.sleep(1)
            wait_sec -= 1
        print('rebooting...')

    def run(self):
        # 讀取資料
        routes_ls = self._load_data(self.input_path)

        if routes_ls:
            browser = self._launch_chrome()

            ct = 1
            for coor_name in tqdm.tqdm(routes_ls):
                time.sleep(0.5)

                url = f'https://www.google.com.tw/maps/dir/{coor_name}/data=!3m1!4b1!4m2!4m1!3e{self.vehicle_type}'
                
                browser, result = self._route_crawler_step(browser, url)
                
                # 將每筆資料同步輸出
                if len(result) != 0:
                    self._output_data(result, coor_name)

                if (ct % self.rest_freq) == 0:
                    start, end = self.rest_sec_range
                    self._rest_countdown(random.randrange(start, end))

                ct+=1

            # 關閉瀏覽器
            browser.close()
            
            with open(self.error_path, 'w', encoding='utf-8') as f:
                f.writelines(self.error_ls)
                
            print(f'There are {len(self.error_ls)} times error in the process')
            
        print('Complete all tasks!')

if __name__ == "__main__":

    # googlecrawler = crawler(
    #     input_data='data/route_bicycle_time/distance_table_half.csv', 
    #     output_path='data/route_bicycle_time/crawler_back.csv'
    #     )
    # googlecrawler.run()

    googlecrawler = crawler(
        input_data='data/route_bicycle_time/distance_table_half.csv', 
        output_path='data/route_bicycle_time/crawler_back.csv',
        vehicle_type='bike'
        )
    googlecrawler.run()
