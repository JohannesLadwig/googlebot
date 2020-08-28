
import pandas as pd
import json

COL_NAMES = ['GlobalEventID', 'Day', 'MonthYear', 'Year', 'FractionDate',
             'Actor1Code', 'Actor1Name', 'Actor1CountryCode',
             'Actor1KnownGroupCode', 'Actor1EthnicCode', 'Actor1Religion1Code',
             'Actor1Religion2Code', 'Actor1Type1Code', 'Actor1Type2Code',
             'Actor1Type3Code', 'Actor2Code', 'Actor2Name', 'Actor2CountryCode',
             'Actor2KnownGroupCode', 'Actor2EthnicCode', 'Actor2Religion1Code',
             'Actor2Religion2Code', 'Actor2Type1Code', 'Actor2Type2Code',
             'Actor2Type3Code',
             'isRootEvent', 'EventCode', 'EventBaseCode', 'EventRootCode',
             'QuadClass', 'GoldsteinScale', 'NumMentions', 'NumSources',
             'NumArticles', 'AvgTone',
             'Actor1Geo_Type', 'Actor1Geo_Fullname', 'Actor1Geo_CountryCode',
             'Actor1Geo_ADM1Code', 'Actor1Geo_ADM2Code', 'Actor1Geo_Lat',
             'Actor1Geo_Long', 'Actor1Geo_FeatureID',
             'Actor2Geo_Type', 'Actor2Geo_Fullname', 'Actor2Geo_CountryCode',
             'Actor2Geo_ADM1Code', 'Actor2Geo_ADM2Code', 'Actor2Geo_Lat',
             'Actor2Geo_Long', 'Actor2Geo_FeatureID',
             'ActionGeo_Type', 'ActionGeo_Fullname', 'ActionGeo_CountryCode',
             'ActionGeo_ADM1Code', 'ActionGeo_ADM2Code', 'ActionGeo_Lat',
             'ActionGeo_Long', 'ActionGeo_FeatureID',
             'DATEADDED', 'SOURCEURL']

RELEVANT_COLL_NAMES = ['GlobalEventID',
                       'Day',
                       'Actor1Name', 'Actor1CountryCode',
                       'Actor2Name', 'Actor2CountryCode',
                       'isRootEvent', 'EventCode', 'NumMentions', 'NumSources',
                       'NumArticles',
                       'Actor1Geo_Type', 'Actor1Geo_Fullname',
                       'Actor1Geo_CountryCode',
                       'Actor1Geo_ADM1Code', 'Actor1Geo_ADM2Code',
                       'Actor2Geo_Type', 'Actor2Geo_Fullname',
                       'Actor2Geo_CountryCode',
                       'ActionGeo_Fullname', 'ActionGeo_CountryCode',
                       ]

COUNTRY_COLS = ['Actor1CountryCode',
                'Actor2CountryCode',
                'Actor1Geo_CountryCode',
                'Actor2Geo_CountryCode',
                'ActionGeo_CountryCode',
                ]
DECODE = 'Data/diverse/CameoTranslate.json'
with open(DECODE, 'r') as js:
    conversion = json.load(js)

GDELTV2_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
rows = [range(0, )]
list_urls = pd.read_csv(GDELTV2_URL, sep=' ', names=['idx', 'smth', 'url'],
                        low_memory=False)
events = list_urls.iloc[::3, 2].tolist()
last_12_hours = events[-48:]

raw_events = pd.DataFrame(columns=RELEVANT_COLL_NAMES)
for url in last_12_hours:
    raw_events = raw_events.append(pd.read_csv(url,
                                               sep='\t',
                                               lineterminator='\n',
                                               low_memory=False,
                                               names=COL_NAMES,
                                               # usecols=RELEVANT_COLL_NAMES,
                                               dtype={'EventCode': 'str', 'GlobalEventID': 'str'},
                                               parse_dates=['Day']),
                                   ignore_index=True)

us_events = pd.DataFrame(columns=['GlobalEventID']+RELEVANT_COLL_NAMES[2:])
for col in COUNTRY_COLS:
    us_events = us_events.merge(raw_events.loc[raw_events[col].isin(['US', 'USA'])][['GlobalEventID']+RELEVANT_COLL_NAMES[2:]],
                                how='outer')
us_events = us_events.merge(raw_events[RELEVANT_COLL_NAMES[:1]], how='left', on='GlobalEventID')
us_events.sort_values(by='NumArticles', ascending=False, inplace=True, ignore_index=True)
us_events = us_events[:100]
EventText = []
for idx, event in enumerate(us_events['EventCode']):
    EventText += [conversion[event]]
