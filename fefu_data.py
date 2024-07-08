""" Импорт библиотек """

import requests
import pandas as pd
import numpy as np
import pickle


""" Сбор данных """


def get_speciality(url):
    """ Напишем функцию для получения списка специальностей c источником финансирования
                         - finance 'Бюджет'.
    """

    user_agent = {
        'user-agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4324.188 Safari/537.36 CrKey/1.54.250320'}

    data = {
        'admissionCampaignType': "Прием на обучение на бакалавриат/специалитет",
        'financingSource' : 'Бюджет',
        'studyForm': "Очная"
    }

    raw = requests.post(url=url, headers=user_agent, params=data).json()
    return raw['data']


def get_data(url, department, data_students, count_place, orig):
    """Сбор данных о поступающих абитуриентах на определенное направление - department. """

    # Словарь ключей для получения кол-во мест
    place = {'Особая квота': 'SpecialQuotaCount',
             'Основные места': 'BudgetQuotaCount',
             'Отдельная квота': 'SeparateQuotaCount',
             'Целевая квота': 'TargetQuotaCount',
             'Полное возмещение затрат': 'ExtraBudgetQuotaCount'}

    user_agent = {
        'user-agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4324.188 Safari/537.36 CrKey/1.54.250320'}
    data = {
        'admissionCampaignType': "Прием на обучение на бакалавриат/специалитет",
        'financingSource': 'Бюджет',
        'studyForm': "Очная",
        'trainingDirection': department,
        'sortDirection': "sum",
        }

    raw = requests.post(url=url, headers=user_agent, params=data).json()

    for student in raw.get("data"):
        if student['Code'] == '':
            continue

        if orig == 'Y' and student['AtestOrig'] == 'N':
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

    return data_students, count_place


def data_loading(data_students, count_place, orig):
    """ Загрузка данных с сайта """

    url_data =  "https://www.dvfu.ru/bitrix/services/main/ajax.php?admissionCampaignType=%D0%9F%D1%80%D0%B8%D0%B5%D0%BC%20%D0%BD%D0%B0%20%D0%BE%D0%B1%D1%83%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%BD%D0%B0%20%D0%B1%D0%B0%D0%BA%D0%B0%D0%BB%D0%B0%D0%B2%D1%80%D0%B8%D0%B0%D1%82%2F%D1%81%D0%BF%D0%B5%D1%86%D0%B8%D0%B0%D0%BB%D0%B8%D1%82%D0%B5%D1%82&financingSource=%D0%91%D1%8E%D0%B4%D0%B6%D0%B5%D1%82&studyForm=%D0%9E%D1%87%D0%BD%D0%B0%D1%8F&trainingDirection=01.03.02%20%D0%9F%D1%80%D0%B8%D0%BA%D0%BB%D0%B0%D0%B4%D0%BD%D0%B0%D1%8F%20%D0%BC%D0%B0%D1%82%D0%B5%D0%BC%D0%B0%D1%82%D0%B8%D0%BA%D0%B0%20%D0%B8%20%D0%B8%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%82%D0%B8%D0%BA%D0%B0&sortDirection=sum&enrolled=N&sendorig=N&topprior=N&mode=class&c=dvfu%3Aadmission.spd&action=getStudents"
    url_speciality = "https://www.dvfu.ru/bitrix/services/main/ajax.php?admissionCampaignType=%D0%9F%D1%80%D0%B8%D0%B5%D0%BC%20%D0%BD%D0%B0%20%D0%BE%D0%B1%D1%83%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%BD%D0%B0%20%D0%B1%D0%B0%D0%BA%D0%B0%D0%BB%D0%B0%D0%B2%D1%80%D0%B8%D0%B0%D1%82%2F%D1%81%D0%BF%D0%B5%D1%86%D0%B8%D0%B0%D0%BB%D0%B8%D1%82%D0%B5%D1%82&financingSource=%D0%91%D1%8E%D0%B4%D0%B6%D0%B5%D1%82&studyForm=%D0%9E%D1%87%D0%BD%D0%B0%D1%8F&mode=class&c=dvfu%3Aadmission.spd&action=getTrainingDirectionList"

    # Загрузка специальностей
    fefu_speciality = get_speciality(url_speciality)
    # Загрузка данных об абитуриентах
    for speciality in fefu_speciality:
        data_students, count_place = get_data(url_data, speciality, data_students, count_place, orig)

    return data_students, count_place


""" Алгоритм """


def incoming_students(category, students_received, count_place, data_students):
    """ Формирование DataFrame с поступившими абитуриентами
        по определенной специальности
    """

    not_students = 0
    while not_students != len(count_place[category]):  # Выполняем цикл до тех пор, пока в
        not_students = 0  # не останется абитуриентов на все специальности

        for speciality in count_place[category]:
            # Проверим остались ли места на данную специальность
            if count_place[category][speciality] == 0:
                not_students += 1
                continue

            # Формируем DataFrame по специальности и сортируем в порядке убывания
            speciality_data = data_students[
                (data_students['Специальность'] == speciality) & (data_students['Категория'] == category)] \
                .sort_values(by=['БВИ', 'Балл'], ascending=(False, False))

            # Делаем выборку из первых абитуриентов
            speciality_data = speciality_data.iloc[:count_place[category][speciality]]
            # Проверяем не пустой ли speciality_data
            if len(speciality_data) == 0:
                not_students += 1
                continue

            # Перебираем проходящих на данную специальность абитуриентов
            for i, student in speciality_data.iterrows():
                # Проверяем есть ли уже абитуриент в DataFrame, поступивших абитуриентов
                if student['СНИЛС'] in students_received['СНИЛС'].to_list():
                    # Проверяем меньше ли новый приоритет
                    if student['Приоритет'] < \
                            students_received[students_received['СНИЛС'] == student['СНИЛС']]['Приоритет'].values[0]:

                        # Так как значение нового приоритета меньше,
                        # убираем абитуриента со старой специальности и добавляем в новую
                        index = students_received[students_received['СНИЛС'] == student['СНИЛС']].index
                        count_place[students_received.loc[index, 'Категория'].values[0]][
                            students_received.loc[index, 'Специальность'].values[0]] += 1

                        # Удаление информацию об абитуриенте
                        students_received.drop(labels=[index[0]], inplace=True)

                    # Если значение исходного приоритета меньше нового, пропускаем абитуриента
                    else:
                        data_students.drop(labels=[i], inplace=True)
                        continue

                # Добавляем информацию о новом, поступившем абитуриенте
                item = pd.DataFrame([student])
                item["БВИ"] = item["БВИ"].astype("boolean")
                students_received = pd.concat([students_received, item])

                # Обновляем кол-во мест
                count_place[student['Категория']][student['Специальность']] -= 1

                # Удаляем из общих данных уже поступивших абитуриентов
                data_students.drop(labels=[i], inplace=True)

    return students_received


"""Для бюджетной основы сначала определяем поступивших абитуриентов на общих основаниях, затем на квотные места, 
   оставшиеся места переходят в места 'Основные места', дополняем списки 'Основные места'.
"""


def get_students_received(students_received, count_place, data_students):
    """ Формирование DataFrame с поступившими абитуриентами """

    # Определяем поступивших абитуриентов на общих основаниях
    students_received = incoming_students('Основные места', students_received, count_place, data_students)

    kvota = ['Особая квота', 'Отдельная квота', 'Целевая квота']

    for category in kvota:
        students_received = incoming_students(category, students_received, count_place, data_students)

    # Добавляем оставшиеся места в общие основания
    for category in kvota:
        for speciality in count_place[category]:
            count_place['Основные места'][speciality] += count_place[category][speciality]
            count_place[category][speciality] = 0

    # Дополняем поступивших абитуриентов на общих основаниях
    students_received = incoming_students('Основные места', students_received, count_place, data_students)

    return students_received



if __name__ == "__main__":
    finance = 'Бюджет'

    orig = input('Выберите категорию аттестата: "N" - не учитывая наличие оригинала'
                 ', "Y" - только оригинал документа: ')
    assert orig in "YN", "Категория не корректна!"

    # Словарь для хранения информации о кол-во мест
    count_place = {}
    # Будущий DataFrame для хранения информации об абитуриентах
    data_students = {'СНИЛС': [], 'Специальность': [], 'Балл': [], 'Приоритет': [], 'БВИ': [], 'Категория': []}

    # Загрузим данные
    data_students, count_place = data_loading(data_students, count_place, orig)
    # Удалим дубликаты
    data_students = pd.DataFrame(data_students).drop_duplicates()

    # Создадим переменную для хранения поступивших абитуриентов
    students_received = pd.DataFrame({'СНИЛС': [], 'Специальность': [], 'Балл': [],
                                      'Приоритет': [], 'БВИ': [], 'Категория': []})

    # Сформируем DataFrame с поступившими абитуриентами
    students_received = get_students_received(students_received, count_place, data_students)

    # Формирование DataFrame с проходными баллами
    passing_score = students_received[students_received['БВИ'] == False] \
        .groupby(['Специальность', 'Категория'], as_index=False) \
        .agg({'Балл': min}).sort_values(by='Категория')

    # Сохраняем кол-во мест
    with open(f'./count_place_budget.pkl', 'wb') as f:
        pickle.dump(count_place, f)

    # Сохраняем поступивших абитуриентов
    students_received.to_excel(f'./students_received_budget.xlsx')

    # Сохраняем проходные баллы в файл
    writer = pd.ExcelWriter(f'./passing_score_budget.xlsx', engine='xlsxwriter')

    for category in passing_score['Категория'].unique():
        passing_score[passing_score['Категория'] == category].to_excel(writer, sheet_name=category)

    writer.close()
