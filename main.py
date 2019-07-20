import message_sender
import event_handler.messages
from event_handler import event_handler
from parsers.parser1 import parser1
from parsers.parser2 import parser2

import config


Sender = message_sender.Sender(config.vk_token)
Sender.start()

Parser1 = parser1.Parser(Sender.add)
Parser1.start()

Parser2 = parser2.Parser(Sender.add)
Parser2.start()




def one_time_schedule(user_id, place, class_, parameter, record=False):
    if place == 1:
        Parser1.single(user_id, class_, parameter, record)

    elif place == 2:
        Parser2.single(user_id, class_, parameter, record)


# Запуск оброботика событий
event_handler.main(Sender.add, one_time_schedule)