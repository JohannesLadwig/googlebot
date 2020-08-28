from selenium import webdriver
from datetime import date
import pandas as pd
import os
from Code.Utilities import *
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class SingleScraperSelenium:
    COL_NAMES = (
        'term_params', 'date_scraped', 'source',
        'political_orientation')

    SOURCE_PROPERTIES = {
        'DailyBeast': {'URL': 'https://www.thedailybeast.com/category/politics',
                       'CLASS_KEY': 'TitleText.TitleText--with-gradient.GridStory__title-text',
                       'DOMAIN': 'thedailybeast.com'},
        'CNN': {'URL': 'https://edition.cnn.com/politics',
                'CLASS_KEY': 'cd__headline-text',
                'DOMAIN': 'cnn.com'}
    }

    """
    Constructs a Bot which can search google and store search results.
    
    input:
    path_search_terms - (relative) path to a file containing search terms
                        in csv form.
    nr_searches - integer number indicating the number of searches the bot should
                    conduct from the given list
    store_results - A boolean. If true, the bot will store search results.
    path_results - (relative) path to a csv file in which the bot can store
                    search results. defaults to 'Data/results.csv'.
    nr_results - integer value, indicating the nr. of search results to
                    store.                      
    """

    def __init__(self,
                 source,
                 political_orientation,
                 path_results,
                 ):

        self.source = source
        self.political_orientation = political_orientation
        self.path_results = path_results

        self.driver_options = None
        self.driver = None

        self.existing_results = pd.DataFrame(columns=SingleScraperSelenium.COL_NAMES)

        self.source_url, self.source_class_key, self.source_domain = \
            SingleScraperSelenium.SOURCE_PROPERTIES[self.source].values()
        self.date_scraped = None

    def __str__(self):
        return f'Scrapes: {self.source}, {self.political_orientation}'

    @property
    def political_orientation(self):
        return self._political_orientation

    @political_orientation.setter
    def political_orientation(self, flag):
        self._political_orientation = flag

    @property
    def path_results(self):
        return self._path_results

    @path_results.setter
    def path_results(self, path):
        self._path_results = path
        if not os.path.exists(path):
            with open(path, 'w') as create:
                pass

    # @property
    # def source_url(self):
    #     return self._source_url
    #
    # @source_url.setter
    # def source_url(self, url):
    #     self._source_url = url
    #
    # @property
    # def source_class_key(self):
    #     return self._source_class_key
    #
    # @source_class_key.setter
    # def source_class_key(self, key):
    #     self._source_class_key = key
    """
    launches browser and runs initialize_terms
    """

    def read_the_news(self, limit = 50):
        self.date_scraped = date.today()
        # self.driver = webdriver.Remote(
        #     f'http://192.168.178.37:{self.port}/wd/hub',
        #     DesiredCapabilities.FIREFOX)
        self.driver = webdriver.Firefox()
        self.scrape(limit)
        self.driver.close()

    """
    download_results cleans and stores the preset nr_results from google
     in a csv file
    input:
    term - the current search term. This is part of the resulting data vector.
    """

    def scrape(self, limit=50):
        self.driver.implicitly_wait(10)
        self.driver.get(self.source_url)
        time.sleep(5)
        self.driver.implicitly_wait(20)
        results_in = self.driver.find_elements_by_class_name(
            self.source_class_key)

        for i, raw_result in enumerate(results_in):
            if i >= limit:
                break
            header = raw_result.text
            if len(header) > 0:
                result_clean = {'term_params': header,
                                'date_scraped': self.date_scraped,
                                'source': self.source,
                                'domain': self.source_domain,
                                'political_orientation': self.political_orientation}

                self.existing_results = \
                    self.existing_results.append(result_clean,
                                                 ignore_index=True)
        self.existing_results.to_csv(self.path_results, mode='a', header=False,
                                     index=False)

