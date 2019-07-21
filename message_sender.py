from time import time, sleep
from datetime import datetime
from random import randint

from requests import post

from threading import Thread

import config


class Sender:
    def __init__(self):
        self.url = 'https://api.vk.com/method/execute?code=return [%s];&v=5.101&access_token=' + config.vk_token

        self.works = True
        self.turn_vip = []
        self.turn = []

        self.time = time()

    def sender(self):
        while True:
            if not self.turn == []:
                attributes = ''
                messages = self.turn[:25]

                for message in messages:
                    message['random_id'] = randint(-100000000, 1000000000000000)
                    attributes += 'API.messages.send(%s),' % str(message)

                """
                if (time() - self.time) < 0.3333334: sleep(0.3333334 - (time() - self.time))
                print(time() - self.time)
                self.time = time()
                """

                print('Sender/%s/%ix/messages=%s//' % (str(datetime.now()), len(messages),  messages))
                answer = post(self.url % attributes).json()

                del self.turn[:len(messages)]
            else:
                sleep(0.01)
                if not self.works: break
                continue

    def start(self):
        self.works = True
        Sender = Thread(target=self.sender, name='Sender')
        Sender.start()

    def stop(self):
        self.works = False

    def add(self, peer_id, message='', keyboard=None, attachment=None, priority=False):
        attributes = {'peer_id': peer_id}

        attributes['message'] = message
        if keyboard != None: attributes['keyboard'] = keyboard
        if attachment != None: attributes['attachment'] = attachment

        self.turn.append(attributes)


if __name__ == '__main__':
    Sender = Sender()
    Sender.start()
    i = 0
    while True:
        #id = 265868386
        id = 284964657
        m = 'Земля лох'

        Sender.add(id, message=m)
        i += 1