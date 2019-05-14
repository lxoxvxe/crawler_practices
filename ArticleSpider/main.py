# -*- coding: utf-8 -*-

from scrapy.cmdline import execute

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#print(os.path.dirname(os.path.abspath(__file__)))
#os.path.abspath(__file__)不就等于__file__吗？？？
#为何不直接写os.path.dirname(__file__)
#print(os.getcwd())
execute(["scrapy", "crawl", "zhihu"])
#execute(["scrapy", "crawl", "jobbole"])