# Импорт библиотек

import requests
import pandas as pd
import numpy as np
import copy

"""#Сбор данных

Напишем функцию для получения списка специальностей c источником финансирования - finance 
                                          ('Бюджетная основа', 'Полное возмещение затрат').
"""


def get_speciality(url, finance):
    user_agent = {
        'user-agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4324.188 Safari/537.36 CrKey/1.54.250320'}
    data = {
        'admissionCampaignType': "Прием на обучение на бакалавриат/специалитет",
        'financingSource': finance,
        'studyForm': "Очная"
    }

    raw = requests.post(url=url, headers=user_agent, params=data).json()
    return raw['data']


"""Напишем функцию, которая будет собирать данные о поступающих на определенное направление - department."""


def get_data(url, department, finance):
    # Словарь ключей для получения кол-во мест
    place = {'Имеющие особое право': 'SpecialQuotaCount',
             'На общих основаниях': 'BudgetQuotaCount',
             'Отдельная квота': 'SeparateQuotaCount',
             'Целевой прием': 'TargetQuotaCount',
             'Полное возмещение затрат': 'ExtraBudgetQuotaCount'}

    user_agent = {
        'user-agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4324.188 Safari/537.36 CrKey/1.54.250320'}
    data = {
        'admissionCampaignType': "Прием на обучение на бакалавриат/специалитет",
        'financingSource': finance,
        'studyForm': "Очная",
        'trainingDirection': department,
        'sortDirection': "sum",
    }

    raw = requests.post(url=url, headers=user_agent, params=data).json()

    for student in raw.get("data"):
        if student['Code'] == '':
            continue

        category = student['Category']

        data_students['СНИЛС'].append(student['Code'])
        data_students['Специальность'].append(department)
        data_students['Приоритет'].append(int(student["SelectedPriority"]))
        data_students['БВИ'].append(student["NoExams"] == 'Y')
        data_students['Категория'].append(category)

        try:
            data_students['Балл'].append(int(student['SumScore']))
        except ValueError:
            data_students['Балл'].append(np.nan)

        if category not in count_place:
            count_place[category] = {}

        if department not in count_place[category]:
            count_place[category][department] = int(student[place[category]])


# Словарь для хранения информации о кол-во мест
count_place = {}
# Будущий DataFrame для хранения информации об абитуриентах
data_students = {'СНИЛС': [], 'Специальность': [], 'Балл': [], 'Приоритет': [], 'БВИ': [], 'Категория': []}

# Выберите одну из категорий источника финансирования: 'Бюджетная основа', 'Полное возмещение затрат'
finance = input(
    'Выберите одну из категорий источника финансирования: "Бюджетная основа", "Полное возмещение затрат": ')

url_speciality = "https://www.dvfu.ru/bitrix/services/main/ajax.php?mode=class&c=dvfu%3Aadmission.spd" \
                 ".new&action=getTrainingDirectionList"
FEFU_speciality = get_speciality(url_speciality, finance)

"""Формирование pandasDataFrame по всем специальностям."""

url_data = 'https://www.dvfu.ru/bitrix/services/main/ajax.php?mode=class&c=dvfu%3Aadmission.spd.new&action=getStudents'

print('Идёт загрузка данных.... \n')
for speciality in FEFU_speciality:
    get_data(url_data, speciality, finance)

data_students = pd.DataFrame(data_students)
print('Размерность полученных  данных: ', data_students.shape)

"""Удалим дубликаты."""

data_students = data_students.drop_duplicates()
print('Размерность после удаления дубликатов: ', data_students.shape, end='\n\n')

"""#Алгоритм

Так как count_place - это словарь словарей, для того чтобы он не изменялся по ходу выполнения программы,
                                                                           сделаем глубокое копирование.
"""

copy_place = copy.deepcopy(count_place)
df_students = data_students.copy()

"""Создадим пустой DataFrame, который будет хранить информацию о поступивших абитуриентах."""

students_received = pd.DataFrame()

"""Напишем функцию, которая будет считать кол-во оставшихся мест на все специальности в определенной категории мест."""


def get_count_place(place, category):
    return sum([place[category][i] for i in place[category]])


"""Посмотрим на общее кол-во мест в категории: На общих основаниях."""

print('Кол-во мест на общих основаниях', get_count_place(copy_place, 'На общих основаниях'), end='\n')

"""Напишем функцию, которая будет формировать DataFrame с поступившими абитуриентами 
                                                 по определенной категории (category)."""


def incoming_students(category):
    global students_received
    global df_students

    start_priority = 1
    old_len = -1

    while len(students_received) != old_len:  # Выполняем цикл до тех пор, пока кол-во поступивших
        old_len = len(students_received)  # абитуриентов не станет равным 0

        for speciality in copy_place[category]:
            # Проверим остались ли места на данную специальность
            if copy_place[category][speciality] == 0:
                continue

            # Формируем DataFrame по специальности и сортируем в порядке убывания
            speciality_data = df_students[
                (df_students['Специальность'] == speciality) & (df_students['Категория'] == category)] \
                .sort_values(by=['БВИ', 'Балл'], ascending=(False, False))
            # Проверяем не пустой ли speciality_data
            if len(speciality_data) == 0:
                continue

            # Делаем выборку из первых абитуриентов и выбираем нужный приоритет
            speciality_data = speciality_data.iloc[:copy_place[category][speciality]]
            speciality_data = speciality_data[
                speciality_data['Приоритет'] == min(start_priority, min(speciality_data['Приоритет']))]
            snils_students = speciality_data['СНИЛС']

            # Обновим оставшееся кол-во мест и добавим абитуриентов в DataFrame поступивших
            copy_place[category][speciality] -= len(speciality_data)
            students_received = pd.concat([students_received, speciality_data])

            # Удаляем из общих данных уже поступивших абитуриентов
            df_students = df_students[
                df_students.apply(lambda row: row['СНИЛС'] not in snils_students.to_list(), axis=1)]

        start_priority += 1


"""Для бюджетной основы сначала определяем поступивших на квотные места абитуриентов, 
   оставшиеся места переходят в места 'На общих основаниях', 
   только после обновления мест определяем поступивших на общих основаниях.
   Для платной основы всё легче, так как присутствуют только места 'На общих основаниях'."""


def get_students_received():
    if finance == 'Бюджетная основа':
        kvota = ['Имеющие особое право', 'Отдельная квота', 'Целевой прием']

        for category in kvota:
            incoming_students(category)

        # Добавляем оставшиеся места в общие основания
        for category in kvota:
            for speciality in copy_place[category]:
                copy_place['На общих основаниях'][speciality] += copy_place[category][speciality]

        # Определяем поступивших абитуриентов на общих основаниях
        incoming_students('На общих основаниях')

    else:
        incoming_students('На общих основаниях')


print('Определение поступивших абитуриентов.... \n')
get_students_received()

"""Проверим размерности данных и кол-во уникальных СНИЛСов (для того чтобы убедится, 
                                              что один абитуриент не попал в наш DataFrame несколько раз)"""

print('Кол-во поступивших абитуриентов: ', students_received.shape)
print('Кол-во уникальных СНИЛСов: ', students_received['СНИЛС'].nunique(), end='\n')

"""Тут можно проверить на какую специальность проходит абитуриент"""

snils = input('Введите снилс в формате xxx-xxx-xxx xx или уникальный код: ')
print(students_received[students_received['СНИЛС'] == snils])

"""Вычислим проходные баллы на специальности"""

passing_score = students_received[students_received['БВИ'] == False] \
    .groupby(['Специальность', 'Категория'], as_index=False) \
    .agg({'Балл': min}).sort_values(by='Категория')

print(passing_score.head(5))

"""#Сохранение данных

Сохраняем собранные данные о всех абитуриентах в Excel таблицу.
"""

print('Сохранение данных... \n')

data_students.to_excel('students.xlsx')
print('Данные о всех абитуриентах сохранены в файл: "students.xlsx"')

"""Сохраним данные о поступивших абитуриентах в Excel таблицу."""

writer = pd.ExcelWriter('passing_score_final.xlsx', engine='xlsxwriter')
print('Данные о всех поступивших абитуриентах сохранены в файл: "passing_score_final.xlsx"')

for category in passing_score['Категория'].unique():
    passing_score[passing_score['Категория'] == category].to_excel(writer, sheet_name=category)

writer.close()
