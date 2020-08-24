from Code.SingleBot import SingleBot
import time
import os
import random
import json
from datetime import datetime
from Code.SeleniumDocker import SeleniumDocker
from Code.ProxyDocker import ProxyDocker


class Swarm:
    COL_NAMES = ('term_params', 'rank', 'domain', 'title', 'text')

    def __init__(self,
                 port,
                 nr_inst,
                 flag,
                 nr_searches_creation,
                 path_terms_creation,
                 path_terms_benign,
                 nr_searches_exp,
                 path_terms_experiment,
                 swarm_name,
                 proxy={},
                 timezone='UTC',
                 nr_results=1,
                 delay_min=10,
                 night_search=False,
                 dir_results='Data/results/',
                 dir_cookie_jar='Data/cookies/',
                 dir_log='Data/log_files/swarms/',
                 visual=False
                 ):
        """
        :param port: string, access selenium docker image
        :param nr_inst: int, nr. of individual bots the swarm runs
        :param flag: string, flag indicates political orientation/nature of the bot
        :param nr_searches_creation: int, nr. of searches to run without storing results
        :param path_terms_creation: str, path to a json containing political creation terms
        :param path_terms_benign: str, path to a json containing non political terms
        :param nr_searches_exp: int, nr. of searches in experiment
        :param path_terms_experiment: str, path to a json containing 'neutral' political terms
        :param swarm_name: str, name of this swarm
        :param nr_results: int, nr of results to store
        :param delay_min: int, delay between rounds of searches
        :param night_search: boolean, if False, searches are only conducted during the day
        :param dir_results: str, directory where results are to be stored
        :param dir_cookie_jar: str, directory where cookies are to be stored
        :param dir_log: str, directory where swarm creates its log
        :param visual: boolean, if True, instannces are run in non dockerized, visual selenium
        """
        self.port = port
        self.nr_inst = nr_inst
        self.flag = flag

        self.nr_searches_creation = nr_searches_creation
        self.path_terms_creation = path_terms_creation

        self.visual = visual

        self.path_terms_benign = path_terms_benign

        self.nr_searches_exp = nr_searches_exp
        self.path_terms_experiment = path_terms_experiment

        self.swarm_name = swarm_name

        self.proxy = proxy
        self.timezone = timezone
        self.dir_cookie_jar = dir_cookie_jar
        self.dir_results = dir_results

        # initialize empty dictionary for instances
        self.instances = {}
        self.nr_results = nr_results
        self.delay_min = delay_min

        self.night_search = night_search

        self.create_terms = 'empty'
        self.benign_terms = 'empty'
        self.exp_terms = 'empty'

        self.exp_progress = 0

        self.path_log = dir_log
        self.log = None
        self.handle_log('r')

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, new_port):
        self._port = new_port

    @property
    def flag(self):
        return self._flag

    @flag.setter
    def flag(self, new_flag):
        self._flag = new_flag

    @property
    def nr_inst(self):
        return self._nr_inst

    @nr_inst.setter
    def nr_inst(self, number):
        if number > 0:
            self._nr_inst = number
        else:
            raise ValueError(
                f'Invalid number of instances: {number}, nr. of instances should be an integer > 0'
            )

    @property
    def nr_searches_creation(self):
        return self._nr_searches_creation

    @nr_searches_creation.setter
    def nr_searches_creation(self, number):
        if number >= 0:
            self._nr_searches_creation = number
        else:
            raise ValueError(
                f'Invalid number of searches: {number}, nr. of searches should be an integer >= 0')

    @property
    def nr_searches_exp(self):
        return self._nr_searches_exp

    @nr_searches_exp.setter
    def nr_searches_exp(self, number):
        if number >= 0:
            self._nr_searches_exp = number
        else:
            raise ValueError(
                f'Invalid number of searches: {number}, nr. of searches should be an integer >= 0')

    @property
    def night_search(self):
        return self._night_search

    @night_search.setter
    def night_search(self, boolean):
        self._night_search = boolean

    """
    property getter and setter for path_search_terms.
    Calls self.initialize_terms() when path is set. This loads search terms into\
    memmory. 
    """

    @property
    def path_terms_creation(self):
        return self._path_terms_creation

    @path_terms_creation.setter
    def path_terms_creation(self, path):
        if os.path.exists(path):
            self._path_terms_creation = path
        else:
            raise ValueError(f'{path} is not a valid path')

    @property
    def path_terms_benign(self):
        return self._path_terms_benign

    @path_terms_benign.setter
    def path_terms_benign(self, path):
        if os.path.exists(path):
            self._path_terms_benign = path
        else:
            raise ValueError(f'{path} is not a valid path')

    @property
    def path_terms_experiment(self):
        return self._path_terms_experiment

    @path_terms_experiment.setter
    def path_terms_experiment(self, path):
        if os.path.exists(path):
            self._path_terms_experiment = path
        else:
            raise ValueError(f'{path} is not a valid path')

    """
    getter and setter for log file path. Expects a directory, not a path!
    Creates a log file at dir/swarm_name and initializes an empty log format if
    none is present.
    """

    @property
    def path_log(self):
        return self._path_log

    @path_log.setter
    def path_log(self, path):
        if os.path.isdir(path):
            self._path_log = path + self.swarm_name
        else:
            raise ValueError('log directory does not exist')

        if not os.path.exists(self._path_log):
            empty_log = {'incomplete_create': False,
                         'incomplete_exp': False,
                         'issue': '',
                         'create': {},
                         'exp': {},
                         'nr_create': 0,
                         'nr_exp': 0,
                         'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
            with open(self._path_log, 'w') as log_file:
                json.dump(empty_log, log_file)
            del log_file

    """
    Setter and getterpass for nr_results. If nr_results == 0, sets store_results to
    false.
    """

    @property
    def nr_results(self):
        return self._nr_results

    @nr_results.setter
    def nr_results(self, number):
        if number >= 0:
            self._nr_results = int(number)
            if len(self.instances) > 0:
                for bot in self.instances.values():
                    bot.nr_results = number
        else:
            raise ValueError(f'{number} should be an integer > 0')

    @property
    def delay_min(self):
        return self._delay_min

    @delay_min.setter
    def delay_min(self, delay):
        if delay >= 0:
            self._delay_min = delay
        else:
            raise ValueError(f'The delay {delay} should be a numeric value > 0')

    @property
    def exp_progress(self):
        return self._exp_progress

    @exp_progress.setter
    def exp_progress(self, number):
        if number >= 0:
            self._exp_progress = int(number)

        else:
            raise ValueError(f'{number} should be an integer > 0')

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    def proxy(self, proxy_dict):
        self._proxy = {'domain': None, 'username': None, 'password': None, 'port': None}
        if 'domain' in proxy_dict:
            self._proxy['domain'] = proxy_dict['domain']
            if 'username' in proxy_dict:
                self._proxy['username'] = proxy_dict['username']
                if 'password' in proxy_dict:
                    self._proxy['password'] = proxy_dict['password']
            if 'port' in proxy_dict:
                self._proxy['port'] = proxy_dict['port']

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, zone_name):
        with open('Data/diverse/timezones.json', 'r') as tz_file:
            valid_tz = json.load(tz_file)
        if zone_name not in valid_tz:
            raise ValueError(
                f'{self.zone_name} is not a valid timezone. See Data/diverse/timezones.json')
        else:
            self._timezone = zone_name

    @property
    def benign_terms(self):
        return self._benign_terms

    @benign_terms.setter
    def benign_terms(self, action):
        if action == 'fill':
            with open(self.path_terms_benign, 'r') as ben_file:
                try:
                    self._benign_terms = json.load(ben_file)
                except json.decoder.JSONDecodeError:
                    raise Exception(
                        f'The benign file has been corrupted while path={self.path_terms_benign}, terms={self.benign_terms}')
            del ben_file
        elif action == 'empty':
            self._benign_terms = None
        else:
            raise ValueError(f'Expected fill or empty, received {action}')

    @property
    def create_terms(self):
        return self._create_terms

    @create_terms.setter
    def create_terms(self, action):
        if action == 'fill':
            with open(self.path_terms_creation, 'r') as create_file:
                try:
                    self._create_terms = json.load(create_file)
                except json.decoder.JSONDecodeError:
                    raise Exception(
                        f'A {self.flag} create file has been corrupted {self.swarm_name}')
            del create_file
        elif action == 'empty':
            self._create_terms = None
        else:
            raise ValueError(f'Expected fill or empty, received {action}')

    @property
    def exp_terms(self):
        return self._exp_terms

    @exp_terms.setter
    def exp_terms(self, action):
        if action == 'fill':
            with open(self.path_terms_experiment, 'r') as exp_file:
                try:
                    self._exp_terms = json.load(exp_file)
                except json.decoder.JSONDecodeError:
                    raise Exception(
                        f'A {self.flag} experiment file has been corrupted {self.swarm_name}')
            del exp_file
        elif action == 'empty':
            self._exp_terms = None
        else:
            raise ValueError(f'Expected fill or empty, received {action}')

    """Saves and Reads log:
        - w to save log to log file
        - r to read log from log file
     """

    def handle_log(self, mode):
        if mode == 'r':
            with open(self.path_log, 'r') as log_file:
                self.log = json.load(log_file)
            del log_file
        if mode == 'w':
            self.log['time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            with open(self.path_log, 'w') as log_file:
                json.dump(self.log, log_file)
            del log_file

    def launch_proxy(self):

        selenium_proxy = None
        if self.proxy['domain'] is not None:
            if self.proxy['port'] is not None:
                ProxyDocker(f'proxy_{self.swarm_name}',
                            self.proxy['domain'],
                            self.proxy['username'],
                            self.proxy['password'],
                            self.proxy['port'])
                if self.visual:
                    selenium_proxy = f'localhost:{self.proxy["port"]}'
                else:
                    selenium_proxy = f'172.17.0.1:{self.proxy["port"]}'
            else:
                selenium_proxy = self.proxy['domain']
        print(selenium_proxy)
        return selenium_proxy

    def launch(self, exist):
        selenium_proxy = self.launch_proxy()
        if not self.visual:
            container = SeleniumDocker(self.port,
                                       'container_' + self.swarm_name,
                                       self.timezone)
            time.sleep(5)
        for i in range(self.nr_inst):
            bot_id = f'{self.swarm_name}{i}'
            instance = SingleBot(self.port,
                                 'dem',
                                 bot_id=bot_id,
                                 nr_results=self.nr_results,
                                 visual=self.visual,
                                 existing=exist,
                                 proxy=selenium_proxy)
            self.instances[bot_id] = instance
            self.log['create'][bot_id] = self.log['create'].get(bot_id, 0)
            self.log['exp'][bot_id] = self.log['exp'].get(bot_id, 0)

    def time_handler(self, t_elapsed):
        office_hour = True
        if not (7 <= time.localtime()[3] < 22):
            office_hour = False
        elif (wait := (60 * self.delay_min - t_elapsed + (
                t_elapsed / self.nr_inst))) > 0:
            time.sleep(wait)
        return office_hour or self.night_search

    def wake(self):
        self.create_terms = 'fill'
        self.benign_terms = 'fill'
        self.exp_terms = 'fill'

    def send_to_bed(self):
        self.create_terms = 'empty'
        self.exp_terms = 'empty'
        self.benign_terms = 'empty'
        self.handle_log('w')

    def search(self, terms, store=False):
        wait = 60 * self.delay_min / (2 * self.nr_inst + 1)
        overall_success = True
        t_0 = time.perf_counter()
        if store:
            step = 'exp'
        else:
            step = 'create'

        bot_subset = []

        if self.log[f'incomplete_{step}']:
            self.log[f'incomplete_{step}'] = False
            max_nr_searched = max(self.log[step].values())
            for bot_id, nr_searched in self.log[step].items():
                if nr_searched < max_nr_searched:
                    bot_subset.append(bot_id)
        if len(bot_subset) == 0:
            bot_subset = self.instances.keys()

        for bot_id, term in zip(bot_subset, terms):
            bot = self.instances[bot_id]
            issue = bot.launch()
            if issue is None:
                issue = bot.search(term, store)
            bot.shutdown()
            success = issue is None
            if success:
                self.log[step][bot_id] = self.log[step][bot_id] + 1
            else:
                self.log[f'incomplete_{step}'] = True
                self.log['issue'] = issue
                break
            time.sleep(wait)

        return time.perf_counter() - t_0, success

    def conduct_searches(self, creation_only=False):
        office_hours = self.time_handler(0)
        completed = True
        while office_hours and self.nr_searches_creation > 0:
            source = random.choices(['political', 'benign'], [0.8, 0.2], k=1)
            file_source = {'political': self.create_terms,
                           'benign': self.benign_terms}
            terms = random.choices(file_source[source[0]], k=self.nr_inst)

            time_elapsed, completed = self.search(terms, store=False)

            if not completed:
                print('Creation searches could no longer be conducted')
                break
            self.nr_searches_creation -= 1
            self.log['nr_create'] = self.log['nr_create'] + 1
            self.handle_log('w')
            office_hours = self.time_handler(time_elapsed)

        while not creation_only and office_hours and self.nr_searches_exp > 0 and completed:
            terms = [self.exp_terms[self.exp_progress]] * self.nr_inst
            time_elapsed, completed = self.search(terms, store=True)
            if not completed:
                print('Experiment searches could no longer be conducted')
                break
            self.nr_searches_exp -= 1
            self.log['nr_exp'] = self.log['nr_exp'] + 1
            self.exp_progress += 1
            office_hours = self.time_handler(time_elapsed)
