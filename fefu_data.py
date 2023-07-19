""" Импорт библиотек """

import requests
import pandas as pd
import numpy as np
import pickle


""" Сбор данных """


def get_speciality(url, finance):
    """ Напишем функцию для получения списка специальностей c источником финансирования
                         - finance ('Бюджетная основа', 'Полное возмещение затрат').
    """

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


def get_data(url, department, finance):
    """Сбор данных о поступающих абитуриентах на определенное направление - department. """
    global data_students, count_place

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

    return data_students, count_place


def data_loading(finance):
    """ Загрузка данных с сайта """
    url_data = 'https://www.dvfu.ru/bitrix/services/main/' \
               'ajax.php?mode=class&c=dvfu%3Aadmission.spd.new&action=getStudents'
    url_speciality = "https://www.dvfu.ru/bitrix/services/main/" \
                     "ajax.php?mode=class&c=dvfu%3Aadmission.spd.new&action=getTrainingDirectionList"

    # Загрузка специальностей
    fefu_speciality = get_speciality(url_speciality, finance)

    # Загрузка данных об абитуриентах
    for speciality in fefu_speciality:
        get_data(url_data, speciality, finance)


""" Алгоритм """


def incoming_students(category):
    """ Формирование DataFrame с поступившими абитуриентами
        по определенной специальности
    """
    global students_received, count_place, data_students

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


"""Для бюджетной основы сначала определяем поступивших абитуриентов на общих основаниях, затем на квотные места, 
   оставшиеся места переходят в места 'На общих основаниях', дополняем списки 'На общих основаниях'.
   Для платной основы всё легче, так как присутствуют только места 'На общих основаниях'.
"""


def get_students_received(finance):
    """ Формирование DataFrame с поступившими абитуриентами """
    global count_place

    # Определяем поступивших абитуриентов на общих основаниях
    incoming_students('На общих основаниях')

    if finance == 'Бюджетная основа':
        kvota = ['Имеющие особое право', 'Отдельная квота', 'Целевой прием']

        for category in kvota:
            incoming_students(category)

        # Добавляем оставшиеся места в общие основания
        for category in kvota:
            for speciality in count_place[category]:
                count_place['На общих основаниях'][speciality] += count_place[category][speciality]
                count_place[category][speciality] = 0

        # Дополняем поступивших абитуриентов на общих основаниях
        incoming_students('На общих основаниях')

    else:
        incoming_students('На общих основаниях')


if __name__ == "__main__":
    type_place = {'Бюджетная основа': 'budget',
                  'Полное возмещение затрат': 'paid'}

    for finance in type_place:
        # Словарь для хранения информации о кол-во мест
        count_place = {}
        # Будущий DataFrame для хранения информации об абитуриентах
        data_students = {'СНИЛС': [], 'Специальность': [], 'Балл': [], 'Приоритет': [], 'БВИ': [], 'Категория': []}

        # Загрузим данные
        data_loading(finance)
        # Удалим дубликаты
        data_students = pd.DataFrame(data_students).drop_duplicates()

        # Создадим переменную для хранения поступивших абитуриентов
        students_received = pd.DataFrame({'СНИЛС': [], 'Специальность': [], 'Балл': [],
                                          'Приоритет': [], 'БВИ': [], 'Категория': []})
        # Сформируем DataFrame с поступившими абитуриентами
        get_students_received(finance)

        # Формирование DataFrame с проходными баллами
        passing_score = students_received[students_received['БВИ'] == False] \
            .groupby(['Специальность', 'Категория'], as_index=False) \
            .agg({'Балл': min}).sort_values(by='Категория')

        # Сохраняем кол-во мест
        with open(f'./count_place_{type_place[finance]}.pkl', 'wb') as f:
            pickle.dump(count_place, f)

        # Сохраняем поступивших абитуриентов
        students_received.to_excel(f'./students_received_{type_place[finance]}.xlsx')

        # Сохраняем проходные баллы в файл
        writer = pd.ExcelWriter(f'./passing_score_{type_place[finance]}.xlsx', engine='xlsxwriter')

        for category in passing_score['Категория'].unique():
            passing_score[passing_score['Категория'] == category].to_excel(writer, sheet_name=category)

        writer.close()
