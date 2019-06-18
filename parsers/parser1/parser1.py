import requests, imgkit, json, random, datetime, time
from bs4 import BeautifulSoup


class parser:

    def assembly_student(self, table, parameter, original_parameter):

        correction = table[1]
        table = table[0]

        result = str(self.head) + '<table cellspacing="0" border="0">'

        for i in table.findAll('colgroup'):
            result += str(i)

        result += '<tbody>' + str(table.findAll('tr')[4+correction]) + str(table.findAll('tr')[5+correction])

        switch = False

        tr = table.findAll('tr')[6 + correction:]

        for i in range(len(tr)):
            if self.preparation_parameters('student', tr[i].text).find(parameter) > 0 and not switch and tr[i].findAll('td', attrs=self.signs_boundaries):
                result += str(tr[i])
                switch = True

            elif not len(tr[i].findAll("td", self.signs_boundaries)) == 0 and switch:
                break

            elif switch:
                result += str(tr[i])

        if not switch:
            result += '</tbody>' + '</table>' + '<div align="center"><font size="6" color="#FF0000">Расписание для группы %s не найдено</font></div>' % original_parameter

        else:
            result += '</tbody>' + '</table>'

        return result

    def assembly_teacher(self, table, parameter, original_parameter):

        correction = table[1]
        table = table[0]

        result = str(self.head) + '<table cellspacing="0" border="0">'

        for i in table.findAll('colgroup'):
            result += str(i)

        result += '<tbody>' + str(table.findAll('tr')[4+correction]) + str(table.findAll('tr')[5+correction])

        i = 0
        upper_bound = 0
        items = [[], []]

        tr = table.findAll('tr')[6 + correction:]

        while i < len(tr):
            if not len(tr[i].findAll("td", self.signs_boundaries)) == 0:
                upper_bound = i

            elif self.preparation_parameters('teacher', tr[i].text).find(parameter) >= 0:
                try:
                    number = int(tr[i].findAll("td")[3].text)

                except:
                    number = 10

                i = upper_bound
                switch = False
                item = ''
                while i < len(tr):
                    if not len(tr[i].findAll("td", self.signs_boundaries)) == 0 and not switch:
                        item += str(tr[i])
                        switch = True

                    elif not len(tr[i].findAll("td", self.signs_boundaries)) == 0  and switch:
                        items[0].append(number)
                        items[1].append(item)
                        upper_bound = i
                        break

                    elif switch:
                        if self.preparation_parameters('teacher', tr[i].text).find(parameter) >= 0:
                            x = '<tr>'

                            for td in tr[i].findAll('td'):
                                if self.preparation_parameters('teacher', td.text).find(parameter) >= 0:

                                    if str(td).find('bgcolor') >= 0:
                                        y = str(td).split('bgcolor')
                                        x += y[0] + 'bgcolor="#FFCA33"' + y[1][10::]

                                    else:
                                        x += '<td bgcolor="#FFCA33"' + str(td)[3:]

                                else:
                                    x += str(td)
                            item += x + '</tr>'
                        else:
                            item += str(tr[i])
                    i += 1
                else:
                    items[0].append(number)
                    items[1].append(item)
            i += 1

        if len(items[0]) == 0:
            return result + '</tbody>' + '</table>' + '<div align="center"><font size="6" color="#FF0000">Расписание для преподавателя %s не найдено</font></div>' % original_parameter

        while not len(items[0]) == 0:
            index = items[0].index(min(items[0]))
            result += items[1][index]
            del items[0][index], items[1][index]

        return result + '</tbody>' + '</table>'

    def preparation_parameters(self, class_, parameter):
        parameter = parameter.lower().replace(" ", "")
        if class_ == 'teacher':
            parameter = parameter.replace(".", "").replace(",", "")
        else:
            parameter = parameter.replace("-", "")
        return parameter

    # Одиноный запрос
    def single(self, user_id, class_, parameter, record=False):
        # Подготовка parameter
        original_parameter = parameter
        parameter = self.preparation_parameters(class_, original_parameter)

        # Перебор таблиц
        for table in self.data:
            correction = table[1]
            table = table[0]

            # Подготовка ячейки
            try:
                self.archive[1][str(table.findAll('tr')[4+correction].text).replace("\n", "")]
            except KeyError:
                self.archive[1][str(table.findAll('tr')[4+correction].text).replace("\n", "")] = {}

            try:
                # Проверка наличия в памяти
                picture = self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")][parameter][0]
                html = self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")][parameter][1]

            except :
                # Составление HTML и запись в память
                if class_ == 'student':
                    html = self.assembly_student([table, correction], parameter, original_parameter)
                    picture = imgkit.from_string(html, False)
                    picture = self.photo_upload(picture)
                    self.archive[1][str(table.findAll('tr')[4+correction].text).replace("\n", "")][parameter] = [picture, html]

                elif class_ == 'teacher':
                    html = self.assembly_teacher([table, correction], parameter, original_parameter)
                    picture = imgkit.from_string(html, False)
                    picture = self.photo_upload(picture)
                    self.archive[1][str(table.findAll('tr')[4+correction].text).replace("\n", "")][parameter] = [picture, html]

            text = parameter + 'Solo'
            self.send_message(user_id, text, picture)

            # Запись в базу
            if record:
                date = self.date_conversion(table.findAll('tr')[4 + correction].text)
                date = 'a'+str(date).replace("-", "")
                html = BeautifulSoup(html, 'html.parser').find('table').text.replace("\n", "--").replace("\\", "-")
                self.c.execute("UPDATE subscriptions_playground_1 SET %s = '%s' WHERE id=%i and class='%s' and parameter='%s'"%
                               (date,html,
                                user_id, class_, original_parameter))
                self.conn.commit()

    # Авто расылка
    def auto_mailing(self):
        while True:
            self.request()
            for table in self.data:
                correction = table[1]
                table = table[0]

                try:
                    self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")]
                except KeyError:
                    self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")] = {}

                date = self.date_conversion(table.findAll('tr')[4 + correction].text)
                date = 'a' + str(date).replace("-", "")

                self.c.execute('SELECT id, class, parameter, %s  FROM subscriptions_playground_1  WHERE NOT (class IS NULL OR parameter IS NULL)'%date)
                for user in self.c.fetchall():
                    print(user)

                    id = user[0]
                    class_ = user[1]
                    html_db = user[3]
                    original_parameter = user[2]
                    parameter = self.preparation_parameters(class_, user[2])

                    try:
                        # Проверка наличия в памяти
                        picture = self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")][parameter][0]
                        html = self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")][parameter][1]
                    except:
                        # Составление HTML и запись в память
                        if class_ == 'student':
                            html = self.assembly_student([table, correction], parameter, original_parameter)
                            picture = imgkit.from_string(html, False)
                            picture = self.photo_upload(picture)
                            self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")][
                                parameter] = [picture, html]

                        elif class_ == 'teacher':
                            html = self.assembly_teacher([table, correction], parameter, original_parameter)
                            picture = imgkit.from_string(html, False)
                            picture = self.photo_upload(picture)
                            self.archive[1][str(table.findAll('tr')[4 + correction].text).replace("\n", "")][
                                parameter] = [picture, html]

                    html = BeautifulSoup(html, 'html.parser').find('table').text.replace("\n", "--").replace("\\", "-")
                    if html != html_db:

                        text = parameter + 'Авто'
                        self.send_message(id, text, picture)

                        date = self.date_conversion(table.findAll('tr')[4 + correction].text)
                        date = 'a' + str(date).replace("-", "")

                        self.c.execute(
                            "UPDATE subscriptions_playground_1 SET %s = '%s' WHERE id=%i and class='%s' and parameter='%s'" %
                            (date, html,
                             id, class_, original_parameter))
                        self.conn.commit()


import requests
from bs4 import BeautifulSoup

import datetime
import time

import imgkit

import psycopg2

from parsers import functions

import config


class Parser:
    def __init__(self, Sender):
        self.Sender = Sender

        self.signs_boundaries = config.signs_boundaries

        self.conn = psycopg2.connect(
                                    host=config.host,
                                    database=config.database,
                                    user=config.user,
                                    password=config.password
                                    )
        self.c = self.conn.cursor()

        self.html = ''
        self.date = 0
        self.archive = {}

    # Упровлеие колоками добавлеие удалеие дней
    def column_control(self, dates):

        for i in range(len(dates)):
            dates[i] = 'a'+str(dates[i]).replace("-", "")

        dates = [dates, []]

        # Запрос колонок
        self.c.execute('SHOW COLUMNS FROM subscriptions_info_1')
        for i in self.c.fetchall():
            dates[1].append(i[0])
        dates[1] = dates[1][3:]

        # Добавление колонок
        for i in dates[0]:
            if not i in dates[1]:
                self.c.execute("ALTER TABLE subscriptions_info_1 ADD %s TEXT" % i)
                self.conn.commit()

        # Удаление колонок
        for i in dates[1]:
            if not i in dates[0]:
                self.c.execute("ALTER TABLE subscriptions_info_1 DROP %s" % i)
                self.conn.commit()

    # обновляет ВСЕ
    def update(self, html):
        self.html = html
        self.date = datetime.date.today()
        self.archive = {}

        HTML = BeautifulSoup(html, 'html.parser')
        self.head = '<head>%s%s</head>' % (str(HTML.find('meta')), str(HTML.find('style')))

        for table in HTML.findAll('table'):
            # Колибровка сдвига
            for tr in table.findAll('tr'):
                if tr.text in 'Расписание занятий с учетом замен':
                    correction = table.findAll('tr').index(tr) - 5
                    break

            # Вывод результата
            date = self.date_conversion(table.findAll('tr')[4 + correction].text)
            tables, dates = [], []
            if date >= datetime.date.today():
                tables.append([table, correction])
                dates.append(date)

        # Сортировка в правильном порядке
        data = []
        while len(dates) != 0:
            i = dates.index(min(dates))
            data.append(tables[i])
            del dates[i], tables[i]

        self.column_control(dates)
        self.tables = data

    # Ждёт обновлние сайта
    def pending_update(self):
        while True:
            try:
                html = requests.get('https://nntc.nnov.ru/sites/default/files/sched/zameny.html').content
                if (str(html) != self.html or self.date != datetime.date.today()) and str(html).find('</html>') >= 0:
                    break

            except:
                continue
            time.sleep(1)
        self.update(html)

    # Преобразует дату в нормальый вид
    def date_conversion(self, date):
        date = date.replace("\n", "").split(" ")

        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
                  'ноября', 'декабря']

        month = months.index(date[2]) + 1
        day = int(date[1])
        year = int(datetime.date.today().year)

        date = datetime.date(year, month, day)
        return date

    # Одиноный запрос расписания
    def single(self, user_id, class_, parameter, record=False):
        pass

    def auto_mailing(self):
        pass

    def start(self):
        pass