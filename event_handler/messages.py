import json
import config
import os
import random
import psycopg2
import apiai
from flask import Flask, request
import logging

# Все для вк! Моря и ААААКеаны, все для вк!! ДЛЯЯЯ ВВВВВКККККК (Все библеотеки для вк)
import vk_api

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class Messg:
    def __init__(self, onetimeschedulefunc):
        self.vk_session = vk_api.VkApi(token=config.vk_token)
        from vk_api.longpoll import VkLongPoll
        from vk_api.bot_longpoll import VkBotLongPoll
        self.longpoll = VkLongPoll(self.vk_session)
        self.vk = self.vk_session.get_api()
        self.blongpoll = VkBotLongPoll(vk=self.vk_session, group_id=config.group_id, wait=25)
        self.conn = psycopg2.connect(
            host=config.host,
            database=config.database,
            user=config.user,
            password=config.password
        )
        self.c = self.conn.cursor()
        self.keyBoardList = ["event_handler/json/cancel.json", "event_handler/json/commands.json",
                             "event_handler/json/isTeacher.json", "event_handler/json/menu.json",
                             "event_handler/json/plate.json", "event_handler/json/hide_keyboard.json"]
        self.onetimeschedule = onetimeschedulefunc

    Random = 0
    rand_phrases = ['Всегда пожалуйста', 'Вот ваше расписание', 'Машины скоро захва... то есть вот ваше расписание',
                    'Бот к вашим услугам :)', 'Не благодарите, просто напишите спасибо))']

    def random_id(self):
        self.Random += random.randint(0, 1000000000000000)
        return self.Random

    def checkMessage(self, msge: str, peerid):
        self.addNewUser(peerid)
        msgeLower = msge.lower()
        if self.GetUserState(peerid)[0] == "left":
            self.SendMessage(peerid, "Сначала подпишитесь назад", 3)
            return

        if msgeLower == "регистрация":
            cmd = "SELECT parameter FROM subscriptions WHERE id=%d" % peerid
            self.c.execute(cmd)
            result = self.c.fetchall()
            if len(result) < 9:
                if self.GetUserState(peerid) == "":
                    msg = "Вы уже проходите регистрацию"
                    state = self.GetUserState(peerid)
                    keyboardInt = 0
                    if state == "setplate":
                        keyboardInt = 4
                    elif state == "setclass":
                        keyboardInt = 2
                    elif state == "setParameter":
                        keyboardInt = 0
                    self.SendMessage(peerid, msg, keyboardInt)
                else:
                    self.StartRegistration(peerid)
                    # LogManager.AddLog(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S") + '  Запрос на регистрацию
                    # от %s(%d), peerid = ' % (self.GetName(peerid, 'nom'), peerid))
            else:
                self.SendMessage(peerid, "Вы зарегистрировали максимальное количество подписок!", 3)

        elif msgeLower == 'удалить профиль':
            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('deleting', peerid)
            self.c.execute(cmd)
            self.conn.commit()
            self.generateJSONToDelete(peerid)
            self.vk.messages.send(
                peer_id=peerid,
                message="Укажите группу/преподавателя для удаления",
                keyboard=open("JSONS_to_delete/" + str(peerid)+".json", "r", encoding="UTF-8").read(),
                random_id=self.random_id()
            )

        elif msgeLower == "расписание":
            listOfUserGroups = self.GetUserDataFromSubscriptions(peerid)
            if len(listOfUserGroups) == 0:
                msg = 'Вы не зарегистрированы ни на одну группу, напишите команду "Регистрация"'
                self.SendMessage(peerid, msg, 3)
            else:
                for item in listOfUserGroups:
                    self.onetimeschedule(peerid, item[1], item[2], item[3])

        elif msgeLower == "расписание на":
            msg = 'Пожалуйста укажите площадку: "Первая" или "Вторая"'
            self.SendMessage(peerid, msg, 4)
            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('onetime_setplate', peerid)
            self.c.execute(cmd)
            self.conn.commit()

            cmd = "INSERT INTO onetimeschedule(id) VALUES (%d)" % peerid
            self.c.execute(cmd)
            self.conn.commit()

        elif msgeLower == "команды":
            msg = 'Меню команд'
            self.SendMessage(peerid, msg, 1)

        elif msgeLower == "назад":
            msg = 'Главное меню'
            self.SendMessage(peerid, msg, 3)

        elif msgeLower == "убрать клавиатуру":
            msg = 'Вы уверены?'
            self.SendMessage(peerid, msg, 5)
            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('hide_ask', peerid)
            self.c.execute(cmd)
            self.conn.commit()

        elif msgeLower == "отмена":
            userState = self.GetUserState(peerid)
            if userState != '' and userState != 'onetime' and userState != 'deleting':
                self.DestroyInRegistration(peerid)
                msg = 'Главное меню'
                self.SendMessage(peerid, msg, 3)

        else:
            state = self.GetUserState(peerid)[0]
            # Если статус == установить площадку, то берем и записываем данные из сообщения в базу с помощью метода и т.д
            if state == "setplate":
                self.SetPlate(peerid, msgeLower)
            elif state == "setclass":
                self.SetClass(peerid, msgeLower)
            elif state == "setparameter":
                self.SetParameter(peerid, msge)
            elif state == "deleting":
                self.DeleteUser(peerid, msge)
            elif state == 'onetime_setplate':
                self.OnetimeSetPlate(peerid, msgeLower)
            elif state == 'onetime_setclass':
                self.OnetimeSetClass(peerid, msgeLower)
            elif state == 'onetime_setparameter':
                self.OnetimeSetParameter(peerid, msge)
            elif state == 'hide_ask':
                if msgeLower == "да":
                    self.SendMessage(peerid, "Клавиатура убрана, теперь она не будет вам мешать, чтобы включить"
                                             "ее назад, просто напишите боту что либо")
                    cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('', peerid)
                    self.c.execute(cmd)
                    self.conn.commit()
                else:
                    self.SendMessage(peerid, "Отмена отключения клавиатуры...", 3)
            else:
                self.TalkWithBot(peerid, msge)

    def StartRegistration(self, peerid):
        cmd = "INSERT INTO subscriptions(id) VALUES (%d)" % peerid
        self.c.execute(cmd)
        self.conn.commit()
        # Переход к сл. шагу и отсылка сл. требований
        cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('setplate', peerid)
        self.c.execute(cmd)
        self.conn.commit()
        msg = 'Пожалуйста укажите площадку: "Первая" или "Вторая"'
        self.SendMessage(peerid, msg, 4)

    def SetPlate(self, peerid, plate):
        plate = plate.replace("(на шапошникова)", "")
        plate = plate.replace("(на студенческой)", "")
        if plate == 'первая' or plate == 'вторая':
            if plate == 'первая':
                intPlate = 1
            else:
                intPlate = 2
            cmd = "UPDATE subscriptions SET plate = %d WHERE id = %d AND plate IS null" % (intPlate, peerid)
            self.c.execute(cmd)
            self.conn.commit()
            # Ставим state на указание class
            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('setclass', peerid)
            self.c.execute(cmd)
            self.conn.commit()
            # Отправка сообщения с просьбой о введении class
            msg = 'Укажите кто вы: "Преподаватель" или "Студент"'
            self.SendMessage(peerid, msg, 2)
        else:
            errorMessage = "Пожалуйста укажите площадку правильно: 'Первая' или 'Вторая'"
            self.SendMessage(peerid, errorMessage, 4)

    def SetClass(self, peerid, Class):
        if Class == "преподаватель" or Class == "студент":
            if Class == "преподаватель":
                Class = "teacher"
                msg = 'Укажите ФИО, например Базин Е.С.'
                self.SendMessage(peerid, msg, 0)
            else:
                Class = "student"
                msg = 'Укажите Группу, например 2ПКС-17-1к (Вы можете не указывать первую цифру (курс), тогда ' \
                      'вам не надо будет регистрироваться при переходе на следующий курс)'
                self.SendMessage(peerid, msg, 0)

            cmd = "UPDATE subscriptions SET class = '%s' WHERE id = %d AND class IS null" % (Class, peerid)
            self.c.execute(cmd)
            self.conn.commit()

            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('setparameter', peerid)
            self.c.execute(cmd)
            self.conn.commit()
        else:
            errorMessage = 'Пожалуйста укажите кто вы правильно: "Преподаватель" или "Студент"'
            self.SendMessage(peerid, errorMessage, 2)

    def SetParameter(self, peerid, Parameter):
        # TODO Список всех групп и преподавателей, поиск по нему и вывод совпадений

        cmd = "SELECT plate, class FROM subscriptions WHERE id=%d AND parameter IS NULL" % peerid
        self.c.execute(cmd)
        lastRegData = self.c.fetchone()

        self.c.execute("SELECT parameter, plate FROM subscriptions WHERE id = %d AND plate=%d AND parameter = '%s'" % (peerid, lastRegData[0], Parameter))
        result = self.c.fetchall()
        print(result)

        if len(result) == 0:
            cmd = "UPDATE subscriptions SET parameter = '%s' WHERE id = %d AND parameter IS NULL" % (Parameter, peerid)
            self.c.execute(cmd)
            self.conn.commit()

            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('', peerid)
            self.c.execute(cmd)
            self.conn.commit()

            msg = 'Вы успешно зарегистрированы!'
            self.SendMessage(peerid, msg, 3)
            print(lastRegData)
            # 0 - площадка
            isFirstTime = self.InsertIntoPlate(lastRegData[0], lastRegData[1], Parameter)
            self.onetimeschedule(peerid, lastRegData[0], lastRegData[1], Parameter, first_time=isFirstTime)

        else:
            self.SendMessage(peerid, "Вы уже подписаны на этого преподавателя/группу", 3)
            self.onetimeschedule(peerid, lastRegData[0], lastRegData[1], Parameter)
            self.DeleteUser(peerid, Parameter)


    def OnetimeSetPlate(self, peerid, plate):
        plate = plate.replace("(на шапошникова)", "")
        plate = plate.replace("(на студенческой)", "")
        if plate == 'первая' or plate == 'вторая':
            if plate == 'первая':
                intPlate = 1
            else:
                intPlate = 2
            cmd = "UPDATE onetimeschedule SET plate = %d WHERE id = %d AND plate IS null" % (intPlate, peerid)
            self.c.execute(cmd)
            self.conn.commit()
            # Ставим state на указание class
            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('onetime_setclass', peerid)
            self.c.execute(cmd)
            self.conn.commit()
            # Отправка сообщения с просьбой о введении class
            msg = 'Укажите кто вы: "Преподаватель" или "Студент"'
            self.SendMessage(peerid, msg, 2)
        else:
            errorMessage = "Пожалуйста укажите площадку правильно: 'Первая' или 'Вторая'"
            self.SendMessage(peerid, errorMessage, 4)


    def OnetimeSetClass(self, peerid, Class):
        if Class == "преподаватель" or Class == "студент":
            if Class == "преподаватель":
                Class = "teacher"
                msg = 'Укажите ФИО, например Базин Е.С.'
                self.SendMessage(peerid, msg, 0)
            else:
                Class = "student"
                msg = 'Укажите Группу, например 2ПКС-17-1к (Вы можете не указывать первую цифру (курс), тогда ' \
                      'вам не надо будет регистрироваться при переходе на следующий курс)'
                self.SendMessage(peerid, msg, 0)

            cmd = "UPDATE onetimeschedule SET class = '%s' WHERE id = %d AND class IS null" % (Class, peerid)
            self.c.execute(cmd)
            self.conn.commit()

            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('onetime_setparameter', peerid)
            self.c.execute(cmd)
            self.conn.commit()
        else:
            errorMessage = 'Пожалуйста укажите кто вы правильно: "Преподаватель" или "Студент"'
            self.SendMessage(peerid, errorMessage, 2)


    def OnetimeSetParameter(self, peerid, parameter):
        cmd = "SELECT plate, class FROM onetimeschedule WHERE id=%d" % peerid
        self.c.execute(cmd)
        result = self.c.fetchone()
        print(result[0])
        self.SendMessage(peerid, self.rand_phrases[random.randint(0, len(self.rand_phrases))], 3)
        self.onetimeschedule(peerid, result[0], result[1], parameter)

        cmd = "DELETE FROM onetimeschedule WHERE id = %d" % peerid
        self.c.execute(cmd)
        self.conn.commit()

        cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('', peerid)
        self.c.execute(cmd)
        self.conn.commit()

    def DestroyInRegistration(self, peerid):
        cmd = "DELETE FROM subscriptions WHERE id=%d AND parameter IS NULL" % peerid
        self.c.execute(cmd)
        self.conn.commit()

        cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('', peerid)
        self.c.execute(cmd)
        self.conn.commit()

    def DeleteUser(self, peerid, parameter):
        if "Площадка 1" in parameter:
            plate = 1
        elif "Площадка 2" in parameter:
            plate = 2
        else:
            plate = 1

        parameter = parameter.replace(" (Площадка 1)", "")
        parameter = parameter.replace(" (Площадка 2)", "")
        cmd = "SELECT plate, class FROM subscriptions WHERE id = %d AND parameter = '%s' AND plate = %d" % (peerid, parameter, plate)
        self.c.execute(cmd)
        result = self.c.fetchone()
        if result is not None:
            self.DeleteFromPlate(result[0], result[1], parameter)
            print(result[0])
            cmd = "DELETE FROM subscriptions WHERE id = %d AND parameter = '%s' AND plate = %s" % (peerid, parameter, result[0])
            self.c.execute(cmd)
            self.conn.commit()
            self.SendMessage(peerid, "Профиль " + str(parameter) + " успешно удален", 3)
        else:
            self.SendMessage(peerid, "Вы не подписаны на профиль " + str(parameter), 3)
        os.remove('JSONS_to_delete/' + str(peerid) + '.json')

        cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('', peerid)
        self.c.execute(cmd)
        self.conn.commit()


    def generateJSONToDelete(self, peerid):
        self.c.execute('SELECT parameter, plate FROM subscriptions WHERE id=%d' % peerid)
        matching = self.c.fetchall()
        data = {}
        data['one_time'] = True
        data['buttons'] = []
        for param in matching:
            data['buttons'].append([{
                "action": {
                    "type": "text",
                    "label": param[0] + " (Площадка " + str(param[1]) + ")"
                },
                "color": "positive"

            }])
        data['buttons'].append([{
            "action": {
                "type": "text",
                "label": "Назад"
            },
            "color": "negative"
        }])
        with open('JSONS_to_delete/' + str(peerid) + '.json', 'w', encoding='utf-8') as outfile:
            json.dump(
                data, outfile, ensure_ascii=False
            )


    def addNewUser(self, peerid):
        cmd = "SELECT id FROM users WHERE id = %d" % (int(peerid))
        self.c.execute(cmd)
        result = self.c.fetchone()
        if result is None:
            # LogManager.AddLog(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S") + '  Добавил пользователя
            # %s(%d) в таблицу Users' % (self.GetName(peerid, 'nom'), peerid))
            cmd = "INSERT INTO users(id, status) VALUES (%d, '')" % (int(peerid))
            self.c.execute(cmd)
            self.conn.commit()

    def SendMessage(self, peerid, mesg, keyboard=None):
        if keyboard is not None:
            self.vk.messages.send(
                peer_id=peerid,
                message=mesg,
                keyboard=open(self.keyBoardList[keyboard], "r", encoding="UTF-8").read(),
                random_id=self.random_id()
            )
        else:
            self.vk.messages.send(
                peer_id=peerid,
                message=mesg,
                random_id=self.random_id()
            )

    def TalkWithBot(self, peerid, message):
        request_from_google = apiai.ApiAI('2ec1776470d340a5a793ff5afa92b63b').text_request()  # Токен API к Dialogflow
        request_from_google.lang = 'ru'  # На каком языке будет послан запрос
        request_from_google.session_id = 'BatlabAIBot'  # ID Сессии диалога (нужно, чтобы потом учить бота)
        request_from_google.query = message  # Посылаем запрос к ИИ с сообщением от юзера
        response_json = json.loads(request_from_google.getresponse().read().decode('utf-8'))
        try:
            response = response_json['result']['fulfillment']['speech']

            if response:
                self.SendMessage(peerid, response, 3)
            else:
                self.SendMessage(peerid, "Я вас не понял", 3)
        except:
            pass

    def InsertIntoPlate(self, plate, Class, parameter):
        cmd = "SELECT subscription_count FROM subscriptions_info_%d WHERE parameter = '%s' AND class = '%s'" % (
            plate,
            parameter,
            Class
        )
        self.c.execute(cmd)
        result = self.c.fetchone()
        if result is None:
            cmd = "INSERT INTO subscriptions_info_%d(subscription_count, class, parameter) VALUES(1, '%s', '%s')" % (
                plate,
                Class,
                parameter)
            self.c.execute(cmd)
            self.conn.commit()
            return True
        else:
            cmd = "UPDATE subscriptions_info_%d SET subscription_count = %d WHERE parameter = '%s' AND class = '%s'" % (
                plate, result[0] + 1, parameter, Class
            )
            self.c.execute(cmd)
            self.conn.commit()
            return False


    def DeleteFromPlate(self, plate, Class, parameter):
        cmd = "SELECT subscription_count FROM subscriptions_info_%d WHERE parameter = '%s' AND class = '%s'" % (
            int(plate), parameter, Class
        )
        self.c.execute(cmd)
        result = self.c.fetchone()
        if result[0] == 1:
            cmd = "DELETE FROM subscriptions_info_%d WHERE class = '%s' AND parameter = '%s'" % (int(plate),
                                                                                                 Class,
                                                                                                 parameter)
            self.c.execute(cmd)
            self.conn.commit()
        else:
            cmd = "UPDATE subscriptions_info_%d SET subscription_count = %d WHERE parameter = '%s' AND class = '%s'" % (
                int(plate),
                result[0] - 1,
                parameter,
                Class
            )

            self.c.execute(cmd)
            self.conn.commit()


    def GetUserState(self, peerid):
        cmd = "SELECT status FROM users WHERE id = %d" % (int(peerid))
        self.c.execute(cmd)
        state = self.c.fetchone()
        return state


    def GetUserDataFromSubscriptions(self, peerid):
        cmd = "SELECT * FROM subscriptions WHERE id=%d" % peerid
        self.c.execute(cmd)
        result = self.c.fetchall()
        return result

    def DeleteAllFinaly(self, peerid):
        cmd = "SELECT parameter FROM subscriptions WHERE id = %d" % peerid
        self.c.execute(cmd)
        result = self.c.fetchall()
        print(result[0][0])
        for parameter in result:
            parameter = parameter[0]
            cmd = "SELECT plate, class FROM subscriptions WHERE id = %d AND parameter = '%s'" % (peerid, parameter)
            self.c.execute(cmd)
            result = self.c.fetchone()
            if result is not None:
                self.DeleteFromPlate(result[0], result[1], parameter)

                cmd = "DELETE FROM subscriptions WHERE id = %d AND parameter = '%s'" % (peerid, parameter)
                self.c.execute(cmd)
                self.conn.commit()

            cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('', peerid)
            self.c.execute(cmd)
            self.conn.commit()

    def SetUserStatus(self, peerid, status):
        cmd = "UPDATE users SET status = '%s' WHERE id = %d" % (status, peerid)
        self.c.execute(cmd)
        self.conn.commit()

messg = None


def Start(onetimeschedule):
    global messg
    messg = Messg(onetimeschedule)
    app.run(debug=False, host='192.168.0.60', port=80)


@app.route('/', methods=['POST'])
def ReturnAnswer():
    # Не забудь на основном боте поставит секретный ключ для колбэкапи
    data = json.loads(request.data)
    print(data)
    type = data['type']
    object = data['object']
    if data['secret'] == config.callbackapi_secret_key:
        # time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
        if type == 'message_new':
            peer_id = object['peer_id']
            msg = object['text']
            if peer_id < 2000000000:
                # name = Messg(onetimes).GetName(peer_id, 'nom')
                # LogManager.AddLog(time + '  ' + name + '(' + str(peer_id) + '): ' + msg)
                messg.checkMessage(msg, peer_id)
            else:
                msg = msg.replace('[club170013824|@nrtkbotvk], ', '')
                msg = msg.replace('[club170013824|@nrtkbotvk] ', '')
                msg = msg.replace('[club170013824|*nrtkbotvk] ', '')
                msg = msg.replace('[club170013824|Расписание НРТК] ', '')

                messg.checkMessage(msg, peer_id)

        elif type == 'group_leave':
            peer_id = object['user_id']
            messg.SetUserStatus(peer_id, 'left')
            messg.SendMessage(peer_id, "Вы отписались от бота, ваш профиль полностью удален", 3)
            try:
                messg.DeleteAllFinaly(peer_id)
            except:
                return 'ok'

        elif type == 'group_join':
            peer_id = object['user_id']
            try:
                if messg.GetUserState(peer_id)[0] == 'left':
                    messg.SetUserStatus(peer_id, '')
                    messg.SendMessage(peer_id, "Добро пожаловать назад!", 3)
            except:
                print(123)
                pass

        elif type == 'message_deny':
            peer_id = object['user_id']
            messg.DeleteAllFinaly(peer_id)
    print('ok')
    return 'ok'
