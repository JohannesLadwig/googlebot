import random as r
from selenium.webdriver.common.keys import Keys
import time
import json
import math
import tldextract
import scipy.interpolate as si
from datetime import datetime
import pytz
import selenium.common.exceptions as sel_exc


from pytz import reference

TITLE_LOC = {'Breitbart': 0, 'Slate': 0, 'AlterNet': 0, 'TheBlaze': 0}


def natural_typing_in_field(field, string, keep_errors=True, min_delay=0.18, max_delay=0.22,
                            p_error=0.03):
    with open("Data/diverse/adjacent_letters.json", 'r') as f:
        letters_dict = json.load(f)
    letters = "abcdefghijklmnopqrstuvwxyz"
    i = 0
    for i, letter in enumerate(string):
        delay = r.uniform(min_delay, max_delay)
        time.sleep(delay)
        make_mistake = p_error > r.uniform(0, 1)
        if make_mistake and (letter in letters):
            error = r.choice(letters_dict[string[i]])
            field.send_keys(error)
            nr_following = r.choice([0, 1, 2, 3])
            true_following = 1
            for error in string[i:i + nr_following]:
                delay = r.uniform(min_delay, max_delay)
                time.sleep(delay)
                field.send_keys(error)
                true_following += 1
            delay = r.uniform(min_delay, max_delay)
            time.sleep(delay)

            keep_mistake = (r.choices([True, False], [0.22, 0.78])[0]) and keep_errors
            while true_following > 0 and not keep_mistake:
                delay = r.uniform(min_delay, max_delay)
                time.sleep(delay)

                field.send_keys(Keys.BACKSPACE)
                true_following -= 1
            delay = r.uniform(min_delay, max_delay)
            time.sleep(delay)
        field.send_keys(letter)
    field.send_keys(Keys.DELETE)


def clean_result(raw_text):
    """ Takes a raw version of a google result and returns the results domain,
    title and the text body of the result.

    raw_text -- a list of strings that form a google result. The list should be
                of length at least 3. Else an exception is raised.
    """

    if len(raw_text) >= 3:
        lines = raw_text.split('\n')
        title = lines[0]
        try:
            domain = lines[1].split('›')[0]
        except:
            Warning(f"{raw_text} is strange, please look into this")
            domain = None
        body = "\n".join(lines[2:])
    else:
        raise Exception(f"raw_text: {raw_text} is not of the usual shape")
    return title, domain, body


def clean_scrape(raw_text, source):
    """ Takes a raw version of a google result and returns the results domain,
    title and the text body of the result.

    raw_text -- a list of strings that form a google result. The list should be
                of length at least 3. Else an exception is raised.
    """

    if len(raw_text) >= 1:
        lines = raw_text.split('\n')
        header = lines[TITLE_LOC[source]]
    else:
        raise Exception(f"raw_text: {raw_text} is not of the usual shape")
    return header


def select_breitbart(raw_html):
    title = raw_html.find('a').get('title')

    return title.strip()


def select_the_blaze(raw_html):
    title = raw_html.get('aria-label')
    return title.strip()


def select_slate(raw_html):
    title = raw_html.get_text()
    return title.strip()


def speech_bool(input_string):
    value = False
    input_string = input_string.lower().strip()
    if input_string == 'y':
        value = True

    return value


def extract_domain(url):
    try:
        split = tldextract.extract(url)
    except TypeError:
        raise TypeError(f'{url} is strange')
    domain = split.domain + '.' + split.suffix
    return domain


def result_domain_match(result, target_domain):
    url = clean_result(result)[1]
    if url is not None:
        domain = extract_domain(url)
        is_match = domain == target_domain
    else:
        print(result)
        print(target_domain)
        is_match = False
        return None
    return is_match


def dist(x_0, x_1, y_0, y_1):
    return math.sqrt((x_0 - x_1) ** 2 + (y_0 - y_1) ** 2)


def clamp(val, max_lim, min_lim=0):
    """
        :param val: numeric to be restricted to [min_lim, max_lim]
        :param max_lim: numeric
        :param min_lim: numeric
        :return val_new: numeric, if val in range returns val, else closest bound
        """
    if max_lim < min_lim:
        min_lim, max_lim = max_lim, min_lim

    val_new = max(min_lim, val)
    val_new = min(val_new, max_lim)

    return val_new


def calc_spline(t, ipl_t, nodes):
    """
    :param t: list, numeric time vector for nodes
    :param ipl_t: list, numeric, time vector for desired points
    :param nodes: list_numeric, points that the spline will pass
    :return list, numeric: list of points that the spline passes at times ipl_t

    Fit a cubic spline to nodes with corresponding times t and return values at
    times ipl_t
    """
    spline_param = si.splrep(t, nodes, k=3)
    spline_list = list(spline_param)
    nodes_list = nodes.tolist()
    spline_list[1] = nodes_list + [0.0, 0.0, 0.0, 0.0]
    points = si.splev(ipl_t, spline_list)
    return points


def get_time(TZ):
    current_time = datetime.now(pytz.timezone(TZ)).hour
    return current_time


def get_timezone():
    tz = time.tzname[0]
    return tz


def connection_handler(driver, url, wait=10, max_tries=3):
    """
    :param driver: selenium driver object
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
            driver.get(url)
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
            else:
                issue = 'webdriver'
        except:
            issue = 'unknown hard crash'
        retries += 1
    time.sleep(120)
    try:
        driver.get(url)
        issue = None
    except sel_exc.TimeoutException:
        issue = 'timeout'
    except sel_exc.WebDriverException:
        issue = 'webdriver'
    except:
        issue = 'Unknown hard crash'
    return issue
