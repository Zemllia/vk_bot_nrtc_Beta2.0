import json
import LogManager,config
import random
from datetime import datetime
import psycopg2
import main

from threading import Thread

#Все для вк! Моря и ААААКеаны, все для вк!! ДЛЯЯЯ ВВВВВКККККК (Все библеотеки для вк)
import vk_api



class Messg:
    from vk_api.longpoll import VkEventType
    from vk_api.bot_longpoll import VkBotEventType
    def __init__(self):
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
        self.keyBoardList = ["json/cancel.json","json/commands.json","json/isTeacher.json","json/menu.json","json/plate.json"]




    Random = 0
    rand_phrases = ['Всегда пожалуйста', 'Вот ваше расписание', 'Машины скоро захва... то есть вот ваше расписание', 'Бот к вашим услугам :)', 'Не благодарите, просто напишите спасибо))']

    def random_id(self):
        self.Random
        self.Random += random.randint(0, 1000000000000000)
        return self.Random

    def checkMessage(self, msge:str, peerid):
        self.addNewUser(peerid)
        msgeLower = msge.lower()
        if msgeLower == 'привет':
            msg = 'Привет! Напиши мне "Расписание!"'
            self.SendMessage(peerid, msg, 3)
            LogManager.AddLog(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S") + '  Отправка сообщения пользователю %s(%d): "Привет"' % (self.GetName(peerid, 'nom'), peerid))

        elif msgeLower == "регистрация":
            if(self.GetUserState(peerid) == ""):
                msg = "Вы уже проходите регистрацию"
                state = self.GetUserState(peerid)
                keyboardInt = 0
                if(state == "setplate"):
                    keyboardInt = 4
                elif(state == "setclass"):
                    keyboardInt = 2
                elif(state == "setParameter"):
                    keyboardInt = 0
                self.SendMessage(peerid, msg, keyboardInt)
            else:
                self.StartRegistration(peerid)
                LogManager.AddLog(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S") + '  Запрос на регистрацию от %s(%d), peerid = ' % (self.GetName(peerid, 'nom'), peerid))

        else:
            state = self.GetUserState(peerid)[0]
            print(state)
            if(state == "setplate"):
                self.SetPlate(peerid, msgeLower)
            elif(state == "setclass"):
                self.SetClass(peerid, msgeLower)
            elif(state == "setparameter"):
                self.SetParameter(peerid, msgeLower)



    def StartRegistration(self, peerid):
        cmd = "INSERT INTO subscriptions(id) VALUES (%d)" % (peerid)
        self.c.execute(cmd)
        self.conn.commit()
        #Переход к сл. шагу и отсылка сл. требований
        cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('setplate', peerid)
        self.c.execute(cmd)
        self.conn.commit()
        msg = 'Пожалуйста укажите площадку: "Первая" или "Вторая"'
        self.SendMessage(peerid, msg, 4)

    def SetPlate(self, peerid, plate):
        #intPlate = 0
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
                msg = 'Укажите Группу, например 2ПКС-17-1к (Довольно важно указать в таком виде, иначе могут появиться некоторые проблемы, в будущем обязательно сделаем удобнее)'
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
        #TODO Список всех групп и преподавателей, поиск по нему и вывод совпадений
        cmd = "UPDATE subscriptions SET parameter = '%s' WHERE id = %d AND parameter IS null" % (Parameter, peerid)
        self.c.execute(cmd)
        self.conn.commit()

        cmd = "UPDATE users SET status = '%s' WHERE id = %d" % ('', peerid)
        self.c.execute(cmd)
        self.conn.commit()

        msg = 'Вы успешно зарегистрированы!'
        self.SendMessage(peerid, msg, 3)
        lastRegData = self.GetUserDataFromSubscriptions(peerid)[-1]
        main.one_time_schedule(peerid, lastRegData[1], lastRegData[3])


#----------------------------------------------------------------------------------------------------------------------
#TODO Он пишет, что профиль удален в любом случае
    def deleteUser(self, curid, group):
        print(123);

    def generateJSONToDelete(self, curid):
        self.curid = curid
        self.c.execute('SELECT parameter FROM subscriptions_playground_1 WHERE id=%d' % (self.curid,))
        matching = self.c.fetchall()
        print(matching);
        data = {}
        data['one_time'] = True
        data['buttons'] = []
        for param in matching:
            data['buttons'].append([{
                "action": {
                    "type": "text",
                    "label": param[0]
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
        print(data)
        with open(str(self.curid)+'.json', 'w', encoding='utf-8') as outfile:
            json.dump(
                data, outfile,ensure_ascii=False
            )

    def addNewUser(self, peerid):
        cmd = "SELECT id FROM users WHERE id = %d" % (int(peerid))
        self.c.execute(cmd)
        result = self.c.fetchone()
        if result == None:
            LogManager.AddLog(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S") + '  Добавил пользователя %s(%d) в таблицу Users' % (self.GetName(peerid, 'nom'), peerid))
            cmd = "INSERT INTO users(id, status) VALUES (%d, '')" % (int(peerid))
            self.c.execute(cmd)
            self.conn.commit()

    def SendMessage(self, peerid, mesg, keyboard):
        self.vk.messages.send(
            peer_id=peerid,
            message=mesg,
            keyboard=open(self.keyBoardList[keyboard], "r", encoding="UTF-8").read(),
            random_id=self.random_id()
        )

    def chk(self):
        while True:
            for event in self.blongpoll.listen():
                if event.type == self.VkBotEventType.MESSAGE_NEW:
                    peerid = event.raw['object']['peer_id']
                    msge = event.raw['object']['text']
                    time = self.GetTime()
                    if event.from_user:
                        name = self.GetName(peerid, 'nom')
                        LogManager.AddLog(str(time) + '  ' + name +': ' + str(msge))
                        self.checkMessage(msge=msge, peerid=peerid)
                    else:
                        if '[club170013824|@nrtkbotvk] ' in msge:
                            msge= msge.replace('[club170013824|@nrtkbotvk] ', '')
                        elif '[club170013824|расписание нртк] ' in msge:
                            msge = msge.replace('[club170013824|расписание нртк] ', '')

                        LogManager.AddLog(time + '  ' + self.GetName(peerid, 'nom') + '(' + str(peerid) + '): ' + msge)
                        self.checkMessage(msge=msge, peerid=peerid)

    def GetName(self,peerid, name_case):
        if(peerid < 2000000001):
            name = self.vk.users.get(user_id=peerid, fields = 'nickname', name_case=name_case)
            name = str(name[0]['first_name']) + ' '+ str(name[0]['last_name'])
            return name
        else:
            name = self.vk._method("messages.getChat", {"chat_id": peerid})
            print(name)


    def GetTime(self):
        time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
        return time

    def GetUserState(self, peerid):
        cmd = "SELECT status FROM users WHERE id = %d" % (int(peerid))
        self.c.execute(cmd)
        state = self.c.fetchone()
        return state

    def GetUserDataFromSubscriptions(self, peerid):
        cmd = "SELECT * FROM subscriptions WHERE id=%d" % (peerid)
        self.c.execute(cmd)
        result = self.c.fetchall()
        return result

    def AddToCurPlate(self):
        print("Add to cur plate")

messg = Messg()
messg.chk()
