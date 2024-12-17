from bs4 import BeautifulSoup
from loguru import logger
import constant as const
from tqdm import tqdm 
import pandas as pd
import numpy as np
import requests
import time
import sys
import re


class CianParser(object):
    def __init__(self, headers=const.headers_cian, main_link=const.cian_main_link, max_pages_cnt=50, max_house_cnt=None):
        self.headers = headers
        self.main_link = main_link
        self.max_pages_cnt = max_pages_cnt
        self.max_house_cnt = max_house_cnt
    

    def retry(foo, waiting=10, exception=requests.exceptions.ConnectionError):
        def inner(self, *args, **kwargs):
            while True:
                try:
                    return foo(self, *args, **kwargs)
                except exception as connection_error:
                    logger.warning(connection_error)
                    time.sleep(waiting)
                    continue
                break

        return inner
    

    @retry
    def do_get_request(self, url):
        response = requests.get(
            url=url,
            headers=self.headers
        )
        
        time.sleep(1)

        return response


    def get_houses_links(self):
        houses_links = []

        logger.info('Getting houses links...')

        if self.max_house_cnt is not None:
            for page_number in tqdm(range(1, self.max_house_cnt+1), file=sys.stdout):
                response = self.do_get_request(url=self.main_link.format(page_number=page_number))
                soup = BeautifulSoup(response.text, 'html.parser')
                pred = soup.find_all('a', href=re.compile("suburban"), class_='_93444fe79c--link--VtWj6')
                loop_list = [tag.get('href') for tag in pred]
                houses_links += loop_list
        
        else:
            for page_number in tqdm(range(1, self.max_pages_cnt+1), file=sys.stdout):
                response = self.do_get_request(url=self.main_link.format(page_number=page_number))
                soup = BeautifulSoup(response.text, 'html.parser')
                pred = soup.find_all('a', href=re.compile("suburban"), class_='_93444fe79c--link--VtWj6')
                loop_list = [tag.get('href') for tag in pred]
                houses_links += loop_list

        houses_links = list(set(houses_links))

        return houses_links


    def parse_houses_data(self):
        houses_links = self.get_houses_links()

        if self.max_house_cnt is not None:
            houses_links = houses_links[:self.max_house_cnt]

        cian_house_id_list = [link.split('/')[-2] for link in houses_links]
        dataset = pd.DataFrame({
            'link': houses_links,
            'cian_house_id': cian_house_id_list
        })
        
        logger.info('Parsing data...')
        for link in tqdm(houses_links, file=sys.stdout):
            response = self.do_get_request(url=link)
            const.status_codes.append(response.status_code)
            soup = BeautifulSoup(response.text, 'html.parser')


            description = soup.find_all('span', class_=const.description_class_span)
            description = [tag.text for tag in description]
            if len(description) != 0:
                description = description[0]
                const.descriptions.append(description)
            else:
                const.descriptions.append(np.nan)
            

            general_space_value = soup.find_all('span', class_=const.general_space_value_class_span)
            general_space_value = [tag.text for tag in general_space_value]

            general_space_name = soup.find_all('span', class_=const.general_space_name_class_span)
            general_space_name = [tag.text for tag in general_space_name]
            
            if len(general_space_name) != 0:
                if general_space_name.__contains__('Общая площадь'):
                    house_space = general_space_value[general_space_name.index('Общая площадь')]
                    const.house_spaces.append(house_space)
                else:
                    const.house_spaces.append(np.nan)
                
                if general_space_name.__contains__('Участок'):
                    yard_space = general_space_value[general_space_name.index('Участок')]
                    const.yard_spaces.append(yard_space)
                else:
                    const.yard_spaces.append(np.nan)

                if general_space_name.__contains__('Этажей в доме'):
                    floors_cnt = general_space_value[general_space_name.index('Этажей в доме')]
                    const.floors_cnts.append(floors_cnt)
                else:
                    const.floors_cnts.append(np.nan)

            else:
                const.house_spaces.append(np.nan)
                const.yard_spaces.append(np.nan)
                const.floors_cnts.append(np.nan)
            


            pledge = soup.find_all('p', class_=const.pledge_class_p)
            pledge = [tag.text for tag in pledge]

            if len(pledge) != 0:
                pledge = pledge[0]
                const.pledges.append(pledge)
            else:
                const.pledges.append(np.nan)
            

            address = soup.find_all('a', class_=const.address_class_a)
            address = [tag.text for tag in address]

            if len(address) != 0:
                address = ', '.join(address)
                const.address_.append(address)
            else:
                const.address_.append(np.nan)
        

            about_house = soup.find_all('div', class_=const.about_house_class_div)
            about_house = [tag.text for tag in about_house]

            if len(about_house) != 0:
                about_house = [re.sub(r'([А-Я])', r' \1', string).split() for string in about_house]
                about_house = [', '.join(string) for string in about_house]
                about_house = ', '.join(about_house)

                const.about_houses.append(about_house)
            else:
                const.about_houses.append(np.nan)
        
        dataset['description'] = const.descriptions
        dataset['status_codes'] = const.status_codes
        dataset['house_space'] = const.house_spaces
        dataset['yard_space'] = const.yard_spaces
        dataset['floors_cnt'] = const.floors_cnts
        dataset['pledge'] = const.pledges
        dataset['address'] = const.address_ 
        dataset['about_house'] = const.about_houses

        logger.success(f'Data successfully parsed!\nFirst 5 rows:\n{dataset.head()}')
        
        return dataset



# if __name__ == '__main__':
#     parser = CianParser(max_house_cnt=2)
#     df = parser.parse_houses_data()


