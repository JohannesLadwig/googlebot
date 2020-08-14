import pandas as pd
import json
import os
import re
import collections
import dateutil.parser as parser
from nltk.corpus import stopwords


import Utilities
from gdelt_url_country import get_country_media

URL = GDEL_GFG_URL = "http://data.gdeltproject.org/gdeltv3/gfg/alpha/lastupdate.txt"

COL_NAMES = ['DATE', 'FromFrontPageURL', 'LinkID', 'LinkPercentMaxID',
             'ToLinkURL', 'LinkText']
IN_COUNTRY_MEDIA = ['Data/diverse/', '_urls.json']

IS_URL = r"[a-z,0-9][\.][a-z,0-9]"

PUNCTUATION = '''!"',;:.-?)([]<>*#\n\t\r'''

S = set(stopwords.words('english'))


with open('Data/diverse/useless_text.json', 'r') as file:
    LIBRARY_OF_USELESS = json.load(file)


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parser.parse(string, fuzzy=fuzzy)
        return True
    except:
        return False


def has_potential(link_text):
    if len(link_text) < 5:
        return False
    if re.search(IS_URL, link_text):
        return False
    if link_text in LIBRARY_OF_USELESS:
        return False
    if is_date(link_text):
        return False
    return True


def clean_text(link_text, remove_stop):
    link_text_list = link_text.split(' ')
    clean_text_list = []
    for token in link_text_list:
        token = token.strip().strip(PUNCTUATION)
        if remove_stop and token in S:
            continue
        if is_date(token):
            continue
        clean_text_list.append(token)
    clean_link_text = " ".join(clean_text_list).strip()
    if len(clean_link_text) == 0:
        return None
    else:
        return clean_link_text


def scan_for_todays_news(country='US', remove_stop=True):
    country_media_path = IN_COUNTRY_MEDIA[0] + country + IN_COUNTRY_MEDIA[1]
    if not os.path.exists(country_media_path):
        get_country_media(country)

    with open(country_media_path, 'r') as file:
        country_media = json.load(file)

    current_url = \
        pd.read_csv(GDEL_GFG_URL, sep=' ', names=['1', '2', 'url'])['url'].loc[
            0]

    data = pd.read_csv(current_url, sep='\t', lineterminator='\n',
                       low_memory=False,
                       names=COL_NAMES,
                       dtype={'FromFrontPageURL': 'str', 'LinkID': 'int',
                              'LinkPercentMaxID': 'float', 'ToLinkURL': 'str',
                              'LinkText': 'str'},
                       parse_dates=['DATE'],
                       error_bad_lines=False)
    data.dropna(subset=['FromFrontPageURL'], inplace=True)
    data['domain'] = data['FromFrontPageURL'].apply(Utilities.extract_domain)
    data = data.loc[data.domain.isin(country_media)]
    data.dropna(subset=['LinkText'], inplace=True)

    data['LinkText'] = data['LinkText'].apply(str.lower)
    data = data.loc[data['LinkText'].apply(has_potential)]

    data['LinkText'] = data['LinkText'].apply(clean_text, remove_stop=remove_stop)
    data.dropna(subset=['LinkText'], inplace=True)
    data.reset_index(inplace=True, drop=True)

    text = data['LinkText']
    return text


def create_n_gram(line, n, useless_n_grams):

    tokens = line.split(' ')
    n_gram_list = []
    for i in range(len(tokens) - n + 1):
        token = ' '.join(tokens[i: i + n])
        if is_date(token):
            continue
        if token in useless_n_grams:
            continue
        n_gram_list.append(token)

    if len(n_gram_list) == 0:
        n_gram_list = None
    return n_gram_list


def common_n_grams(text, n, stop_removed):
    flag = ''
    if stop_removed:
        flag = 'b'
    with open(f'Data/diverse/useless_text_{n}_{flag}.json', 'r') as file:
        useless_n_grams = json.load(file)

    n_grams = text.apply(create_n_gram, args=(n,useless_n_grams,))
    n_grams.dropna(inplace=True)
    n_grams.reset_index(inplace=True, drop=True)
    freq = collections.Counter()

    for gram_list in n_grams:
        freq.update(gram_list)

    return freq


if __name__ == "__main__":
    data = scan_for_todays_news('US', remove_stop=True)
    Freq_4 = common_n_grams(data, 4, stop_removed=True)
    potential = Freq_4.most_common(20)
    with open('Data/terms/exp_terms.json', 'w') as file:
        json.dump(list(zip(*potential))[0], file, separators=(',\n', ':'))
    # potentialy_bad = Freq.most_common(400)
    # with open(f'Data/diverse/useless_text_{4}_b.json', 'w') as file:
    #     json.dump(list(zip(*potentialy_bad))[0], file, separators=(',\n', ':'))
