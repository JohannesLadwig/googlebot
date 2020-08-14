import random as r
from selenium.webdriver.common.keys import Keys
import time
import json
import math
import tldextract
import scipy.interpolate as si

TITLE_LOC = {'Breitbart': 0, 'Slate': 0, 'AlterNet': 0, 'TheBlaze': 0}


def natural_typing_in_field(field, string, min_delay=0.225, max_delay=0.275,
                            p_error=0.05):
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
            while true_following > 0:
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
    return raw_html.find('a').get('title')


def select_the_blaze(raw_html):
    return raw_html.get('aria-label')


def select_slate(raw_html):
    return raw_html.get_text()


def speech_bool(input_string):
    value = False
    input_string = input_string.lower().strip()
    if input_string == 'y':
        value = True

    return value


def extract_domain(url):
    split = tldextract.extract(url)
    domain = split.domain + '.' + split.suffix
    return domain


def result_domain_match(result, target_domain):
    url = clean_result(result)[1]
    domain = extract_domain(url)
    is_match = domain == target_domain
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

