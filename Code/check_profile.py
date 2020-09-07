import json
from selenium import webdriver
import Code.Utilities as Util
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import random as r

with open('/Users/johannes/Dropbox/thesis_code/googlebot/Data/diverse/profile.json') as profiles_in:
    profiles = json.load(profiles_in)
with open('/Users/johannes/Dropbox/thesis_code/googlebot/Data/diverse/agents.json') as fl:
    valid_agents = json.load(fl)

for agent in profiles[500:]:
    options = webdriver.FirefoxOptions()
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", agent)
    options.profile = profile
    driver = webdriver.Firefox(options=options)
    driver.get('https://www.google.com')
    term = r.choice(['USA', 'France', 'Greeece', 'Thailand', 'Germany', 'Denmark', 'Italy', 'EU', 'UN', 'Ghandi', 'swaziland',  'hero', 'covid', 'covid 19', 'new cases',
                     'new york', 'los anngeles', 'Nice', 'Jazz'])
    search_field = driver.find_element_by_name("q")
    search_field.clear()
    time.sleep(d0 := r.uniform(0.5, 1.5))
    Util.natural_typing_in_field(search_field, term)
    time.sleep(d1 := r.uniform(0.15, 0.5))
    search_field.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, 2).until(
            ec.presence_of_element_located((By.CLASS_NAME, 'rc'))
            )
        driver.close()

    except:
        driver.close()
        continue
    time.sleep(r.uniform(3,10))
    valid_agents.append(agent)
    with open('/Users/johannes/Dropbox/thesis_code/googlebot/Data/diverse/agents.json', 'w') as fl:
        json.dump(valid_agents, fl)


