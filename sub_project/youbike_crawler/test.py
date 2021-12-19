# encoding: utf-8
"""
@ author: yen-nan ho
@ contact: aaron1aaron2@gmail.com
@ date: 2021.05.14
"""

import os
import json
import time
import shutil
import unittest
from crawler import *

class Testcrawler(unittest.TestCase):
    def _set_up(self):
        self.args = get_args()
        self.args.is_test = True
        self.args.output_folder = 'output/test'

        shutil.rmtree(self.args.output_folder, ignore_errors=True)

    def _read_json(self, path):
        try:
            f = open(path, mode='r', encoding='utf-8')
            data = json.load(f)
            f.close()
            if len(data) == 0:
                return False
            return True

        except:
            return False

    def test_get_data(self):
        self._set_up()
        args = self.args
        args.run_time = 1
        args.work_freq_in_min = 1
        crawler_agent = agent(args)
        file_path = crawler_agent.get_data()

        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(self._read_json(file_path))

    def test_run_regular(self):
        self._set_up()
        args = self.args
        args.run_time = 2
        args.work_freq_in_min = 1
        crawler_agent = agent(args)
        result = crawler_agent.run_regular()
        self.assertEqual(result, 'finish - run_time')

        args = self.args
        args.stop_date = '2021.05.13'
        args.work_freq_in_min = 1
        crawler_agent = agent(args)
        result = crawler_agent.run_regular()
        self.assertEqual(result, 'finish - stop_date')

suite = unittest.TestLoader().loadTestsFromTestCase(Testcrawler)
runner = unittest.TextTestRunner(verbosity=2)
test_results = runner.run(suite)