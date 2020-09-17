import time
import pandas as pd
import os
import random as r
from Code import Utilities as Util, BotInterface as BI
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import exceptions
from datetime import datetime
import re
import shutil


class SingleBot:
    IP = 'localhost'
    COL_NAMES = ('title',
                 'search_term',
                 'rank',
                 'domain',
                 'text',
                 'flag',
                 'bot_ID',
                 'time')
    COL_NAMES_SEARCHES = ('term',
                          'source',
                          'time',
                          'type',
                          'selected',
                          'bot_ID')

    def __init__(self,
                 port,
                 flag,
                 bot_id,
                 swarm_name,
                 path_results,
                 path_searches,
                 user_agent,
                 profile_dir,
                 nr_results=1,
                 visual=False,
                 existing=False,
                 proxy=None,
                 accept_cookie=False,
                 ):
        """
        :param port: string, access selenium docker image
        :param flag: string, flag indicates political orientation/nature of the bot
        :param bot_id: string, 'ns2ame' of the single bot, consists of the swarm name
         and instance number
        :param dir_results: string, directory where the single bot stores its results
            defaults to Data/results/
        :param nr_results: int, nr. of results to store when conducting
            experimental searchƒ
        :param visual: boolean, when True docker is not used, instead
            searches are conducted in a visible firefox instance.
            defaults to False
        :param existing: boolean, when True cookie and results are
            not overwritten on initialization.
        """
        self.port = port
        self.flag = flag
        self.bot_id = bot_id
        self._swarm_name = swarm_name
        self.path_results = path_results
        self.path_searches = path_searches
        self.nr_results = nr_results
        self.visual = visual
        self._proxy = proxy
        # initialize empty results Dataframe with desired columns
        self.existing_results = pd.DataFrame(columns=SingleBot.COL_NAMES)
        self.existing_searches = pd.DataFrame(
            columns=SingleBot.COL_NAMES_SEARCHES)
        # initialize empty driver options
        self.driver_options = webdriver.FirefoxOptions()
        # initialize empty driver
        self.driver = None
        self.interface = None
        # initialize path to bot specific cookie jar from jar directorys

        # set desired capabilitiies
        self._profile_dir = profile_dir
        self._profile_path = None
        self._firefox_capabilities = DesiredCapabilities.FIREFOX.copy()

        self._firefox_profile = webdriver.FirefoxProfile()
        self._firefox_options = None
        if self._proxy is not None:
            self._firefox_capabilities['proxy'] = {
                "proxyType": "MANUAL",
                "httpProxy": self._proxy,
                "ftpProxy": self._proxy,
                "sslProxy": self._proxy,
                "noProxy": ["this-page-intentionally-left-blank.org"]
            }

        # initialize path to bot specific results file from results directory
        self._IP = SingleBot.IP
        # If old cookies and results are not to be reused, run create.
        if not existing:
            if os.path.isdir(f'{self._profile_dir["Host"]}/{self.bot_id}'):
                shutil.rmtree(f'{self._profile_dir["Host"]}/{self.bot_id}')
            self._firefox_options = webdriver.FirefoxOptions()
            self._firefox_options.set_preference("moz:webdriverClick", 'true')

            self._firefox_options.set_preference("media.autoplay.default", 1)
            self._firefox_options.set_preference("media.autoplay.allow-muted",
                                                 'false')
            profile = webdriver.FirefoxProfile()
            profile.set_preference("general.useragent.override", user_agent)
            self._firefox_options.profile = profile
            self.create(accept_cookie)
        else:
            self._profile_path = f'{self._profile_dir["Selenium"]}/{self.bot_id}'

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

    @property
    def path_searches(self):
        return self._path_searches

    @path_searches.setter
    def path_searches(self, path):
        self._path_searches = path
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

    def store_search(self, term_params, selected):
        if term_params['type'] == 'political':
            source = term_params['choice_param']
        else:
            source = None
        search_store = {'term': term_params.get('term'),
                        'source': source,
                        'time': datetime.now(),
                        'type': term_params.get('type'),
                        'selected': selected,
                        'bot_ID': self.bot_id}
        self.existing_searches = self.existing_searches.append(search_store,
                                                               ignore_index=True)
        self.existing_searches.to_csv(self.path_searches, mode='a',
                                      header=False,
                                      index=False)
        self.existing_searches = None
        self.existing_searches = pd.DataFrame(
            columns=SingleBot.COL_NAMES_SEARCHES)

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
            self.driver = webdriver.Firefox(
                desired_capabilities=self._firefox_capabilities,
                options=self._firefox_options
            )
        else:
            self.driver = webdriver.Remote(
                f'http://{self._IP}:{self.port}/wd/hub',
                desired_capabilities=self._firefox_capabilities,
                options=self._firefox_options
            )
            self.driver.maximize_window()

        self.driver.implicitly_wait(30)
        Util.connection_handler(self.driver, "https://www.google.com/")
        time.sleep(3)
        if accept_cookie:
            self.interface = BI.BotInterface(self.driver)
            self.interface.set_cursor_loc()
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
        issue = None
        self._firefox_profile = webdriver.FirefoxProfile()
        self._firefox_options = webdriver.FirefoxOptions()
        self._firefox_profile.profile_dir = self._profile_path
        self._firefox_options.profile = self._firefox_profile
        if self.visual:
            self.driver = webdriver.Firefox(
                desired_capabilities=self._firefox_capabilities,
                options=self._firefox_options
            )
        else:
            try:
                self.driver = webdriver.Remote(
                    f'http://{self._IP}:{self.port}/wd/hub',
                    desired_capabilities=self._firefox_capabilities,
                    options=self._firefox_options)
            except:
                issue = 'failed_launch'
        time.sleep(5)

        try:
            self.interface = BI.BotInterface(self.driver)
        except:
            issue = 'failed_interface_connection'
        self.interface.set_cursor_loc()
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
            if len(result.text) > 1:
                if Util.result_domain_match(result.text, target_domain) is None:
                    print(f'{self.bot_id} loaded at bottom issue')
                    self.driver.get_screenshot_as_file(
                        f'Data/log_files/swarms/img{self.bot_id}.png')
                    break
                elif Util.result_domain_match(result.text, target_domain):
                    return result
        return None

    def match_rank(self, target_rank, rank=1, class_name='rc'):
        """
        :param rank: int rank across pages of first result on current page
        :param target_rank: int, rank of desired choices
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
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((By.XPATH, '//*[@id="pnnext"]'))
            )
        except:
            return False
        self.interface.scroll_to_bottom()
        next_button = self.driver.find_element_by_xpath('//*[@id="pnnext"]')
        where = next_button.rect
        where['y'] -= self.interface.y_scroll_loc
        x_dev = random.randint(1, max(int(where['width'] - 1), 1))
        y_dev = random.randint(1, max(int(where['height'] - 1), 1))
        x_loc = int(where['x']) + x_dev
        y_loc = int(where['y']) + y_dev
        self.interface.mouse_to(x_loc, y_loc)
        self.interface.safe_click(next_button, x_dev, y_dev)
        time.sleep(3)
        try:
            WebDriverWait(self.driver, 180).until(
                ec.presence_of_element_located((By.CLASS_NAME, 'rc'))
            )
        except:
            return False
        y = self.interface.reset_scroll_loc()
        self.interface.scroll_to_top(fast=True)
        return True

    def select_result(self, term_params):

        time.sleep(random.uniform(1, 3))
        try:
            e = self.driver.find_elements_by_class_name('WE0UJf')[0]
            nr_available = int(re.search('\\b[0-9]+', e.text).group(0))
        except:
            nr_available = 100
        max_pages = 3
        page = 1
        rank = 1
        result = None
        term, choice_type, choice_param, kind = term_params.values()
        while page <= max_pages and (result is None):

            if choice_type == 'domain':
                self.interface.scroll_to_bottom(slow=True)
            if choice_type == 'domain':
                result = self.match_domain(choice_param)
            elif choice_type == 'rank':
                result, rank = self.match_rank(choice_param, rank)
            if result is None and page < max_pages and nr_available > (max_pages-1)*8:
                self.next_page()
                page += 1
            else:
                break
        if result is not None:
            try:
                button = result.find_element_by_class_name('LC20lb.DKV0Md')
            except:
                try:
                    self.interface.scroll_to_bottom()
                    button = result.find_element_by_class_name('LC20lb.DKV0Md')
                except:
                    print('values dont exist')
                    img = self.driver.get_screenshot_as_file(
                        f'Data/log_files/swarms/img{self.bot_id}.png')
                    print(self.bot_id)

                    return 'failure'
            where = button.rect
            if choice_type == 'domain':
                self.interface.scroll_to_top(fast=True)
            if where[
                'y'] > self.interface.height - 100 - self.interface.y_scroll_loc:
                goal = where['y'] - random.randint(self.interface.height // 3,
                                                   2 * self.interface.height // 3)
                self.interface.scroll(goal + self.interface.y_scroll_loc)
                where['y'] -= self.interface.y_scroll_loc

            x_dev = random.randint(1, (int(where['width'] - 1) // 2))
            x_loc = int(where['x']) + x_dev
            y_dev = random.randint(1, int(where['height'] - 1))
            y_loc = int(where['y']) + y_dev

            self.interface.mouse_to(x_loc, y_loc)
            self.interface.safe_click(button, x_dev, y_dev)
            self.interface.y_scroll_loc = self.driver.execute_script(
                'return window.pageYOffset;')
            time.sleep(10)
            try:
                self.interface.scroll_to_bottom(slow=True, limit=3500)
            except:
                print(self.bot_id)
                print('failure on scroll to bottom')
                img = self.driver.get_screenshot_as_file(
                    f'Data/log_files/swarms/img{self.bot_id}.png')
                print(term_params)
                print(self.driver.current_url)
                return 'failure'
            return 'success'
        else:
            return 'failure'

    def shutdown(self):

        """
        If current domain is google store cookies from driver in cookie jar and 'close' driver
        """
        window = self.driver.current_window_handle
        self.driver.execute_script("window.open()")
        self.driver.switch_to.window(window)
        self.driver.close()
        time.sleep(10)
        path = self.driver.capabilities['moz:profile']
        self._firefox_options = None
        self._firefox_profile = None

        if not self.visual:
            if os.path.isfile(
                    f'{self._profile_dir["Host"]}/{self.bot_id}/cookies.sqlite'):
                os.system(
                    f'docker exec container_{self._swarm_name} rm -r {self._profile_dir["Selenium"]}/{self.bot_id}')

            os.system(
                f'docker exec container_{self._swarm_name} cp --remove-destination -a {path} {self._profile_dir["Selenium"]}/{self.bot_id}')

            self.driver.quit()
            if os.path.lexists(
                    lock := f'{self._profile_dir["Host"]}/{self.bot_id}/lock'):
                os.unlink(lock)
                os.unlink(
                    f'{self._profile_dir["Host"]}/{self.bot_id}/.parentlock')
            self._profile_path = f'{self._profile_dir["Host"]}/{self.bot_id}'

        else:
            if not os.path.isdir(f'{self._profile_dir["Host"]}/{self.bot_id}'):
                shutil.copytree(path,
                                f'{self._profile_dir["Host"]}/{self.bot_id}')
                time.sleep(2)
                self.driver.quit()
            else:
                shutil.copytree(path,
                                f'{self._profile_dir["Host"]}/interim_{self.bot_id}')
                time.sleep(2)
                self.driver.quit()
                if os.path.isdir(f'{self._profile_dir["Host"]}/{self.bot_id}'):
                    shutil.rmtree(f'{self._profile_dir["Host"]}/{self.bot_id}')
                shutil.copytree(
                    f'{self._profile_dir["Host"]}/interim_{self.bot_id}',
                    f'{self._profile_dir["Host"]}/{self.bot_id}')
                shutil.rmtree(
                    f'{self._profile_dir["Host"]}/interim_{self.bot_id}')

            self._profile_path = f'{self._profile_dir["Host"]}/{self.bot_id}'

        return self._profile_path

    def download_results(self, term, class_name='rc'):
        """
        :param class_name: class name for text field to be stored
        :param term: string, a phrase or word  that has  been searched
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
                                'bot_id': self.bot_id,
                                'time': datetime.now()}
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

    def search(self, term_params, store=False, save_search=True):
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
        if issue := Util.connection_handler(self.driver,
                                            "https://www.google.com/") is None:
            try:
                search_field = self.driver.find_element_by_name("q")
            except exceptions.NoSuchElementException:
                self.driver.refresh()
            try:
                search_field = self.driver.find_element_by_name("q")
            except exceptions.NoSuchElementException:
                issue = 'No search bar?!'
                print(issue)
                print(self.bot_id)
                img = self.driver.get_screenshot_as_file(
                    f'Data/log_files/swarms/img{self.bot_id}.png')
                return issue

            search_field.clear()
            time.sleep(d0 := r.uniform(0.5, 1.5))
            Util.natural_typing_in_field(search_field, term_params['term'],
                                         keep_errors=not store)
            time.sleep(d1 := r.uniform(0.15, 0.5))
            search_field.send_keys(Keys.RETURN)

            # checks if results will load

            issue, nr_results = Util.click_search(self.driver, self.interface)
            if nr_results == -1:
                issue, nr_results = Util.click_search(self.driver, self.interface)
            if nr_results == -1:
                issue, nr_results = Util.click_search(self.driver, self.interface)
            if nr_results == -1:
                e_present = self.driver.find_elements_by_class_name('rc')
                if len(e_present)>0:
                    nr_results=1
                try:
                    self.interface.scroll_to_top(fast=True)
                except:
                    issue = 'theres something here, but its very broken'
            if issue is not None:
                    print(f'{self.bot_id} encountered {issue}')
                    self.driver.get_screenshot_as_file(
                        f'Data/log_files/swarms/img{self.bot_id}.png')
                    return issue+'/search'
            elif nr_results == -1:
                print(f'{self.bot_id} encountered -1 results')
                self.driver.get_screenshot_as_file(
                    f'Data/log_files/swarms/img{self.bot_id}.png')
                return issue+'/search'
            self.interface.scroll_to_top(fast=True)
            # let more results load and download if needed
            time.sleep(d2 := r.uniform(1.5, 2.5))
            if store:
                time.sleep(d2 := r.uniform(1.5, 2.5))
                self.download_results(term_params['term'])
            if nr_results == 0:
                selected = 'No Results'
            elif term_params['choice_type'] != 'none':
                time.sleep(d2 := r.uniform(1.5, 2.5))
                selected = self.select_result(term_params)
            else:
                selected = 'None'
            time.sleep(random.uniform(5, 10))
            if save_search:
                self.store_search(term_params, selected)
            return None
        else:
            return issue + '/search'
