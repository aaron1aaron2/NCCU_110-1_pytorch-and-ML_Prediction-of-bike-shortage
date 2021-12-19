# encoding: utf-8
"""
@ author: yen-nan ho
@ contact: aaron1aaron2@gmail.com
@ date: 2021.05.13
"""

import os
import re
import time
import json
import requests
import datetime
import argparse

requests.packages.urllib3.disable_warnings() # 忽略 requests https 時 urllib3 跳出的警告 


def get_args():
    parser = argparse.ArgumentParser('Youbike crawler:')

    parser.add_argument('--output_folder', default = 'output',
                        help = "輸出位置")
    parser.add_argument('--sublevel_in_folder', default = 'day', 
                        help = "輸出時以年、月、日作為資料夾子層級的資料夾。 ['day', 'month', '']")

    parser.add_argument('--work_freq_in_min', type=float, default = 30,
                        help = "多少分鐘執行一次")
    parser.add_argument('--work_freq_in_day', default = '10:20',
                        help = "每天幾點執行一次")

    parser.add_argument('--work_freq_unit', default = 'min',
                        help = "定時爬取時間單位。 ['min', 'day']")

    parser.add_argument('--stop_date', default = '',
                        help = "停止爬取的日期，空值代表不設定停止時間。")
    parser.add_argument('--run_time', type=int, default = -1,
                        help = "執行次數上限")
    parser.add_argument('--retry_time', type=int, default = 3,
                        help = "當有問題時重新測試的次數")

    parser.add_argument('--is_test', type=str2bool, default = False,
                        help = "當有問題時重新測試的次數")


    args = parser.parse_args()

    return args

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

class agent:
    def __init__(self, args):
        # output 
        self.output_folder = args.output_folder
        self.sublevel_in_folder = args.sublevel_in_folder

        # regular
        self.work_freq_in_min = args.work_freq_in_min
        self.work_freq_in_day = args.work_freq_in_day
        self.work_freq_unit = args.work_freq_unit
        self.stop_date = args.stop_date
        self.run_time = args.run_time

        # other
        self.retry_time = args.retry_time
        self.is_test = args.is_test

        self._check_args()

        print('='*50 + '\n[args]\n' + str(args)[10 : -1] + '\n' + '='*50)


    def _check_args(self):
        os.makedirs(self.output_folder, exist_ok=True)
        print(f"data is output at {self.output_folder}")

        assert self.sublevel_in_folder in ['day', 'month', ''], "Supported parameters in '--sublevel_in_folder': ['day', 'month', '']"
        assert self.work_freq_unit in ['min', 'day'], "Supported parameters in '--work_freq_unit': ['min', 'day']"

        if self.work_freq_unit == 'day':
            print(f'Crawl every day at {self.work_freq_in_day}')
            assert re.match(r"\d\d:\d\d", self.work_freq_in_day) != None, "The format of '--work_freq_in_day' must be '10:30'(24-hour time system)"

        if self.work_freq_unit == 'min':
            print(f'Crawl every {self.work_freq_in_min} minutes')
            assert self.work_freq_in_min >= 1, "--work_freq_in_min must be greater than 1"
        
        if self.stop_date != '':
            assert re.match(r"\d\d\d\d\.\d\d\.\d\d", self.stop_date) != None, "The format of '--stop_date' must be '2021.5.20'"
            print(f'stop at {self.stop_date}')
            self.stop_date = datetime.datetime.strptime(self.stop_date, '%Y.%m.%d')


    def get_data(self):
        date, current_time  = datetime.datetime.now().strftime("%Y.%m.%d %H%M%S").split(' ')

        if self.sublevel_in_folder == 'day':
            output_folder = os.path.join(self.output_folder, date)
        elif self.sublevel_in_folder == 'month':
            output_folder = self.output_folder
        else:
            output_folder = self.output_folder

        os.makedirs(output_folder, exist_ok=True)

        output_file = os.path.join(output_folder, f'{date}_{current_time}.json')

        try_time = 0
        while True:
            try:
                r = requests.get("https://tcgbusfs.blob.core.windows.net/blobyoubike/YouBikeTP.json", verify=False)
                respond_dt = r.json()

                with open(output_file, mode='w', encoding='utf-8') as f:
                    json.dump(respond_dt['retVal'], f, ensure_ascii=False, indent=1)

                print(f'[success] file is save at {output_file}')
                break

            except:
                print(f'error(try {try_time} times)')
                try_time+=1
                time.sleep(1)

            if try_time > self.retry_time:
                print(f'pass at {date} - {current_time}')
                break

        if self.is_test:
        	return output_file
        # pd.DataFrame(respond_dt['retVal']).T


    def run_regular_s(self):
        '''schedule 版本的，但是每分鐘的模式時間會慢慢延遲，這邊留著每天固定時間。'''
        import schedule

        # if self.work_freq_unit == 'min':
        #     schedule.every(self.work_freq_in_min).minutes.do(self.get_data)

        if self.work_freq_unit == 'day':
            schedule.every().day.at(self.work_freq_in_day).do(self.get_data)

        runtime = 0
        while True:
            schedule.run_pending()
            runtime += 1
            time.sleep(1)

            if self.stop_date != '':
                if datetime.datetime.now() > self.stop_date:
                    print('finish!')
                    if self.is_test: return 'finish - stop_date'
                    break

            if self.run_time != -1:
                if runtime > self.run_time:
                    print('finish!')
                    if self.is_test: return 'finish - run_time'
                    break

    def run_regular(self):
        runtime = 0
        last_run = 0
        while True:
            current_min = datetime.datetime.now().minute

            if (current_min!=last_run) & ((current_min % self.work_freq_in_min) == 0):
                self.get_data()
                runtime += 1
                last_run = current_min

            if self.stop_date != '':
                if datetime.datetime.now() > self.stop_date:
                    print('finish!')
                    if self.is_test: return 'finish - stop_date'
                    break

            if self.run_time != -1:
                if runtime > self.run_time:
                    print('finish!')
                    if self.is_test: return 'finish - run_time'
                    break

            time.sleep(1)

    def run(self):
        if self.work_freq_unit == 'min':
            self.run_regular()

        if self.work_freq_unit == 'day':
            self.run_regular_s()

def main():
    args = get_args()

    crawler_agent = agent(args)
    crawler_agent.run()




if __name__ == '__main__':
    main()