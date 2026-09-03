# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import login, log
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b, c, p = login(pw)
    log("LOGIN OK final url=", p.url)
    b.close()
