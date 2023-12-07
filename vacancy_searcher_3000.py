import os

# ищем только вакансии где есть такие слова (поиск от hh, оэтому похожие слова тоже попадают)
# vacancies_to_look_in_name = ['Аналитик','Analyst','Data Scientist',
#                             'Data Science','ML','LLM',
#                             'Machine Learning','прогнозирование','анализ']

vacancies_to_look_in_name = str(os.getenv('VACANCIES_TO_LOOK')).split(',')



# указываем в каких странах мы заинтересованы только для удаленки, и в каких - согласны на любой формат
# countries_and_schedule = {'remote':[113, 5, 16], 'not_given':[40, 97, 9, 48, 1001, 28]}
# 'area': 113 Россия; 'area': 40 Казахстан; 5 и 16 - Украина и Беларусь; остальное - разные другие страны

countries_and_schedule = str(os.getenv('COUNTRIES')).split(',')


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

remote_words = str(os.getenv('EXCLUDE_WORDS')).split(',')

# число календарных дней за которое подтягиваем историю загрузки вакансий, брала с запасом, чтобы ничего не упустить, 
# но большинство вакансий повторяются, так что на увеличении времени это не сильно сказывается (начиная со второго прогона кода)
days_to_look = 2

# т.к. я искала 9 вакансий по 9 разным странам, плюс страны для удаленки прогоняются дважды, 
# то у меня выходило 108 запросов, и при прохождении каждых 10 код выдает print, чтобы понимать сколько осталось
print_every_N_steps = 10

import requests
import json
import time
import pandas as pd


print('VACANCIES_TO_LOOK:' + vacancies_to_look_in_name)
print('COUNTRIES:' + countries_and_schedule)
print('REMOTE:' + remote_words)
print('EXCLUDE_WORDS:' + remote_words)

quit()

vacancies_to_look_in_name = ['NAME:'+x for x in vacancies_to_look_in_name]
n_vacancies = len(vacancies_to_look_in_name)
all_countries = sum(list(list(countries_and_schedule.values())+[countries_and_schedule['remote']]), [])
n_countries = len(all_countries)
countries_iteration = sum([[x]*n_vacancies for x in all_countries],[])
n_remote = len(countries_and_schedule['remote'])
all_schedules = ['remote']*n_remote*n_vacancies+[None]*\
                (n_countries-n_remote)*n_vacancies
remote_words_there = 0


def getPage(page = 0, vacancy_type = 0):

    all_params = {
        'text': vacancies_to_look_in_name*n_countries, # Текст поиска
        'schedule': all_schedules,
        'period': [days_to_look]*n_vacancies*n_countries, # 1 - за сутки; 3 - за 3 дня, 7 - за неделю
        'area': countries_iteration, 
        'page': [page]*n_vacancies*n_countries, # Индекс страницы поиска на HH
        'per_page': [100]*n_vacancies*n_countries # Кол-во вакансий на 1 странице
    }

    params = {x:all_params[x][vacancy_type] for x in all_params.keys()}

    req = requests.get('https://api.hh.ru/vacancies', params) # Посылаем запрос к API
    data = req.content.decode() # Декодируем его ответ, чтобы Кириллица отображалась корректно
    req.close()
    return data

all_v=[]
try:
    all_vc = pd.read_csv('all_vacancies.csv')
except:
    all_vc = pd.DataFrame(columns=['vacancy_url'])
new_df = pd.DataFrame(columns=['name','exp','url','descr','sch','loc'])
try:
    for dir in ['docs/vacancies', 'docs/pagination']:
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
except:
    pass
# чтобы видеть целиком описание вакансии
pd.set_option('display.max_colwidth', 10000)

# def pretty_print(df):
#     return display( HTML( df.style.set_properties(**{'text-align': 'left'}).to_html().replace("\\n  <strong>","<br> <strong>").replace("<strong>","<br> <strong>").replace("\\n","<br> ⏺") ) )



# проходимся по всем типам вакансий
for i in range(n_vacancies*n_countries):
    # проходимся по всем страницам поиска
    for page in range(0, 100):
        # Преобразуем текст ответа запроса в справочник Python
        jsObj = json.loads(getPage(page, i))
        
        # Сохраняем файлы в папку {путь до текущего документа со скриптом}\docs\pagination
        # Определяем количество файлов в папке для сохранения документа с ответом запроса
        # Полученное значение используем для формирования имени документа
        nextFileName = './docs/pagination/{}.json'.format(len(os.listdir('./docs/pagination')))
        
        # Создаем новый документ, записываем в него ответ запроса, после закрываем
        f = open(nextFileName, mode='w', encoding='utf8')
        f.write(json.dumps(jsObj, ensure_ascii=False))
        f.close()
        
        # Проверка на последнюю страницу, если вакансий меньше 10000
        if (jsObj['pages'] - page) <= 1:
            break
        
        # Необязательная задержка, но чтобы не нагружать сервисы hh, оставим
        time.sleep(0.25)

    # проходимся по всем вакансиям
    for fl in os.listdir('./docs/pagination'):
        
        # Открываем файл, читаем его содержимое, закрываем файл
        f = open('./docs/pagination/{}'.format(fl), encoding='utf8')
        jsonText = f.read()
        f.close()
        
        # Преобразуем полученный текст в объект справочника
        jsonObj = json.loads(jsonText)
        
        # Получаем и проходимся по непосредственно списку вакансий
        for v in jsonObj['items']:
            if (v['url'] not in list(all_vc['vacancy_url'])) and (v['url'] not in all_v):
            
                # Обращаемся к API и получаем детальную информацию по конкретной вакансии
                all_v.append(v['url'])
                req = requests.get(v['url'])
                data = req.content.decode()
                req.close()
                
                # Создаем файл в формате json с идентификатором вакансии в качестве названия
                # Записываем в него ответ запроса и закрываем файл
                fileName = './docs/vacancies/{}.json'.format(v['id'])
                f = open(fileName, mode='w', encoding='utf8')
                f.write(data)
                f.close()
                
                time.sleep(0.25)
            else:
                pass

    # добавляем в датафрейм
    list_files = os.listdir('./docs/vacancies')
    for vacancy in list_files:
        f = open('./docs/vacancies/{}'.format(vacancy), encoding='utf8')
        jsonText = f.read()
        f.close()
        jsonObj = json.loads(jsonText)

        if i >= n_vacancies*n_countries:
            remote_words_there=1 if any(word in jsonObj['description'].lower() for word in remote_words) else 0

        if remote_words_there or (i < n_vacancies*(n_countries-n_remote)):
            if not any(word in jsonObj['name'].lower() for word in exclude_words_IN_NAME):
                stri = jsonObj['description']
                # stri = stri.replace('<strong>','\033[1m')
                # stri = stri.replace('</strong>','\033[0m')
                stri = stri.replace('</li> <li>','\\n')
                stri = stri.replace('<ul> <li>','\\n')
                stri = stri.replace('</li>','\\n')
                stri = stri.replace('</ul>','')

                new_df.loc[len(new_df)] = [jsonObj['name'], 
                                    jsonObj['experience']['id'],
                                    jsonObj['alternate_url'], 
                                    stri,
                                    jsonObj['schedule']['id'],
                                    jsonObj['area']['name']]

    # удаляем файлы
    for dir in ['docs/vacancies', 'docs/pagination']:
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

    # отслеживаем работу
    if (i%print_every_N_steps==0)&(len(str(n_vacancies*n_countries - i))>1):
        if n_vacancies*n_countries - i >= 100:
            print('осталось '+str(n_vacancies*n_countries - i)+' типов', end='')
        else:
            print('осталось '+str(n_vacancies*n_countries - i)+' типов вакансий', end='')
        print('\r', end='')

print('\n\nВсего '+str(len(new_df))+' новых вакансий')