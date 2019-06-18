from time import time, sleep
from datetime import datetime

from requests import post

from threading import Thread


class Sender:
    def __init__(self, vk_token):
        self.vk_token = vk_token

        self.works = True
        self.turn_vip = []
        self.turn = []

        self.time = time()

    def send_message(self, message):
        attributes = ''
        for key in message:
            attributes += '%s=%s&' % (key, message[key])

        answer = post('https://api.vk.com/method/messages.send?%sv=5.38&access_token=%s' % (attributes, self.vk_token)).json()
        return answer

    def sender(self):
        while True:
            if not self.turn_vip == []:
                message = self.turn_vip[0]
                vip = True

            elif not self.turn == []:
                message = self.turn[0]
                vip = False

            else:
                sleep(0.01)
                if not self.works: break
                continue

            """
            if (time() - self.time) < 0.3333334: sleep(0.3333334 - (time() - self.time))
            print(time() - self.time)
            self.time = time()
            """

            print('Sender/%s/id=%s/message=%s' % (str(datetime.now()), message['peer_id'], message['message']))
            result = self.send_message(message)

            if vip: del self.turn_vip[self.turn_vip.index(message)]
            else: del self.turn[self.turn.index(message)]

    def start(self):
        self.works = True
        Thread(target=self.sender, name='Sender')

    def stop(self):
        self.works = False

    def add(self, peer_id, message=None, keyboard=None, attachment=None, priority=False):
        attributes = {'peer_id': peer_id}

        if message != None: attributes['message'] = message
        if keyboard != None: attributes['keyboard'] = keyboard
        if attachment != None: attributes['attachment'] = attachment

        if priority:
            self.turn_vip.append(attributes)
        else:
            self.turn.append(attributes)