import os

# число календарных дней за которое подтягиваем историю загрузки вакансий, брала с запасом, чтобы ничего не упустить, 
# но большинство вакансий повторяются, так что на увеличении времени это не сильно сказывается (начиная со второго прогона кода)
days_to_look = 2

user_id = os.getenv('USER_ID')
user_query = os.getenv('QUERY_ID')

db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pw = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')

if ( user_id is None ):  ## external params
    print('No user_id is provided! Aborting...')
    quit()

if ( user_query is None ):  ## external params
    print('No user_query is provided! Aborting...')
    quit()

select_query = """
    SELECT url FROM vacancies where usr_id = %s
    """

get_query = """
    SELECT * FROM querries where usr_id = %s and id = %s
    """

insert_query = """
    INSERT INTO vacancies (usr_id, query_id, url, name, experience, alternate_url, description, schedule, location)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """                                    

import requests
import json
import time
# import pandas as pd
import psycopg2

try:
    # Establish a connection
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_pw,
        host=db_host,
        port="5432"
    )
    print("Connection successful!")

except psycopg2.Error as e:
    print(f"Error connecting to PostgreSQL: {e}")

all_v=[]

with conn.cursor() as cursor:
    cursor.execute(select_query,(user_id))
    for row in cursor.fetchall():
        all_v.append(row[0])
    cursor.close()

# quit()

with conn.cursor() as cursor:
    cursor.execute( get_query,(user_id,user_query) )
    # cursor.execute( get_query,(user_id) )
    for row in cursor.fetchall():
        # print(row)
        vacancies_to_look_in_name=row[2].strip("'").split(',')
        countries=row[3].strip("'").split(',')
        schedule=row[4].strip("'").split(',')
        countries_and_schedule = {'remote':countries, 'all':schedule}
        remote_words=row[5].strip("'").split(',')
        exclude_words_IN_NAME=row[6].strip("'").split(',')
        needed_expirience=row[7].strip("'").split(',')
    cursor.close()

print('VACANCIES_TO_LOOK:', vacancies_to_look_in_name)
# print('COUNTRIES ON SITE:', countries)
# print('COUNTRIES REMOTE:', schedule)
print('COUNTRIES & SCHED:', countries_and_schedule)
print('REMOTE:', remote_words)
print('EXCLUDE_WORDS:', exclude_words_IN_NAME)
print('EXPIRIENCE_NEEDED:', needed_expirience)
print('PROCESSED URLs COUNT:', len(all_v))

vacancies_to_look_in_name = ['NAME:'+x for x in vacancies_to_look_in_name]
n_vacancies = len(vacancies_to_look_in_name)
vacancies_request = ' OR '.join(vacancies_to_look_in_name) # TODO: ADD EXCLUDE WORDS IN QUERRY
remote_words_there = 0


def getPage(schedule = 'remote', country = 113, page = 0):

    all_params = {
        'text': vacancies_request, # Текст поиска
        'schedule': schedule,
        'period': days_to_look, # 1 - за сутки; 3 - за 3 дня, 7 - за неделю
        'area': country, # one area id for each querry
        'page': page, # Индекс страницы поиска на HH
        'per_page': 100 # Кол-во вакансий на 1 странице
    }
    req = requests.get('https://api.hh.ru/vacancies', all_params) # Посылаем запрос к API
    data = req.content.decode() # Декодируем его ответ, чтобы Кириллица отображалась корректно
    req.close()
    return data

def getVacnciesByType( l_countries, schedule = 'remote' ):
    step = 0
    new_vacancy_count=0
    # проходимся по всем типам вакансий
    for country in l_countries:
        # проходимся по всем страницам поиска
        for page in range(0, 10):
            # Преобразуем текст ответа запроса в справочник Python
            jsObj = json.loads(getPage(schedule, country, page))
            
            # print( 'Items: ', jsObj['items'] )
            # print( 'Pages: ', jsObj['pages'] )

            for v in jsObj['items']:
                if (v['url'] not in all_v): 
                
                    # Обращаемся к API и получаем детальную информацию по конкретной вакансии
                    all_v.append(v['url'])
                    req = requests.get(v['url'])
                    data = req.content.decode()
                    req.close()
                    
                    jsonObj = json.loads(data)

                    # remote_words_there=1 #if any(word in jsonObj['description'].lower() for word in remote_words) else 0

                    # if remote_words_there:

                    if jsonObj['experience']['id'] in needed_expirience:
                        if not any(word in jsonObj['name'].lower() for word in exclude_words_IN_NAME):

                            stri = jsonObj['description']
                            # stri = stri.replace('<strong>','\033[1m')
                            # stri = stri.replace('</strong>','\033[0m')
                            stri = stri.replace('</li> <li>','\n')
                            stri = stri.replace('<ul> <li>','\n')
                            stri = stri.replace('</li>','\n')
                            stri = stri.replace('</ul>','')


                            # (user_id,query_id,url,name,experience,alternate_url,description,schedule,location)
                            # print('Vac name: ', jsonObj['name'])
                            # print('Exp: ', jsonObj['experience']['id'])
                            # print('url: ', jsonObj['alternate_url'])
                            # print('Desc: ', stri)     
                            # print('Sched: ', jsonObj['schedule']['id'])
                            # print('Location: ', jsonObj['area']['name'])

                            vacancy_data = (
                                user_id,
                                user_query,
                                v['url'],
                                jsonObj['name'], 
                                jsonObj['experience']['id'],
                                jsonObj['alternate_url'],   
                                stri,                          
                                jsonObj['schedule']['id'],
                                jsonObj['area']['name']
                            )

                            # print('Ready insert data: ', vacancy_data)

                            with conn.cursor() as cursor:
                                cursor.execute(insert_query, vacancy_data)
                                time.sleep(0.25)
                                conn.commit()
                                cursor.close()
                                
                            new_vacancy_count += 1
                            time.sleep(0.25)
                    
                else:
                    pass

            # Необязательная задержка, но чтобы не нагружать сервисы hh, оставим
            time.sleep(0.25)

            # Проверка на последнюю страницу, если вакансий меньше 10000
            if (jsObj['pages'] - page) <= 1:
                break            
                        
    print('\n\n Всего '+str(new_vacancy_count)+' новых вакансий по запросу ' + schedule)

getVacnciesByType(countries,'fullDay')
getVacnciesByType(countries,'remote')

getVacnciesByType(schedule,'remote')

conn.close()