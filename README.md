# FEFU-applicants

Данный срипт __формирует список поступивших абитуриентов__ в высшее учебное заведение "ДВФУ".
На основе сформированного списка __даёт информацию о проходных баллах__ по специальностям.  


## Установка  

Скачайте архив с исходным кодом. В нём находятся два файла с python скриптом и файл с библиотеками:

- fefu_colab.ipynb 
- fefu_data.py
- requirements.txt


## Работа со скриптами

> Для выполнения некоторых ячеек (в случае использования ipynb версии) или всего кода целиком (py версия) может потребоваться определённое кол-во времени. Поэтому не стоит переживать, если выполнение длится больше нескольких минут.  


### fefu_colab

fefu_colab.ipynb - файл для облачного сервиса Google Colaboratory. В нём вы можете изучить и проанализировать полученные данные, а в разделе __Сохранение данных__ сохранить их. 

Для начала работы с данным файлом проделайте ряд следующих шагов:

1. Перейдите на сайт [Google Colab](https://colab.research.google.com/?utm_source=scs-index)
2. Зарегистрируйтесь или войдите в аккаунт
3. Нажмите на кнопку __Файл__ в верхней панели
4. В выпадающем списке выберите __Открыть блокнот__
5. Загрузите файл FEFU.ipynb

Для работы со скриптом необходимо установить зависимости. Они записаны в файле __requirements.txt__ . Добавьте данный файл во вкладку __Файлы__ (логотип папки в левой части экрана) и используйте следующий код для установки: `!pip install -r requirements.txt`

> Далее уточнения по некоторым строкам кода

---

В данной ячейки кода необходимо выбрать категорию мест, абитуриенты которой будут подгружаться:
- __Бюджетная основа__ - бюджетные места;
- __Полное возмещение затрат__ - платные места .

```python
# Выберите одну из категорий источника финансирования: 'Бюджетная основа', 'Полное возмещение затрат'
finance = input()
```

---

Выполнив следующую ячейку, можно проверить: поступил ли абитуриент в ВУЗ. 

```python
snils = input('Введите снилс в формате xxx-xxx-xxx xx или уникальный код: ')
students_received[students_received['СНИЛС'] == snils]
```

---

Данные ячейки сохраняют полученные и обработанные данные в формате _xlsx_. После их выполнения таблицы можно найти во вкладке __Файлы__ (логотип папки в левой части экрана).

```python
data_students.to_excel('students.xlsx')


writer = pd.ExcelWriter('passing_score_final.xlsx', engine='xlsxwriter')

for category in passing_score['Категория'].unique():
    passing_score[passing_score['Категория'] == category].to_excel(writer, sheet_name=category)

writer.close()
```

---

После выполнения раздела __Алгоритм__, вы можете посмотреть на данные и проанализировать их:

- __data_students__ - DataFrame с информацией о всех абитуриентах на выбранную ранее категорию мест __finance__;
- __students_received__ - DataFrame с поступившими абитуриентами;
- __df_students__ - DataFrame с не поступившими абитуриентами;
- __passing_score__ - DataFrame с проходными баллами на выбранную ранее категорию мест __finance__ 

---

### fefu_data.py

Данный скрипт создан для сбора данных, выполнения алгоритма, отбирающего поступивших абитуриентов, и сохранение данной информации в фалы. 

Для начала работы необходимо: 

1. Создать виртуальное окружение
2. Установить зависимости `pip install -r requirements.txt`

После установки зависимости можно приступать к выполнению скрипта. 

__Результат выполнения__  
После выполнения данного скрипта в директорию загрузятся шесть файлов: 

- __count_place_budget.pkl__ /__count_place_paid.pkl__- данные о кол-во мест на бюджетной /платной основе;
- __passing_score_budget.xlsx__ /__passing_score_paid.xlsx__- данные о проходных баллах на бюджетную/ платную основу;
- __students_received_budget.xlsx__ /__students_received_paid.xlsx__- Excel таблица с поступившими абитуриентами на бюджетной /платной основе. 

---

## Авторы проекта

- __[Eduard Ganzha](https://github.com/deep-learning-engenear)__
- __[davikch](https://github.com/davikch)__
