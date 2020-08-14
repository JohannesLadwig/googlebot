from datetime import date
import pandas as pd
import os
from Utilities import *
import requests
from bs4 import BeautifulSoup



class SingleScraper:
    COL_NAMES = (
        'term_params', 'date_scraped', 'source', 'domain',
        'political_orientation')
    SOURCE_PROPERTIES = {
        'Breitbart': {'URL': 'https://www.breitbart.com/politics/',
                      'CLASS_KEY': 'tC',
                      'METHOD': select_breitbart,
                      'DOMAIN': 'breitbart.com'},
        'TheBlaze': {'URL': 'https://www.theblaze.com/Politics/',
                     'CLASS_KEY': 'widget__headline-text custom-post-headline',
                     'METHOD': select_the_blaze,
                     'DOMAIN': 'theblaze.com'},
        'Slate': {'URL': 'https://slate.com/news-and-politics',
                  'CLASS_KEY': 'topic-story__hed',
                  'METHOD': select_slate,
                  'DOMAIN': 'slate.com'},
        'AlterNet': {'URL': 'https://www.alternet.org/category/news-politics/',
                     'CLASS_KEY': 'entry-title grid-title',
                     'METHOD': select_slate,
                     'DOMAIN':'alternet.com'}
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

        self.existing_results = pd.DataFrame(columns=SingleScraper.COL_NAMES)

        self.source_url, self.source_class_key, self.select_method, self.source_domain = \
            SingleScraper.SOURCE_PROPERTIES[self.source].values()

        # self.headers = requests.utils.default_headers()
        # self.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'})
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}

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

    """
    download_results cleans and stores the preset nr_results from google
     in a csv file
    input:
    term - the current search term. This is part of the resulting data vector.
    """

    def read_the_news(self):
        self.date_scraped = date.today()
        req = requests.get(self.source_url, headers=self.headers)
        soup = BeautifulSoup(req.content, 'html.parser')
        results_in = soup.find_all(class_=self.source_class_key)
        for raw_result in results_in:
            header = self.select_method(raw_result)
            if len(header) > 0:
                result_clean = {'term_params': header,
                                'date_scraped': self.date_scraped,
                                'source': self.source,
                                'domain': self.source_domain,
                                'political_orientation': self.political_orientation}
                self.existing_results = \
                    self.existing_results.append(result_clean,
                                                 ignore_index=True)
        self.existing_results.to_csv(self.path_results, mode='a', index=False, header=False)
