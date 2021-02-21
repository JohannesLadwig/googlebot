from Code.SingleBot import SingleBot
import time
import os
import random
import json
from Code.SeleniumDocker import SeleniumDocker
from Code.ProxyDocker import ProxyDocker
from datetime import datetime
import Code.Utilities as Util
import traceback


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
                 proxy=None,
                 timezone=Util.get_timezone(),
                 nr_results=1,
                 delay_min=10,
                 night_search=False,
                 dir_results='Data/results/',

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
        :param dir_log: str, directory where swarm creates its log
        :param visual: boolean, if True, instannces are run in non dockerized, visual selenium
        """
        if proxy is None:
            proxy = {''}
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
        self.dir_results = dir_results
        self.path_results = f'{self.dir_results}{self.swarm_name}.csv'
        self.path_searches = f'{self.dir_results}{self.swarm_name}_searches.csv'
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

        self._profile_dir = {
            'Host': f'/Users/johannes/Uni/HSG/googlebot/Data/profiles/swarm_{self.swarm_name}',
            'Selenium': f'/Users/johannes/Uni/HSG/googlebot/Data/profiles/swarm_{self.swarm_name}',
        }
        if not visual:
            self._profile_dir['Selenium'] = '/home/profiles'

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

        self.path_results = f'{self.dir_results}{self.swarm_name}.csv'

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
                         'exp_progress': 0,
                         'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                         'profile': {},
                         'profile_path': {}}
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
        self._proxy = {'domain': None, 'username': None, 'password': None,
                       'port': None}
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
        if zone_name is None:
            zone_name = Util.get_timezone()
        with open('Data/diverse/timezones.json', 'r') as tz_file:
            valid_tz = json.load(tz_file)
        if zone_name not in valid_tz:
            raise ValueError(
                f'{zone_name} is not a valid timezone. See Data/diverse/timezones.json')
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
                json.dump(self.log, log_file, indent='  ')
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
            shared_folder_1 = [self._profile_dir["Host"],
                               self._profile_dir["Selenium"]]

            container = SeleniumDocker(self.port,
                                       f'container_{self.swarm_name}',
                                       self.timezone,
                                       bind_config=shared_folder_1,
                                       )

            time.sleep(5)
        with open('Data/diverse/agents_3.json') as profiles_in:
            profiles = json.load(profiles_in)

        for i in range(self.nr_inst):
            bot_id = f'{self.swarm_name}{i}'
            if exist:
                profile = self.log['profile'][bot_id]
            else:
                profile = random.choice(profiles)
                self.log['profile'][bot_id] = profile
            instance = SingleBot(self.port,
                                 self.flag,
                                 bot_id=bot_id,
                                 swarm_name=self.swarm_name,
                                 path_results=self.path_results,
                                 path_searches=self.path_searches,
                                 user_agent=profile,
                                 profile_dir=self._profile_dir,
                                 nr_results=self.nr_results,
                                 visual=self.visual,
                                 existing=exist,
                                 proxy=selenium_proxy)
            self.instances[bot_id] = instance
            self.log['create'][bot_id] = self.log['create'].get(bot_id, 0)
            self.log['exp'][bot_id] = self.log['exp'].get(bot_id, 0)
        self.handle_log('w')

    def time_handler(self, t_elapsed, start_up=False):
        office_hour = True
        if 3 > Util.get_time(self.timezone) or 22 < Util.get_time(
                self.timezone):
            office_hour = False
        while not self._night_search and 3 < Util.get_time(self.timezone) < 7:
            time.sleep(300)
        if start_up:
            wait = 60 * random.uniform(0, self.delay_min / self.nr_inst)
        else:
            wait = 60 * self.delay_min / self.nr_inst
            wait = random.uniform(wait, 1.5 * wait)

        if office_hour and wait > 0:
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
        t_0 = time.perf_counter()
        wait = 60 * self.delay_min / (4 * self.nr_inst)
        success = True
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
            issue = ""
            retries = 0
            while issue is not None and retries < 2:
                issue = bot.launch()
                time.sleep(15)
                retries += 1

            if issue is None:
                try:
                    issue = bot.search(term, store)
                except:
                    print(traceback.format_exc())
                    try:
                        time.sleep(15 * 60 + 1)
                        issue = self.retry_search(bot, term, store)
                    except:
                        issue = 'hard crash'
                        print(traceback.format_exc())
            if issue == 'scroll failure':
                self._restart_docker(bot)
                issue = None
            if issue is not None:
                print(f'{bot_id} encountered {issue} attempting auto restart')
                time.sleep(15 * 60 + 1)
                try:
                    issue = self.retry_search(bot, term, store)
                except:
                    issue = 'hard crash'
                    print(traceback.format_exc())
            if issue is None:
                profile_path = bot.shutdown()
            elif issue == 'scroll failure':
                self._restart_docker(bot)
            else:
                try:
                    profile_path = bot.shutdown()
                except:
                    profile_path = self.log['profile_path'][bot_id]
            self.log['profile_path'][bot_id] = profile_path
            success = issue is None
            if success:
                self.log[step][bot_id] = self.log[step][bot_id] + 1
            else:
                self.log[f'incomplete_{step}'] = True
                self.log['issue'] = issue
                self.handle_log('w')
                print(f'{bot_id} encountered {issue} auto restart failed')
                print(self.log['profile'][bot_id])
                break
            self.handle_log('w')
            time.sleep(random.uniform(3 * wait, 5 * wait))

        return time.perf_counter() - t_0, success

    def conduct_searches(self, creation_only=False):
        office_hours = self.time_handler(0, start_up=True)
        completed = True
        while office_hours and self.nr_searches_creation > 0:

            source = random.choices(['political', 'benign'], [0.8, 0.2], k=1)
            file_source = {'political': self.create_terms,
                           'benign': self.benign_terms}
            terms = random.choices(file_source[source[0]], k=self.nr_inst)
            time_elapsed, completed = self.search(terms, store=False)

            if not completed:
                print(
                    f'Creation searches could no longer be conducted {self.swarm_name}')
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
            self.exp_progress += 1
            self.log['exp_progress'] = self.exp_progress
            self.log['nr_exp'] = self.log['nr_exp'] + 1
            self.handle_log('w')
            office_hours = self.time_handler(time_elapsed)
        self.exp_progress = 0


    def _restart_docker(self, bot):
        try:
            bot.shutdown()
        except:
            None
        if self.proxy['domain'] is not None:
            if self.proxy['port'] is not None:
                ProxyDocker(f'proxy_{self.swarm_name}',
                            self.proxy['domain'],
                            self.proxy['username'],
                            self.proxy['password'],
                            self.proxy['port'])

        time.sleep(2)
        container = SeleniumDocker(self.port,
                                   f'container_{self.swarm_name}',
                                   self.timezone,
                                   bind_config=[
                                       self._profile_dir["Host"],
                                       self._profile_dir["Selenium"]],
                                   )
        time.sleep(5)

    def retry_search(self, bot, term, store):
        self._restart_docker(bot)
        bot.launch()
        issue = bot.search(term, store)
        return issue
