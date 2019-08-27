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
        self.averaged_parameter = functions.averaged_parameter

        self.conn = psycopg2.connect(
            host=config.host,
            database=config.database,
            user=config.user,
            password=config.password
        )

        self.html = ''
        self.date = 0
        self.archive = {}

        self.colgroup = """
                <colgroup>
                <col class="xl678515" width="100">
                <col class="xl678515" width="140">
                <col class="xl678515" width="30">
                <col class="xl678515" width="140">
                <col class="xl678515" width="30">
                <col class="xl678515" width="140">
                <col class="xl678515" width="30">
                <col class="xl678515" width="140">
                <col class="xl678515" width="30">
                <col class="xl678515" width="140">
                <col class="xl678515" width="30">
                <col class="xl678515" width="140">
                <col class="xl678515" width="30">
                <col class="xl678515" width="140">
                <col class="xl668515" width="40">
                </colgroup>
                """

        self.cap = """
                <tr bgcolor="#A9A9A9">
                    <td><div align="center"><font size="3">Группа</font></div></td>
                    <td><div align="center"><font size="3">1 пара</font></div></td>
                    <td><div align="center"><font size="3">каб.№</font></div></td>
                    <td><div align="center"><font size="3">2 пара</font></div></td>
                    <td><div align="center"><font size="3">каб.№</font></div></td>
                    <td><div align="center"><font size="3">3 пара</font></div></td>
                    <td><div align="center"><font size="3">каб.№</font></div></td>
                    <td><div align="center"><font size="3">4 пара</font></div></td>
                    <td><div align="center"><font size="3">каб.№</font></div></td>
                    <td><div align="center"><font size="3">5 пара</font></div></td>
                    <td><div align="center"><font size="3">каб.№</font></div></td>
                    <td><div align="center"><font size="3">6 пара</font></div></td>
                    <td><div align="center"><font size="3">каб.№</font></div></td>
                    <td><div align="center"><font size="3">7 пара</font></div></td>
                    <td><div align="center"><font size="3">каб.№</font></div></td>
                    <td><div align="center"><font size="3">-</font></div></td>
                </tr>
                """

    def pending_update(self):
        while True:
            try:
                cookies = {'beget': 'begetok; expires=2035-08-24 15:26:54.364773'}

                answer = requests.get('https://nntc.nnov.ru/sites/default/files/sched/schedule_2.html',
                                    cookies=cookies)

                if answer.status_code != 200:
                    if self.html == '':
                        with open("site.html", "r", encoding="utf8") as f:
                            html = f.read()
                            break
                    continue

                html = str(answer.content, 'windows-1251')

                if self.date != datetime.date.today() and self.html != '':
                    html = self.html
                    break

                if str(html) != self.html and '</html>' in str(html):
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

    def update(self, html):
        self.html = html
        self.date = datetime.date.today()
        self.archive = {}
        HTML = BeautifulSoup(html, 'html.parser')
        self.head = '<head>' + str(HTML.find('meta')) + '</head>'

        tables = []
        table_upper_bound = None

        trs = HTML.findAll('tr')

        for line_number in range(len(trs)):
            if 'Замена в расписании' in trs[line_number].text and table_upper_bound == None:
                table_upper_bound = line_number

            elif 'Замена в расписании' in trs[line_number].text:

                # >=
                if self.date_conversion(trs[table_upper_bound].text) != datetime.date.today():
                    tables.append(trs[table_upper_bound:line_number])
                    self.archive[self.date_conversion(trs[table_upper_bound].text)] = {'student': {}, 'teacher': {}}
                table_upper_bound = line_number
        else:
            # >=
            if self.date_conversion(trs[table_upper_bound].text) != datetime.date.today():
                tables.append(trs[table_upper_bound:line_number])
                self.archive[self.date_conversion(trs[table_upper_bound].text)] = {'student': {}, 'teacher': {}}

        self.column_control(list(self.archive.keys()))
        self.tables = tables

    # Упровлеие колоками добавлеие удалеие дней
    def column_control(self, dates):
        c = self.conn.cursor()

        for i in range(len(dates)):
            dates[i] = 'a' + str(dates[i]).replace("-", "")

        dates = [dates, []]
        # Запрос колонок
        c.execute("SELECT * FROM information_schema.columns WHERE table_name = 'subscriptions_info_2'")
        for i in c.fetchall():
            dates[1].append(i[3])
        dates[1] = dates[1][3:]

        # Добавление колонок
        for i in dates[0]:
            if not i in dates[1]:
                c.execute("ALTER TABLE subscriptions_info_2 ADD {} TEXT".format(i))
                self.conn.commit()

        # Удаление колонок
        for i in dates[1]:
            if not i in dates[0]:
                c.execute("ALTER TABLE subscriptions_info_2 DROP {}".format(i))
                self.conn.commit()

    def date_conversion(self, date):
        date = date.replace("\n", "").split(" ")

        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
                      'ноября', 'декабря']

        for i in range(len(date)):
            try:
                int(date[i])
                break
            except:
                pass

        month = months.index(date[1+i]) + 1
        day = int(date[0+i])
        year = int(datetime.date.today().year)

        date = datetime.date(year, month, day)
        return date

    def assembly_student(self, day, parameter):
        averaged_parameter = self.averaged_parameter('student', parameter)

        result = '<body>' + str(self.head) + '</body>'
        result += '<table border="1" cellpadding="2" width="1500">'
        result += str(self.colgroup)

        result +=  '<tbody>'
        result += """
        <tr bgcolor="#A9A9A9">
            <td colspan="16"><div align="center"><font size="6">%s</font></div></td>
        </tr>
        """ % day[0].text
        result += self.cap

        for line in day[2:]:
            if averaged_parameter in self.averaged_parameter('student', line.findAll('td')[0].text):
                line = line.findAll('td')
                result += '<tr>'
                result += '<td bgcolor="#B3B3B3">%s</td>' % line[0].text
                for i in line[1:]:
                    result += str(i)

                result += '</tr>' + '</table>'
                break
        else:

            result += '</table>' + '<div align="center"><font size="7" color="#FF0000">Расписание для группы %s не найдено</font></div>' % parameter

        return result + '</body>'

    def assembly_teacher(self, day, parameter):
        averaged_parameter = self.averaged_parameter('teacher', parameter)

        result = '<body>' + str(self.head) + '</body>'
        result += '<table border="1" cellpadding="2" width="1500">'
        result += str(self.colgroup)

        result += '<tbody>'
        result += """
                <tr bgcolor="#A9A9A9">
                    <td colspan="16"><div align="center"><font size="6">%s</font></div></td>
                </tr>
                """ % day[0].text

        result += self.cap

        switch = True

        for line in day[2:]:
            if averaged_parameter in self.averaged_parameter('teacher', line.text):
                line = line.findAll('td')
                result += '<tr>'
                result += '<td bgcolor="#B3B3B3">%s</td>' % line[0].text
                for i in line[1:]:
                    if averaged_parameter in self.averaged_parameter('teacher', i.text):
                        result += str(i).replace('<td', '<td bgcolor="#EEE8AA"')
                    else:
                        result += str(i)

                result += '</tr>'
                switch = False

        if switch:
            result += '</table>' + '<div align="center"><font size="7" color="#FF0000">Расписание для преподователя %s не найдено</font></div>' % parameter
            return result + '</body>'

        result += '</table>'
        return result + '</body>'

    def create_or_query(self, table, class_, parameter):
        date = self.date_conversion(table[0].text)

        try:
            # Проверка наличия в памяти
            picture, html = self.archive[date][class_][parameter]

        except:
            # Составление HTML и запись в память
            if class_ == 'student':
                html = self.assembly_student(table, parameter)

            elif class_ == 'teacher':
                html = self.assembly_teacher(table, parameter)

            picture = imgkit.from_string(html, False)
            picture = functions.photo_upload(picture)
            self.archive[date][class_][parameter] = [picture, html]

        return picture, html

    # Одиноный запрос расписания
    def single(self, user_id, class_, parameter, first_time):

        # Перебор таблиц
        if self.tables == []:
            self.Sender(user_id, message='Нет актуального расписания для {}.'.format(parameter))
            return

        for table in self.tables:
            picture, html = self.create_or_query(table, class_, parameter)
            self.Sender(user_id, attachment=picture)

            if first_time:
                c = self.conn.cursor()
                c.execute(
                    "UPDATE subscriptions_info_2 SET {0} = '{1}' WHERE (class='{2}' and parameter='{3}' "
                    "and subscription_count=1)".format(
                        'a' + str(self.date_conversion(table[0].text)).replace("-", ""), html,
                        class_, parameter))
                self.conn.commit()

    def auto_mailing(self):
        c = self.conn.cursor()

        while True:
            html = self.pending_update()
            self.update(html)

            for table in self.tables:
                c.execute("SELECT class, parameter, {} FROM subscriptions_info_2".format(
                    'a'+str(self.date_conversion(table[0].text)).replace("-", "")))

                for line in c.fetchall():

                    def flow(table, line):
                        c = self.conn.cursor()
                        picture, html = self.create_or_query(table, line[0], line[1])

                        c.execute("SELECT * FROM subscriptions WHERE (plate=2 and class='{}'"
                                       "and parameter='{}')".format(line[0], line[1]))

                        if line[2] != html:
                            for user in c.fetchall():
                                self.Sender(user[0], attachment=picture)

                            c.execute(
                                "UPDATE subscriptions_info_2 SET {} = '{}' WHERE (class='{}' and parameter='{}')".format(
                                    'a'+str(self.date_conversion(table[0].text)).replace("-", ""), html,
                                    line[0], line[1]))
                            self.conn.commit()

                    Thread(target=flow, args=(table, line)).start()

    def start(self):
        auto_mailing = Thread(target=self.auto_mailing, name='auto_mailing_parser2')
        auto_mailing.start()


import message_sender

if __name__ == '__main__':
    Sender = message_sender.Sender()
    Sender.start()

    Parser1 = Parser(Sender.add)
    Parser1.start()

    time.sleep(10)

    user_id = 265868386
    class_ = 'student'
    parameter = '1ТМ-18-1'

    Parser1.single(user_id, class_, parameter, first_time=True)