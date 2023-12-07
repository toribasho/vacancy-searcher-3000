import os

# ищем только вакансии где есть такие слова (поиск от hh, оэтому похожие слова тоже попадают)
# vacancies_to_look_in_name = ['Аналитик','Analyst','Data Scientist',
#                             'Data Science','ML','LLM',
#                             'Machine Learning','прогнозирование','анализ']

vacancies_to_look_in_name = str(os.getenv('VACANCIES_TO_LOOK')).split(',')



# указываем в каких странах мы заинтересованы только для удаленки, и в каких - согласны на любой формат
# countries_and_schedule = {'remote':[113, 5, 16], 'not_given':[40, 97, 9, 48, 1001, 28]}
# 'area': 113 Россия; 'area': 40 Казахстан; 5 и 16 - Украина и Беларусь; остальное - разные другие страны

countries = str(os.getenv('COUNTRIES')).split(',')
schedule = str(os.getenv('SCHEDULE')).split(',')

countries_and_schedule = {'remote':countries, 'not_given':schedule}

# те страны которые только для удаленки - берем во-первых вакансии где указан удаленный режим, 
# во-вторых смотрим ВСЕ режимы, и отбираем вакансии где в описании есть следующие слова:
# remote_words = ['удалён','удален','за пределами рф','дистанцион','из дома','remote',
#                 'relocation','релокаци','из другой страны','из любой точки мира','online']

remote_words = str(os.getenv('REMOTE')).split(',')

# если эти слова есть в названии вакансии, то эти вакансии автоматически исключаем из просмотра, чтобы не тратить время
# exclude_words_IN_NAME = ['1c', '1с', 'системн', 'финансов', 'senior', 'lead', 'старший', 'ведущий',
#                          'эксперт', 'автор', 'developer', 'лаборант', 'руководитель', 'менеджер',
#                          'бизнес', 'экономист', 'химик', 'начальник', 'главный', 'медсестра',
#                          'спикер', 'архитектор', 'бухгалтер', 'директор', 'business', 'научный', 
#                          'линии поддержки', 'ozon', 'wildberries', 'маркетплейс', 'system', 'писатель',
#                          'безопасность','куратор','golang','оператор','financial','информационной безопасности']

exclude_words_IN_NAME = str(os.getenv('EXCLUDE_WORDS')).split(',')

# число календарных дней за которое подтягиваем историю загрузки вакансий, брала с запасом, чтобы ничего не упустить, 
# но большинство вакансий повторяются, так что на увеличении времени это не сильно сказывается (начиная со второго прогона кода)
days_to_look = 1

# т.к. я искала 9 вакансий по 9 разным странам, плюс страны для удаленки прогоняются дважды, 
# то у меня выходило 108 запросов, и при прохождении каждых 10 код выдает print, чтобы понимать сколько осталось
print_every_N_steps = 10

import requests
import json
import time
import pandas as pd
import psycopg2


all_v=[]
conn = psycopg2.connect("host=postgres_container dbname=public user=tori password=112233" )
with conn.cursor() as cursor:
    cursor.execute("SELECT url FROM vacancies")
    for row in cursor.fetchall():
        all_v.append(row["url"])

# with conn.cursor() as cursor:
#     cursor.execute("SELECT url FROM vacancies")
#     for row in cursor.fetchall():
#         all_v.append(row["url"])

cur.close()

print('VACANCIES_TO_LOOK:', vacancies_to_look_in_name)
print('COUNTRIES:', countries_and_schedule)
print('REMOTE:', remote_words)
print('EXCLUDE_WORDS:', exclude_words_IN_NAME)
print('PROCESSED URLs COUNT:', len(all_v))

quit()

vacancies_to_look_in_name = ['NAME:'+x for x in vacancies_to_look_in_name]
n_vacancies = len(vacancies_to_look_in_name)
vacancies_request = ' OR '.join(vacancies_to_look_in_name) # TODO: ADD EXCLUDE WORDS IN QUERRY
n_countries = len(countries)
n_remote = len(countries_and_schedule['remote'])
remote_words_there = 0


def getPage(country = 113, page = 0):

    all_params = {
        'text': vacancies_request, # Текст поиска
        'schedule': 'remote',
        'period': days_to_look, # 1 - за сутки; 3 - за 3 дня, 7 - за неделю
        'area': country, # one area id for each querry
        'page': page, # Индекс страницы поиска на HH
        'per_page': 100 # Кол-во вакансий на 1 странице
    }

    req = requests.get('https://api.hh.ru/vacancies', all_params) # Посылаем запрос к API
    data = req.content.decode() # Декодируем его ответ, чтобы Кириллица отображалась корректно
    req.close()
    return data

# чтобы видеть целиком описание вакансии
pd.set_option('display.max_colwidth', 10000)

step = 0
# проходимся по всем типам вакансий
for country in range(n_countries):
    # проходимся по всем страницам поиска
    for page in range(0, 100):
        # Преобразуем текст ответа запроса в справочник Python
        jsObj = json.loads(getPage(country, page))
        
        # Проверка на последнюю страницу, если вакансий меньше 10000
        if (jsObj['pages'] - page) <= 1:
            break

        for v in jsObj['items']:
            if (v['url'] not in list(all_vc['vacancy_url'])) and (v['url'] not in all_v): 
            
                # Обращаемся к API и получаем детальную информацию по конкретной вакансии
                all_v.append(v['url'])
                req = requests.get(v['url'])
                data = req.content.decode()
                req.close()
                
                jsonObj = json.loads(data)

                remote_words_there=1 if any(word in jsonObj['description'].lower() for word in remote_words) else 0

                stri = jsonObj['description']
                # stri = stri.replace('<strong>','\033[1m')
                # stri = stri.replace('</strong>','\033[0m')
                stri = stri.replace('</li> <li>','\\n')
                stri = stri.replace('<ul> <li>','\\n')
                stri = stri.replace('</li>','\\n')
                stri = stri.replace('</ul>','')

                with conn.cursor() as cursor:
                    cursor.execute("""INSERT INTO vacancies (url,name,experience,alternate_url,schedule,location,added,description) 
                            VALUES (%s, %s, %s, %s, %s, current_timestamp, %s); 
                            """, 
                            (jsonObj['name'], 
                            jsonObj['experience']['id']),
                            jsonObj['alternate_url'],                             
                            jsonObj['schedule']['id'],
                            jsonObj['area']['name'],
                            stri)
                
                
                time.sleep(0.25)
            else:
                pass
        
        
        # Необязательная задержка, но чтобы не нагружать сервисы hh, оставим
        time.sleep(0.25)

    # отслеживаем работу
    if (step%print_every_N_steps==0)):
        if n_vacancies*n_countries - i >= 100:
            print('осталось '+str(n_vacancies*n_countries - i)+' типов', end='')
        else:
            print('осталось '+str(n_vacancies*n_countries - i)+' типов вакансий', end='')
        print('\r', end='')
    step+=1

print('\n\n Всего '+str(len(new_df))+' новых вакансий')

conn.close()