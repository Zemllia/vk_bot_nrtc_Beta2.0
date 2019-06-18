import requests, imgkit, json, random, datetime, time, random
from bs4 import BeautifulSoup


class parser:
    def __init__(self, conn, c, vk):

        self.vk = vk

        self.conn = conn
        self.c = c

        self.archive = [['', 0], {}]
        self.random_ = 0

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

    def request(self):
        # Попытка обновить сайт
        while True:
            try:
                r = requests.get('https://nntc.nnov.ru/sites/default/files/sched/schedule_2.html').content
                HTML = BeautifulSoup(r, 'html.parser')

                if (str(r) != self.archive[0][0] or self.archive[0][1] != datetime.date.today()) and str(r).find(
                        '</html>') >= 0:
                    break
            except:
                continue

            break

            time.sleep(0)

        # Произошло изменение
        self.archive = [[str(r), datetime.date.today()], {}]
        self.head = '<head>' + str(HTML.find('meta')) + '</head>'

        upper_bound = 0
        data = []
        tr = HTML.find('table').findAll('tr')
        dates = [[], []]

        for line in range(1, len(tr)):
            if 'неделя' in tr[line].text.lower() or line+1 == len(tr):

                dates[0].append(self.date_conversion(tr[upper_bound].text))
                data.append(tr[upper_bound:line])
                upper_bound = line

        # Добавление колонок

        # Удаление колонок

        self.data = data

    def date_conversion(self, date):
        date = date.replace("\n", "").lower().split(" ")

        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
                  'ноября', 'декабря']

        for word in range(len(date)):
            if date[word] in months:
                month_= word
                break

        month = months.index(date[month_]) + 1
        day = int(date[month_-1])
        year = int(datetime.date.today().year)

        date = datetime.date(year, month, day)
        return date

    # Загрузка на сервер вк
    def photo_upload(self, picture):
        img = {'photo': ('Schedule.jpg', picture)}
        address = self.vk.photos.getMessagesUploadServer()['upload_url']

        response = requests.post(address, files=img)
        result = json.loads(response.text)
        result = self.vk.photos.saveMessagesPhoto(photo=result['photo'], server=result['server'], hash=result['hash'])
        return 'photo'+str(result[0]['owner_id'])+'_'+str(result[0]['id'])

    def send_message(self, id, text, picture):
        try:
            self.random_ -= random.randint(0, 1000000000000000)

            result = self.vk.messages.send(
                user_id=id,
                message=None,
                attachment=picture,
                random_id=self.random_)
            return result
        except:
            print('Error')
            pass

    def preparation_parameters(self, class_, parameter):
        parameter = parameter.lower().replace(" ", "").replace("\r", "").replace("\n", "")
        if class_ == 'teacher':
            parameter = parameter.replace(".", "").replace(",", "")
        else:
            parameter = parameter.replace("-", "")
        return parameter

    def assembly_student(self, day, parameter, original_parameter):

        result = '<body>' + str(self.head) + '</body>'
        result +=  '<table border="1" cellpadding="2" width="1500">'
        result += str(self.colgroup)


        result +=  '<tbody>'
        result += """
        <tr bgcolor='#F1A904'>
            <td colspan="16"><div align="center"><font size="6">%s</font></div></td>
        </tr>
        """ % day[0].text
        result += """
        <tr bgcolor='#F1A904'>
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

        for line in day[2:]:
            if parameter == self.preparation_parameters('student', line.findAll('td')[0].text):
                line = line.findAll('td')
                result += '<tr>'
                result += '<td bgcolor="#B3B3B3">%s</td>' % line[0].text
                for i in line[1:]:
                    result += str(i)

                result += '</tr>' + '</table>'
                break
        else:

            result += '</table>' + '<div align="center"><font size="5" color="#FF0000">Расписание для группы %s не найдено</font></div>' % original_parameter

        return result + '</body>'

    def assembly_teacher(self, day, parameter, original_parameter):
        result = '<body>' + str(self.head) + '</body>'
        result += '<table border="1" cellpadding="2" width="1500">'
        result += str(self.colgroup)

        result += '<tbody>'
        result += """
                <tr bgcolor='#F1A904'>
                    <td colspan="16"><div align="center"><font size="6">%s</font></div></td>
                </tr>
                """ % day[0].text
        result += """
                <tr bgcolor='#F1A904'>
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

        switch = True

        for line in day[2:]:
            if parameter in self.preparation_parameters('teacher', line.text):
                line = line.findAll('td')
                result += '<tr>'
                result += '<td bgcolor="#B3B3B3">%s</td>' % line[0].text
                for i in line[1:]:
                    if parameter in self.preparation_parameters('teacher', i.text):
                        result += str(i)
                    else:
                        result += str(i)

                result += '</tr>'
                switch = False

        if switch:
            result += '</table>' + '<div align="center"><font size="5" color="#FF0000">Расписание для преподователя %s не найдено</font></div>' % original_parameter
            return result + '</body>'

        result += '</table>'
        return result + '</body>'

    # Одиноный запрос
    def single(self, user_id, class_, parameter, record=False):

        self.request()

        # Подготовка parameter
        original_parameter = parameter
        parameter = self.preparation_parameters(class_, original_parameter)

        # Перебор дней
        for day in self.data:

            # Подготовка ячейки
            try:
                self.archive[1][str(day[0])]
            except KeyError:
                self.archive[1][str(day[0])] = {}

            try:
                # Проверка наличия в памяти
                picture = self.archive[1][str(day[0])][parameter][0]
                html = self.archive[1][str(day[0])][parameter][1]

            except:
                # Составление HTML и запись в память
                if class_ == 'student':
                    html = self.assembly_student(day, parameter, original_parameter)
                    picture = imgkit.from_string(html, False)
                    picture = self.photo_upload(picture)
                    self.archive[1][str(day[0])][parameter] = [
                        picture, html]

                elif class_ == 'teacher':
                    html = self.assembly_teacher(day, parameter, original_parameter)
                    picture = imgkit.from_string(html, False)
                    picture = self.photo_upload(picture)
                    self.archive[1][str(day[0])][parameter] = [
                        picture, html]

            text = parameter + 'Solo'
            self.send_message(user_id, text, picture)

            # Запись в базу
            if record:
                date = self.date_conversion(table.findAll('tr')[4 + correction].text)
                date = 'a' + str(date).replace("-", "")
                html = BeautifulSoup(html, 'html.parser').find('table').text.replace("\n", "--").replace("\\", "-")
                self.c.execute(
                    "UPDATE subscriptions_playground_2 SET %s = '%s' WHERE id=%i and class='%s' and parameter='%s'" %
                    (date, html,
                     user_id, class_, original_parameter))
                self.conn.commit()

    # Авто расылка
    def auto_mailing(self):
        pass
