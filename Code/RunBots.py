from Code.Swarm import Swarm
import multiprocessing as mp
import time
from Code import gdelt_gkg as gkg, Utilities as Util, \
    GenerateSearchTerms as Gen, RunScraper as Scrape
import json
from functools import partial


def declare_swarms(inst, t, night, proxy):
    a = Swarm(port=4444,
              nr_inst=inst,
              flag='left',
              nr_searches_creation=0,
              path_terms_creation="Data/terms/left_terms.json",
              path_terms_benign="Data/terms/benign_terms.json",
              nr_searches_exp=0,
              path_terms_experiment="Data/terms/exp_terms.json",
              swarm_name='a',
              proxy=proxy['swarm_a'],
              timezone=proxy['swarm_a']['TZ'],
              nr_results=1,
              delay_min=t,
              night_search=night,
              dir_results='Data/results/',
              dir_cookie_jar='Data/cookies/')

    b = Swarm(port=4445,
              nr_inst=inst,
              flag='left',
              nr_searches_creation=0,
              path_terms_creation="Data/terms/left_terms.json",
              path_terms_benign="Data/terms/benign_terms.json",
              nr_searches_exp=0,
              path_terms_experiment="Data/terms/exp_terms.json",
              swarm_name='b',
              proxy=proxy['swarm_b'],
              timezone=proxy['swarm_b']['TZ'],
              nr_results=1,
              delay_min=t,
              night_search=night,
              dir_results='Data/results/',
              dir_cookie_jar='Data/cookies/'
              )
    c = Swarm(port=4446,
              nr_inst=inst,
              flag='right',
              nr_searches_creation=0,
              path_terms_creation="Data/terms/right_terms.json",
              path_terms_benign="Data/terms/benign_terms.json",
              nr_searches_exp=0,
              path_terms_experiment="Data/terms/exp_terms.json",
              swarm_name='c',
              proxy=proxy['swarm_c'],
              timezone=proxy['swarm_c']['TZ'],
              nr_results=1,
              delay_min=t,
              night_search=night,
              dir_results='Data/results/',
              dir_cookie_jar='Data/cookies/'
              )
    d = Swarm(port=4447,
              nr_inst=inst,
              flag='right',
              nr_searches_creation=0,
              path_terms_creation="Data/terms/right_terms.json",
              path_terms_benign="Data/terms/benign_terms.json",
              nr_searches_exp=0,
              path_terms_experiment="Data/terms/exp_terms.json",
              swarm_name='d',
              proxy=proxy['swarm_d'],
              timezone=proxy['swarm_d']['TZ'],
              nr_results=1,
              delay_min=t,
              night_search=night,
              dir_results='Data/results/',
              dir_cookie_jar='Data/cookies/'
              )
    e = Swarm(port=4448,
              nr_inst=inst,
              flag='control',
              nr_searches_creation=0,
              path_terms_creation="Data/terms/right_terms.json",
              path_terms_benign="Data/terms/benign_terms.json",
              nr_searches_exp=0,
              path_terms_experiment="Data/terms/exp_terms.json",
              swarm_name='e',
              proxy=proxy['swarm_e'],
              timezone=proxy['swarm_e']['TZ'],
              nr_results=1,
              delay_min=t,
              night_search=night,
              dir_results='Data/results/',
              dir_cookie_jar='Data/cookies/'
              )
    return [a, b, c, d, e]


def searches_remaining(process, all_bots):
    remaining = 0
    if process in ['c', 'r']:
        for individual in all_bots:
            remaining += individual.nr_searches_creation
    if process in ['r', 'e']:
        for individual in all_bots:
            remaining += individual.nr_searches_exp

    return remaining


def set_search_param(process, all_bots):
    if process in ['c', 'r']:
        nr_search = int(input(
            'Please input the desired nr. of searches per instance in creating a profile: '))
        for individual in all_bots[:-1]:
            individual.nr_searches_creation = nr_search
    if process in ['e', 'r']:
        nr_search = int(input(
            'Please input the desired nr. of searches per instance for experimentation: '))
        nr_res = int(input(
            'Please input the desired nr. of results you wish to store per search: '))
        for individual in all_bots:
            individual.nr_searches_exp = nr_search
            individual.nr_results = nr_res


def execute(swarm, create=False):
    swarm.wake()

    swarm.conduct_searches(create)

    swarm.send_to_bed()

    return swarm


def visual(nr_vis, t_delay, nr_searches, nr_experiment, proxy):
    bernd = Swarm(port=4444,
                  nr_inst=nr_vis,
                  flag='right',
                  nr_searches_creation=nr_searches,
                  path_terms_creation="Data/terms/right_terms.json",
                  path_terms_benign="Data/terms/benign_terms.json",
                  nr_searches_exp=nr_experiment,
                  path_terms_experiment="Data/terms/exp_terms.json",
                  swarm_name='bernd',
                  proxy=proxy['bernd'],
                  timezone=proxy['bernd']['TZ'],
                  nr_results=3,
                  delay_min=t_delay,
                  night_search=True,
                  dir_results='Data/results/',
                  dir_cookie_jar='Data/cookies/',
                  dir_log='Data/log_files/swarms/',
                  visual=True)
    bernd.launch(exist=False)
    execute(bernd)


def launch_control(all_bots, process):
    launch = False
    creation_complete = searches_remaining('c', all_bots) == 0
    if creation_complete or (process == 'e'):
        launch = True
    return launch


# docker run -p 4445:4444 -d --shm-size=2g  --name bot_2 selenium/standalone-firefox
if __name__ == "__main__":
    run_visualization = Util.speech_bool(
        input('Only run a visual example? (y/n): '))
    nr_inst = int(input('Nr. of instances per swarm: '))

    delay = int(input('Delay between searches: '))

    print('Please make sure you have set proxy data at Data/proxy_data/proxy_data.json')
    with open('Data/proxy_data/proxy_data.json', 'r') as raw_proxy_data:
        proxy_data = json.load(raw_proxy_data)

    if run_visualization:
        nr_creation = int(
            input('Please input the desired nr. of creation searches: '))
        nr_exp = int(
            input('Please input the desired nr. of experimental searches: '))
        visual(nr_inst, delay, nr_creation, nr_exp, proxy_data)
        quit()

    night_search = Util.speech_bool(input('Conduct searches at night (y/n): '))
    restart = Util.speech_bool(
        input('Are you restarting a crashed experiment session? (y/n): '))

    swarm_list = declare_swarms(nr_inst, delay, night_search, proxy_data)
    swarm_a, swarm_b, swarm_c, swarm_d, swarm_e = swarm_list

    keep_cookie = Util.speech_bool(
        input('Re-use old cookies and run from log? (y/n): '))
    print('Creating the bots, this will take a minute.')

    for bot in swarm_list:
        bot.launch(keep_cookie)
    print(
        f'{nr_inst} instances have been created for four political and one neutral swarm')

    instruction = 'r'
    bots_asleep = True
    while instruction != 'q':
        instruction = input(
            f'Enter: \n - "r" to run all processes \n - "c" to run creation \n - "e" to run experimentation\n - "d" to change delay parameter (currently {delay} minutes)\n - "q" to quit this program\n  ')

        if instruction == 'q':
            continue
        elif instruction == 'd':
            delay = int(input('Delay between searches: '))
            for bot in swarm_list:
                bot.delay_min = delay
        elif instruction in ["e", "c", "r"]:
            set_search_param(instruction, swarm_list)
            create_only = True

            while searches_remaining(instruction, swarm_list) > 0:
                if is_exp := launch_control(swarm_list, instruction):
                    create_only = False
                if (7 > time.localtime()[3] or time.localtime()[
                    3] >= 22) and not night_search:
                    bots_asleep = True
                    print('Its night, bots are asleep!')
                while (7 > time.localtime()[3] or time.localtime()[
                    3] >= 22) and not night_search:
                    time.sleep(300)

                if bots_asleep and not is_exp:
                    print("Reading todays news")
                    Scrape.news_circle()
                    print(
                        "Converting headlines to queries, creating fresh set of nonsense")
                    Gen.GenerateSearchTerms('Data/terms/Raw_Media_Headers.csv')
                    Gen.GenerateBenignTerms()
                elif bots_asleep and not restart:
                    for bot in swarm_list:
                        bot.exp_progress = 0
                    print("Checking the GDELT Database for current issues")
                    gkg.main(50)
                else:
                    restart = False
                print("Waking the bots")
                bots_asleep = False
                print(
                    f'{searches_remaining(instruction, swarm_list)} searches remain')
                with open('Data/terms/benign_terms.json', 'r') as ben_file:
                    try:
                        test_terms = json.load(ben_file)
                    except:
                        raise Exception(
                            f'The benign file has been corrupted just before restart')

                intermediate = partial(execute, create=create_only)
                pool = mp.Pool(processes=5)
                swarm_list = pool.map(intermediate, swarm_list)
                pool.close()
                pool.join()
                print(
                    f'{searches_remaining(instruction, swarm_list)} searches remain')
