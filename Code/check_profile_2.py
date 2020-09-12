import json
from selenium import webdriver
import Code.Utilities as Util
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import random as r

with open('/Users/johannes/Uni/HSG/googlebot/Data/diverse/agents.json') as profiles_in:
    profiles = json.load(profiles_in)

valid_agents = []

for i, agent in enumerate(profiles[0:100]):
    agent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0"
    options = webdriver.FirefoxOptions()
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", agent)
    options.profile = profile
    driver = webdriver.Firefox(options=options)
    driver.get('https://www.google.com/search?client=firefox-b-d&q=trump')
    a = input('valid?')
    if a == 'y':
        valid_agents.append(agent)
        driver.quit()
    elif a == 'n':
        driver.quit()
        continue
    else:
        print(i)
        break

    with open('/Users/johannes/Uni/HSG/googlebot/Data/diverse/agents_3.0.json', 'w') as fl:
        json.dump(valid_agents, fl)


