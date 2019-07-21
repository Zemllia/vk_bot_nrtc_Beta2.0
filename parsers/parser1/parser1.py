import requests
from bs4 import BeautifulSoup

import datetime
import time

import imgkit

import psycopg2

from threading import Thread

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

    # Приведение к норм виду
    def averaging_parameters(self, class_, parameter):
        parameter = parameter.lower().replace(" ", "")
        if class_ == 'teacher':
            parameter = parameter.replace(".", "").replace(",", "")
        else:
            parameter = parameter.replace("-", "")
        return parameter

    # Упровлеие колоками добавлеие удалеие дней
    def column_control(self, dates):

        for i in range(len(dates)):
            dates[i] = 'a'+str(dates[i]).replace("-", "")

        dates = [dates, []]
        # Запрос колонок
        self.c.execute("SELECT * FROM information_schema.columns WHERE table_name = 'subscriptions_info_1'")
        for i in self.c.fetchall():
            dates[1].append(i[3])
        dates[1] = dates[1][3:]

        # Добавление колонок
        for i in dates[0]:
            if not i in dates[1]:
                self.c.execute("ALTER TABLE subscriptions_info_1 ADD {} TEXT".format(i))
                self.conn.commit()

        # Удаление колонок
        for i in dates[1]:
            if not i in dates[0]:
                self.c.execute("ALTER TABLE subscriptions_info_1 DROP {}".format(i))
                self.conn.commit()

    # обновляет ВСЕ
    def update(self, html):
        self.html = html
        self.date = datetime.date.today()
        self.archive = {}

        HTML = BeautifulSoup(html, 'html.parser')
        self.head = '<head>%s%s</head>' % (str(HTML.find('meta')), str(HTML.find('style')))
        tables, dates = [], []

        for table in HTML.findAll('table'):
            table = table.findAll('tr')

            number_deleted = 0
            # Колибровка сдвига
            for i in range(len(table)):
                i -= number_deleted
                if 'NNN DD MMMM' in str(table[i]):
                    break

                elif i == 0:
                    if 'НРТК' in table[i].text:
                        table[i] = '<tr></tr>'

                    table[i] = BeautifulSoup(str(table[i]).replace('rowspan="', 'rowspan="1"'), 'html.parser').findAll('tr')[0]

                else:
                    del table[i]
                    number_deleted += 1

            # Вывод результата
            date = self.date_conversion(table[1].text)
            # >=
            if date != datetime.date.today():
                tables.append(table)
                dates.append(date)
                self.archive[date] = {}

        self.column_control(dates)

        # Сортировка в правильном порядке
        data = []
        while len(dates) != 0:
            i = dates.index(min(dates))
            data.append(tables[i])
            del dates[i], tables[i]

        self.tables = data

    # Замена даты (англ на рус) из-за бага на сайте от 30 ‎мая ‎2019 +-
    def date_replacement(self, html):
        months = [['January', 'января'],
                  ['February', 'февраля'],
                  ['March', 'марта'],
                  ['April', 'апреля'],
                  ['May', 'мая'],
                  ['June', 'июня'],
                  ['July', 'июля'],
                  ['August', 'августа'],
                  ['September', 'сентября'],
                  ['October', 'октября'],
                  ['November', 'ноября'],
                  ['December', 'декабря']]

        weekdays = [['Monday', 'понедельник'],
                    ['Tuesday', 'вторник'],
                    ['Wednesday', 'среда'],
                    ['Thursday', 'четверг'],
                    ['Friday', 'пятница'],
                    ['Saturday', 'суббота'],
                    ['Sunday', 'воскресенье']
                    ]

        html = str(html, 'utf-8')
        for i in months:
            html = html.replace(i[0], i[1])

        for i in weekdays:
            html = html.replace(i[0], i[1])

        return html

    # Ждёт обновлние сайта
    def pending_update(self):
        while True:
            try:
                html = requests.get('https://nntc.nnov.ru/sites/default/files/sched/zameny.html').content
                html = self.date_replacement(html)

                if self.date != datetime.date.today() and self.html != '':
                    html = self.html
                    break

                if str(html) != self.html and str(html).find('</html>') >= 0:
                    with open("site.html", "w", encoding="utf8") as f:
                        f.write(html)
                    break

            except:
                if self.html == '':

                    with open("site.html", "r", encoding="utf8") as f:
                        html = f.read()
                    break

                continue
            time.sleep(1)

        return html

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

    def assembly_student(self, table, parameter):
        averaged_parameter = self.averaging_parameters('student', parameter)

        result = str(self.head) + '<table cellspacing="0" border="0">'
        result += """   
                    <colgroup width="142"></colgroup>
        	        <colgroup width="392"></colgroup>
        	        <colgroup width="326"></colgroup>
        	        <colgroup width="68"></colgroup>
        	        <colgroup width="156"></colgroup>
        	        <colgroup width="131"></colgroup>
        	        """
        result += '<tbody>' + str(table[0]) + str(table[1]) + str(table[2])

        switch = False

        trs = table[3:]

        for i in range(len(trs)):
            if self.averaging_parameters('student', trs[i].text).find(averaged_parameter) > 0 and not switch and trs[i].findAll(
                    'td', attrs=self.signs_boundaries):
                result += str(trs[i])
                switch = True

            elif not len(trs[i].findAll("td", self.signs_boundaries)) == 0 and switch:
                break

            elif switch:
                result += str(trs[i])

        if not switch:
            result += '</tbody>' + '</table>' + '<div align="center"><font size="6" color="#FF0000">Расписание для группы %s не найдено</font></div>' % parameter

        else:
            result += '</tbody>' + '</table>'

        return result

    def assembly_teacher(self, table, parameter):
        averaged_parameter = self.averaging_parameters('teacher', parameter)

        result = str(self.head) + '<table cellspacing="0" border="0">'
        result += """   
            <colgroup width="142"></colgroup>
	        <colgroup width="392"></colgroup>
	        <colgroup width="326"></colgroup>
	        <colgroup width="68"></colgroup>
	        <colgroup width="156"></colgroup>
	        <colgroup width="131"></colgroup>
	        """

        result += '<tbody>' + str(table[0]) + str(table[1]) + str(table[2])

        i = 0
        upper_bound = 0
        items = [[], []]

        tr = table[3:]

        while i < len(tr):
            if not len(tr[i].findAll("td", self.signs_boundaries)) == 0:
                upper_bound = i

            elif self.averaging_parameters('teacher', tr[i].text).find(averaged_parameter) >= 0:
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

                    elif not len(tr[i].findAll("td", self.signs_boundaries)) == 0 and switch:
                        items[0].append(number)
                        items[1].append(item)
                        upper_bound = i
                        break

                    elif switch:
                        if self.averaging_parameters('teacher', tr[i].text).find(averaged_parameter) >= 0:
                            x = '<tr>'

                            for td in tr[i].findAll('td'):
                                if self.averaging_parameters('teacher', td.text).find(averaged_parameter) >= 0:

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
            result += '</tbody>' + '</table>' + '<div align="center"><font size="6" color="#FF0000">Расписание для преподавателя %s не найдено</font></div>' % parameter
            return result

        while len(items[0]) != 0:
            index = items[0].index(min(items[0]))
            result += items[1][index]
            del items[0][index], items[1][index]

        result += '</tbody>' + '</table>'
        return result

    def create_or_query(self, table, class_, parameter):
        date = self.date_conversion(table[1].text)

        try:
            # Проверка наличия в памяти
            picture, html = self.archive[date][parameter]

        except:
            # Составление HTML и запись в память
            if class_ == 'student':
                html = self.assembly_student(table, parameter)
                picture = imgkit.from_string(html, False)
                picture = functions.photo_upload(picture)
                self.archive[date][parameter] = [picture, html]

            elif class_ == 'teacher':
                html = self.assembly_teacher(table, parameter)
                picture = imgkit.from_string(html, False)
                picture = functions.photo_upload(picture)
                self.archive[date][parameter] = [picture, html]

        return picture, html

    # Одиноный запрос расписания
    def single(self, user_id, class_, parameter):
        # Перебор таблиц
        if self.tables == []:
            self.Sender(user_id, message='Нет актуального расписания для {}.'.format(parameter))
            return

        for table in self.tables:
            picture, html = self.create_or_query(table, class_, parameter)
            self.Sender(user_id, attachment=picture)

            self.c.execute("UPDATE subscriptions_info_1 SET {0} = '{1}' WHERE (class='{2}' and parameter='{3}' and {0}='')".format(
                'a' + str(self.date_conversion(table[1].text)).replace("-", ""), html,
                class_, parameter))
            self.conn.commit()

    def auto_mailing(self):
        while True:
            html = self.pending_update()
            self.update(html)

            for table in self.tables:
                self.c.execute("SELECT class, parameter, {} FROM subscriptions_info_1".format(
                    'a'+str(self.date_conversion(table[1].text)).replace("-", "")))

                for line in self.c.fetchall():
                    picture, html = self.create_or_query(table, line[0], line[1])
                    self.c.execute("SELECT * FROM subscriptions WHERE (plate=1 and class='{}' and parameter='{}')".format(
                        line[0], line[1]))

                    if line[2] != html:
                        for user in self.c.fetchall():
                            self.Sender(user[0], attachment=picture)

                        self.c.execute("UPDATE subscriptions_info_1 SET {} = '{}' WHERE (class='{}' and parameter='{}' and subscription_count=1)".format(
                            'a'+str(self.date_conversion(table[1].text)).replace("-", ""), html,
                            line[0], line[1]))
                        self.conn.commit()

    def start(self):
        auto_mailing = Thread(target=self.auto_mailing, name='auto_mailing_parser1')
        auto_mailing.start()


import message_sender

if __name__ == '__main__':
    Sender = message_sender.Sender()
    Sender.start()

    Parser1 = Parser(Sender.add)
    Parser1.start()

    user_id = 265868386
    class_ = 'student'
    parameter = '2ПКС-17-1к'

    Parser1.single(user_id, class_, parameter)
