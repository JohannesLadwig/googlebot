import time
import pandas as pd
import os
import random as r
from Code import Utilities as Util, BotInterface as BI
import json
import random
from selenium import webdriver
# import seleniumwire
import selenium.common.exceptions as sel_exc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


class SingleBot:
    IP = '192.168.1.19'
    COL_NAMES = ('term_params',
                 'rank',
                 'domain',
                 'title',
                 'text',
                 'flag',
                 'bot_ID')

    def __init__(self,
                 port,
                 flag,
                 bot_id,
                 dir_cookie_jar='Data/cookies/',
                 dir_results='Data/results/',
                 nr_results=1,
                 visual=False,
                 existing=False,
                 proxy=None,
                 accept_cookie=False
                 ):
        """
        :param port: string, access selenium docker image
        :param flag: string, flag indicates political orientation/nature of the bot
        :param bot_id: string, 'name' of the single bot, consists of the swarm name
         and instance number
        :param dir_cookie_jar: string, directory where single bot is to create or access a cookie jar
            defaults to Data/cookies/
        :param dir_results: string, directory where the single bot stores its results
            defaults to Data/results/
        :param nr_results: int, nr. of results to store when conducting
            experimental search
        :param visual: boolean, when True docker is not used, instead
            searches are conducted in a visible firefox instance.
            defaults to False
        :param existing: boolean, when True cookie and results are
            not overwritten on initialization.
        """
        self.port = port
        self.flag = flag
        self.bot_id = bot_id
        self.dir_cookie_jar = dir_cookie_jar
        self.dir_results = dir_results
        self.nr_results = nr_results
        self.visual = visual
        self._proxy = proxy
        # initialize empty results Dataframe with desired columns
        self.existing_results = pd.DataFrame(columns=SingleBot.COL_NAMES)
        # initialize empty driver options
        self.driver_options = None
        # initialize empty driver
        self.driver = None
        self.interface = None
        # initialize path to bot specific cookie jar from jar directory
        self.cookie_jar = self.dir_cookie_jar + self.bot_id + '.json'

        # set desired capabilitiies
        print(self._proxy)
        self._firefox_capabilities = DesiredCapabilities.FIREFOX
        if self._proxy is not None:
            self._firefox_capabilities['proxy'] = {
                "proxyType": "MANUAL",
                "httpProxy": self._proxy,
                "ftpProxy": self._proxy,
                "sslProxy": self._proxy,
                }


        # initialize path to bot specific results file from results directory
        self.path_results = self.dir_results + self.bot_id + '.csv'
        self._IP = SingleBot.IP
        # If old cookies and results are not to be reused, run create.
        if not existing:
            self.create(accept_cookie)

    def __str__(self):
        return f'BotID: {self.bot_id}, {self.flag}'

    """    
    port getter and setter
    """

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, new_port):
        self._port = new_port

    """    
    flag getter and setter
    """

    @property
    def flag(self):
        return self._flag

    @flag.setter
    def flag(self, new_flag):
        self._flag = new_flag

    """
    cookie jar getter and setter, raises value error if non valid  directory
    is attempted to be set
    """

    @property
    def dir_cookie_jar(self):
        return self._dir_cookie_jar

    @dir_cookie_jar.setter
    def dir_cookie_jar(self, path):
        if os.path.isdir(path):
            self._dir_cookie_jar = path
        else:
            raise ValueError(f'{path} is not a valid directory')

    """
    results directory getter and setter, raises value error if non valid directory
    is set
    """

    @property
    def dir_results(self):
        return self._dir_results

    @dir_results.setter
    def dir_results(self, path):
        if os.path.isdir(path):
            self._dir_results = path
        else:
            raise ValueError(f'{path} is not a valid directory')

    """
    cookie_jar directory getter and setter, raises value error if non valid directory
    is set
    """

    @property
    def cookie_jar(self):
        return self._cookie_jar

    @cookie_jar.setter
    def cookie_jar(self, path):
        self._cookie_jar = path
        if not os.path.exists(path):
            with open(path, 'w') as create:
                pass

    """results path getter and setter, creates file if none exists in location 
    of passed path. (allways use with known good directories)
    """

    @property
    def path_results(self):
        return self._path_results

    @path_results.setter
    def path_results(self, path):
        self._path_results = path
        if not os.path.exists(path):
            with open(path, 'w') as create:
                pass

    """
    Setter and getter for nr_results. If nr_results == 0, sets store_results to
    false.
    """

    @property
    def nr_results(self):
        return self._nr_results

    @nr_results.setter
    def nr_results(self, number):
        if number >= 0:
            self._nr_results = int(number)
        # elif number == 0:
        #     self._nr_results = 1
        else:
            raise ValueError(f'{number} should be an integer > 0')

    @property
    def driver(self):
        return self._driver

    @driver.setter
    def driver(self, driver):
        self._driver = driver

    @property
    def interface(self):
        return self._interface

    @interface.setter
    def interface(self, interface):
        self._interface = interface

    def connection_handler(self, url, wait=30, max_tries=5):
        """
        :param url: str, url to some website
        :param wait: int, nr. of seconds to wait between retries
        :param max_tries: int, nr. of times to retry querrying website
        :return: boolean, True  if website succesfully loaded, false else

        Note: only waits in case of timeour or  webdriver exception. Other
            Errors in page loading are not handled, and must be adressed should
            they occour.
        """
        retries = 0
        issue = None
        while retries < max_tries:

            try:
                self.driver.get(url)
                return issue
            except sel_exc.TimeoutException:
                retries += 1
                if retries < max_tries - 1:
                    time.sleep(wait)
                else:
                    issue = 'timeout'
            except sel_exc.WebDriverException:
                retries += 1
                if retries < max_tries - 1:
                    time.sleep(wait)
                else: issue = 'webdriver'
            retries += 1
        return issue

    def accept_cookies(self):
        """
        :return: void
        accepts cookie preferences on Google
        """
        button_path = '/html/body/div/div[3]/div[1]/div/div/div/div/div[2]/div/div/div[2]/div[2]/div/div/g-raised-button/div'
        WebDriverWait(self.driver, 180).until(
                ec.element_to_be_clickable((By.XPATH, button_path))
            )
        self.interface.move_and_click(button_path)
        down_button_path = '/html/body/div/c-wiz/div[2]/div/div/div/div/div[4]/div/div/span/img'
        self.interface.partial_mouse(
            int(self.interface.width) // 2 + random.randint(-50, 0),
            int(self.interface.height) // 2 + random.randint(-20, 20))
        self.driver.switch_to.frame(0)
        self.interface.move_and_click(down_button_path)
        time.sleep(0.3)
        for i in range(2):
            self.interface.click()
            time.sleep(0.5)
        accept_button_path = '/html/body/div/c-wiz/div[2]/div/div/div/div/div[5]/div/form/div/span'
        self.interface.move_and_click(accept_button_path)

    def create(self, accept_cookie):
        """
            set and launch blank driver and access google.
            Accepts cookie preferences.
            Does not load existing cookies! only use when cookies
             are to be re-set
        """

        if self.visual:
            self.driver = webdriver.Firefox(desired_capabilities=self._firefox_capabilities)
        else:
            self.driver = webdriver.Remote(
                f'http://{self._IP}:{self.port}/wd/hub',
                desired_capabilities=self._firefox_capabilities,
            )
        self.interface = BI.BotInterface(self.driver)
        self.interface.set_cursor_loc()
        self.driver.get("https://www.google.com/")
        if accept_cookie:
            self.accept_cookies()
        time.sleep(2)
        self.shutdown()

    def launch(self):
        """
        :return: boolean
                    True when connection to "https://www.google.com/webhp?hl=en/grlf" can be
                        established
                    else False
        accesses webdriver, acceses dead google page and loads cookies from jar.
        """
        if self.visual:
            self.driver = webdriver.Firefox(desired_capabilities=self._firefox_capabilities)
        else:
            self.driver = webdriver.Remote(
                f'http://{self._IP}:{self.port}/wd/hub',
                desired_capabilities=self._firefox_capabilities)

        if issue := self.connection_handler("https://www.google.com/grlf") is None:
            time.sleep(2)
            with open(self.cookie_jar, 'r') as jar:
                cookie = json.load(jar)
            time.sleep(1)
            for crumble in cookie:
                self.driver.add_cookie(crumble)
            self.interface = BI.BotInterface(self.driver)
            self.interface.set_cursor_loc()
            return None
        else:
            return issue

    def match_domain(self, target_domain, class_name='rc'):
        """
        :param target_domain:
        :param class_name: class name for text field to be stored
        :return: matched element

        expects driver to have accessed google and searched term_params.
        """
        results_in = self.driver.find_elements_by_class_name(class_name)

        for result in results_in:
            if len(result.text) > 0:
                if Util.result_domain_match(result.text, target_domain):
                    return result

        return None

    def match_rank(self, target_rank, rank=1, class_name='rc'):
        """
        :param rank: int rank across pages of first result on current page
        :param target_rank: int, rank of desired choice
        :param class_name: class name for text field to be stored
        :return: matched element

        expects driver to have accessed google and searched term_params.
        """
        results_in = self.driver.find_elements_by_class_name(class_name)
        for result in results_in:
            if len(result.text) > 0:
                if rank == target_rank:
                    return result, rank
                rank += 1
        return None, rank

    def next_page(self):
        try:
            WebDriverWait(self.driver, 180).until(
                ec.presence_of_element_located((By.XPATH, '//*[@id="pnnext"]'))
            )
        except:
            return False
        self.interface.scroll_to_bottom()
        next_button = self.driver.find_element_by_xpath('//*[@id="pnnext"]')
        where = next_button.rect
        where['y'] -= self.interface.y_scroll_loc
        x_loc = int(where['x']) + random.randint(1, int(where['width'] - 1))
        y_loc = int(where['y']) + random.randint(1, int(where['height'] - 1))
        self.interface.mouse_to(x_loc, y_loc)
        self.interface.click()
        self.interface.y_scroll_loc = 0
        time.sleep(3)
        try:
            WebDriverWait(self.driver, 180).until(
                ec.presence_of_element_located((By.CLASS_NAME, 'rc'))
            )
        except:
            return False

        return True

    def select_result(self, term_params):

        time.sleep(random.randint(1,3))
        max_pages = 3
        page = 1
        rank = 1
        result = None
        term, choice_type, choice_param = term_params.values()
        while page <= max_pages and result is None:
            if choice_type == 'domain':
                result = self.match_domain(choice_param)
            elif choice_type == 'rank':
                result, rank = self.match_rank(choice_param, rank)
            if result is None:
                self.next_page()
                page += 1
        if result is not None:
            button = result.find_element_by_class_name('r')
            where = button.rect
            if where['y'] > self.interface.height - 100 - self.interface.y_scroll_loc:
                goal = where['y'] - random.randint(self.interface.height // 3,
                                                   2 * self.interface.height // 3)
                self.interface.scroll(goal + self.interface.y_scroll_loc)
                where['y'] -= self.interface.y_scroll_loc

            x_loc = int(where['x']) + random.randint(1, (int(where['width'] - 1)//3))
            y_loc = int(where['y']) + random.randint(1, int(where['height'] - 1))
            # store cookies before leaving domain
            cookie = self.driver.get_cookies()
            with open(self.cookie_jar, 'w') as jar:
                json.dump(cookie, jar)

            self.interface.mouse_to(x_loc, y_loc)
            self.interface.click()
            self.interface.y_scroll_loc = 0
            time.sleep(3)
            self.interface.scroll_to_bottom(slow=True, limit=5000)

    def shutdown(self):

        """
        If current domain is google store cookies from driver in cookie jar and 'close' driver
        """
        if Util.extract_domain( self.driver.current_url) == 'google.com':
            cookie = self.driver.get_cookies()
            with open(self.cookie_jar, 'w') as jar:
                json.dump(cookie, jar)
        self.driver.close()

    def download_results(self, term, class_name='rc'):
        """
        :param class_name: class name for text field to be stored
        :param term_params: string, a phrase or word  that has  been searched
        :return:

        expects driver to have accessed google and searched term_params.
        """
        # potentially add error handling here, not sure if this can fail as called
        # find elements by class_name
        results_in = self.driver.find_elements_by_class_name(class_name)

        # iterate elements in results_in, clean these and append to existing results
        rank = 1
        i = 0
        while (rank <= self.nr_results) and i < len(results_in):
            result = results_in[i].text
            if len(result) > 0:
                # Clean and store result
                title, domain, body = Util.clean_result(result)
                result_clean = {'title': title,
                                'search_term': term,
                                'rank': rank,
                                'domain': domain,
                                'text': body,
                                'flag': self.flag,
                                'bot_id': self.bot_id}
                self.existing_results = \
                    self.existing_results.append(result_clean,
                                                 ignore_index=True)
                rank += 1
            i += 1
        self.existing_results.to_csv(self.path_results, mode='a', header=False,
                                     index=False)
        # empty self.existing_results
        self.existing_results = None
        self.existing_results = pd.DataFrame(columns=SingleBot.COL_NAMES)

    """
    execute_searches: conducts google searches according to the bots
        specifications.
    """

    def search(self, term_params, store=False):
        """
        :param term_params: str, phrase or term to google
        :param store: boolean, when True, self.nr_results will be stored
        :return: boolean, True if search executed successfully
        """

        # if results are not stored, search terms are cut short randomly
        # This could be moved to the function calling this, doesnt really make
        # sense here as this function is meant to search, not create search terms.

        if not store:
            words = term_params['term'].split(' ')
            if len(words) > 6:
                nr = random.randint(6, min(len(words) - 1, 12))
                words = words[0:nr]
                term_params['term'] = ' '.join(words)
        # open google, if sucessfull proceed
        if issue := self.connection_handler("https://www.google.com/") is None:
            search_field = self.driver.find_element_by_name("q")
            search_field.clear()
            time.sleep(d0 := r.uniform(0.5, 1.5))
            Util.natural_typing_in_field(search_field, term_params['term'])
            time.sleep(d1 := r.uniform(0.15, 0.5))
            search_field.send_keys(Keys.RETURN)
            # checks if results will load
            try:
                WebDriverWait(self.driver, 180).until(
                    ec.presence_of_element_located((By.CLASS_NAME, 'rc'))
                )
            except:
                issue = 'results_load/search'
                img = self.driver.get_screenshot_as_file(f'Data/log_files/swarms/img{self.bot_id}.png')

                return issue

            # let more results load and download if needed
            time.sleep(d2 := r.uniform(1.5, 2.5))
            if store:
                self.download_results(term_params['term'])
            if term_params['choice_type'] != 'none':
                self.select_result(term_params)
            time.sleep(4.5 - d0 - d1 - d2)
            return None
        else:
            return issue + '/search'
