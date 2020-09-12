from Code.SingleScraper import SingleScraper
import pandas as pd
from datetime import date
from Code.SingleScraperSelenium import SingleScraperSelenium

OUT_PATH = 'Data/terms/Raw_Media_Headers.csv'
COL_NAMES = ['term_params',
             'date_scraped',
             'source',
             'domain',
             'political_orientation']


def news_circle():
    Donald = SingleScraper(source='Breitbart',
                           political_orientation='right',
                           path_results=OUT_PATH)

    Mitch = SingleScraper(source='TheBlaze',
                          political_orientation='right',
                          path_results=OUT_PATH)

    Bernie = SingleScraper(source='Slate',
                           political_orientation='left',
                           path_results=OUT_PATH)

    Elizabeth = SingleScraper(source='AlterNet',
                              political_orientation='left',
                              path_results=OUT_PATH)

    Alexandria = SingleScraper(source='OccupyDemocrats',
                               political_orientation='left',
                               path_results=OUT_PATH)

    Joe = SingleScraperSelenium(source='CNN',
                                political_orientation='left',
                                path_results=OUT_PATH)

    Kamala = SingleScraperSelenium(source='DailyBeast',
                                   political_orientation='left',
                                   path_results=OUT_PATH)

    Mike = SingleScraper(source='DailyCaller',
                         political_orientation='right',
                         path_results=OUT_PATH)

    Tucker = SingleScraper(source='FoxNews',
                           political_orientation='right',
                           path_results=OUT_PATH)

    Donald.read_the_news()
    Mitch.read_the_news()
    Tucker.read_the_news(20)
    Mike.read_the_news()

    # Bernie.read_the_news()
    Elizabeth.read_the_news()
    Alexandria.read_the_news()
    # Joe.read_the_news(20)
    # Kamala.read_the_news()

    today = pd.Timestamp(date.today())

    headers = pd.read_csv(OUT_PATH, header=0, parse_dates=['date_scraped'])
    todays_headers = headers['date_scraped'] == today
    new_headers = headers.loc[todays_headers]
    new_headers = new_headers.drop_duplicates()
    headers = headers.loc[-todays_headers]
    headers.to_csv(OUT_PATH, mode='w', header=True, index=False)
    new_headers.to_csv(OUT_PATH, mode='a', header=False, index=False)


if __name__ == "__main__":
    news_circle()
