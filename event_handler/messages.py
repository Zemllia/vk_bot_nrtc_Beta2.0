import json
import os
import random

class Messg:
    from vk_api.longpoll import VkEventType
    def __init__(self, longpoll, c, vk,vk_api, parser,conn):
        self.longpoll = longpoll
        self.c = c
        self.vk = vk
        self.vk_api = vk_api
        self.parser = parser
        self.conn = conn

    Random = 0

    def random_id(self):
        self.Random
        self.Random += random.randint(0, 1000000000000000)
        return self.Random

    def sendIfRegistered(self, mainEvent, class_, parameter, record):
        self.parser.single(mainEvent.user_id, class_, parameter.lower(),record)

    def checkMessage(self, event):
        print(event.user_id)
        self.curid = event.user_id
        """c.execute('SELECT id FROM users WHERE id=?', (event.user_id,))
        matching = c.fetchone()
        if matching == None:
            addNewUser(event)"""

        self.msg = event.text.lower()
        if self.msg == 'привет':
            self.addNewUser(event)
            if event.from_user:
                self.vk.messages.send(
                    user_id=event.user_id,
                    message='Привет, напиши слово Расписание',
                    keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                    random_id=self.random_id()
                )

        elif self.msg == 'расписание':
            self.addNewUser(event)
            self.c.execute('SELECT id FROM subscriptions_playground_1 WHERE id=%d' % (self.curid,))
            matching = self.c.fetchone()
            print('Запрос на расписание ', matching)
            if matching is None:
                self.vk.messages.send(
                    user_id=event.user_id,
                    message='Вы не зарегистрированы, напишите команду "Регистрация"',
                    keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                    random_id = self.random_id()
                )
            else:
                self.vk.messages.send(
                    user_id=event.user_id,
                    message='Расписание',
                    keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                    random_id = self.random_id()
                )
                self.c.execute('SELECT parameter, class FROM subscriptions_playground_1 WHERE id=%d' % (self.curid,))
                print('Выбор пользователя: ',matching)
                matching = self.c.fetchall()
                for predmet in matching:
                    parameter = predmet[0]
                    class_ = predmet[1]
                    print(parameter,class_)
                    self.sendIfRegistered(event, class_, parameter, record=False)

        elif self.msg == 'помощь':
            self.addNewUser(event)
            self.vk.messages.send(
                user_id=event.user_id,
                message='Расписание - узнать расписание на сегодня \n Помощь - список команд \n Регистрация - зарегистрироваться на постоянную рассылку расписания',
                keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                random_id = self.random_id()
            )

        elif self.msg == 'регистрация':
            self.addNewUser(event)
            self.registerNewUser(event)

        elif self.msg == 'удалить профиль':
            self.addNewUser(event)
            self.c.execute('SELECT id FROM subscriptions_playground_1 WHERE id=%d' % (self.curid,))
            if self.c.fetchone() is None:
                self.vk.messages.send(
                    user_id=event.user_id,
                    message='Вы не зарегистрированы',
                    keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                    random_id = self.random_id()
                )
            else:
                self.generateJSON(event)
                self.vk.messages.send(
                    user_id=event.user_id,
                    message='Укажите группу для удаления',
                    keyboard=open(str(event.user_id)+".json", "r", encoding="UTF-8").read(),
                    random_id = self.random_id()
                )
                self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                          ('deleting', self.curid))

        elif self.msg == 'команды':
            self.vk.messages.send(
                user_id=event.user_id,
                message='Доступные вам команды"',
                keyboard=open("json/commands.json", "r", encoding="UTF-8").read(),
                random_id = self.random_id()
            )

        elif self.msg == 'назад':
            self.vk.messages.send(
                user_id=event.user_id,
                message='Главное меню',
                keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                random_id = self.random_id()
            )
            self.c.execute('SELECT status FROM users WHERE id=%d' % (self.curid,))
            matching = self.c.fetchone()[0]
            if matching == 'deleting':
                os.remove(str(event.user_id)+".json")
                self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                          ('', self.curid))
                self.conn.commit()

        else:
            self.addNewUser(event)
            self.c.execute('SELECT status FROM users WHERE id=%d' % (self.curid))
            matching = self.c.fetchone()[0]
            if matching == '':
                self.c.execute('SELECT * FROM subscriptions_playground_1 WHERE id=%d' % (self.curid,))
                print(self.c.fetchone())
                self.vk.messages.send(
                    user_id=event.user_id,
                    message='Такой команды нет, напишите "Помощь"',
                    keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                    random_id = self.random_id()
                )
            elif matching == 'deleting':
                print('выполняю делит')
                self.deleteUser(event, self.msg)
            elif matching == 'afterRegister':
                self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                          ('', self.curid))
                self.vk.messages.send(
                    user_id=self.curid,
                    message='С помощью команды "Расписание", вы можете узнать расписание для групп, на которые подписаны',
                    keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
                    random_id=self.random_id()
                )
                self.conn.commit()

    def addNewUser(self, curevent):

        curid = curevent.user_id
        self.c.execute('SELECT id FROM users WHERE id=(%d)' % (curid))
        matching = self.c.fetchone()
        print(matching)
        if matching == None:
            self.c.execute("INSERT INTO users VALUES (%d, '%s')" % (curid, ''))
            #conn.commit()
        else:
            self.checkStep(curevent)

    def checkStep(self, curevent):
        self.curid = curevent.user_id
        self.c.execute('SELECT status FROM users WHERE id=(%d)' % (self.curid))
        matching = self.c.fetchone()[0]
        if curevent.text.lower() == 'отмена' and matching != '':
            self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                      ('afterRegister', self.curid))
            self.conn.commit()
            try:
                self.c.execute("DELETE FROM subscriptions_playground_1 WHERE id =%d AND (class IS NULL OR parameter IS NULL)" %
                          (self.curid,))
                self.conn.commit()
            except:
                return
            return
        #Здесь запускаем метод, который записывает площадку и выводим сообщение о запросе
        if matching == 'firststep':
            self.firstStep(curevent)
        #Здесь запускаем метод, который записывает группу/ФИО и переходим на конечный шаг
        elif matching == 'secondstep':
            self.secondStep(curevent)

    def firstStep(self, curevent):
        curid = curevent.user_id
        self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                  ('secondstep', curid))
        self.conn.commit()
        if curevent.text.lower() == 'студент':
            self.vk.messages.send(
                user_id=curid,
                message='Укажите группу',
                keyboard=open("json/cancel.json", "r", encoding="UTF-8").read(),
                random_id=self.random_id()
            )
            self.c.execute("UPDATE subscriptions_playground_1 SET class = '%s' WHERE id = %d AND class IS NULL" %
                      ('student', curid,))
            self.conn.commit()
        elif curevent.text.lower() == 'преподаватель':
            self.vk.messages.send(
                user_id=curid,
                message='Укажите ваше ФИО(например Базин Е.С.)',
                keyboard=open("json/cancel.json", "r", encoding="UTF-8").read(),
                random_id=self.random_id()
            )
            self.c.execute("UPDATE subscriptions_playground_1 SET class = '%s' WHERE id = %d AND class IS NULL" %
                      ('teacher', curid,))
            self.conn.commit()
        else:
            self.vk.messages.send(
                user_id=curid,
                message='Укажите правмльный вариант(Студент/Преподаватель)',
                keyboard=open("json/cancel.json", "r", encoding="UTF-8").read(),
                random_id=self.random_id()
            )
            self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                      ('firststep', curid))

    def secondStep(self, curevent):
        curid = curevent.user_id
        self.c.execute('SELECT parameter FROM subscriptions_playground_1 WHERE id=%d AND parameter IS NULL' % (self.curid))
        self.conn.commit()
        matching = self.c.fetchall()
        match = False
        for a in matching:
            if a[0] == curevent.text.lower():
                match = True
        if match != True:
            self.vk.messages.send(
                user_id=curid,
                message='Вы успешно зарегистрированы',
                keyboard=open("json/commands.json", "r", encoding="UTF-8").read(),
                random_id=self.random_id()
            )
            self.c.execute("UPDATE subscriptions_playground_1 SET parameter = '%s' WHERE id = %d AND parameter IS NULL" %
                      (curevent.text.lower(), curid))
            self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                      ('afterRegister', curid))
            self.conn.commit()
            self.c.execute('SELECT parameter,class FROM subscriptions_playground_1 WHERE id=%d' % (curid,))
            self.conn.commit()
            self.matching = self.c.fetchall()
            print(self.matching)
            self.parameter = self.matching[-1][0]
            self.class_ = self.matching[-1][1]
            print(self.parameter,self.class_)
            self.sendIfRegistered(curevent, self.class_, self.parameter, record=True)
        else:
            self.vk.messages.send(
                user_id=curid,
                message='Вы уже подписаны на эту группу',
                random_id=self.random_id()
            )
            self.destroyInRegistration(curevent)

    def destroyInRegistration(self, curevent):
        self.curid = curevent.user_id
        try:
            self.c.execute("DELETE FROM subscriptions_playground_1 WHERE id =%d AND parameter IS NULL)" %
                      (self.curid,))
            self.conn.commit()
        except:
            return
        self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" % ('afterRegister', self.curid))
        self.conn.commit()

    def registerNewUser(self, curevent):
        curid = curevent.user_id
        self.vk.messages.send(
            user_id=curid,
            message='Укажите кем вы являетесь(Преподаватель/Студент)',
            keyboard=open("json/isTeacher.json", "r", encoding="UTF-8").read(),
            random_id=self.random_id()
        )
        self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                  ('firststep', curid))
        self.c.execute("INSERT INTO subscriptions_playground_1(id) VALUES (%d)" %
                  (curid,))
        self.conn.commit()

    def deleteUser(self, curevent, group):
        self.curid = curevent.user_id
        self.c.execute("DELETE FROM subscriptions_playground_1 WHERE id = %d AND parameter = '%s'" %
                  (self.curid, group,))
        self.conn.commit()
        self.vk.messages.send(
            user_id=curevent.user_id,
            message='Профиль успешно удален',
            keyboard=open("json/menu.json", "r", encoding="UTF-8").read(),
            random_id = self.random_id()
        )
        self.c.execute("UPDATE users SET status = '%s' WHERE id = %d" %
                  ('', self.curid))
        self.conn.commit()
        os.remove(str(curevent.user_id)+".json")

    def generateJSON(self, curevent):
        self.curid = curevent.user_id
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

    def chk(self):
        while True:
            for event in self.longpoll.listen():
                if event.type == self.VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    print(event.user_id)
                    self.checkMessage(event)