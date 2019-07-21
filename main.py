import message_sender
from event_handler import event_handler
from parsers.parser1 import parser1
from parsers.parser2 import parser2


Sender = message_sender.Sender()
Sender.start()

Parser1 = parser1.Parser(Sender.add)
Parser1.start()

Parser2 = None #parser2.Parser(Sender.add)
#Parser2.start()


def one_time_schedule(user_id, plate, class_, parameter):
    if plate == 1:
        Parser1.single(user_id, class_, parameter)

    elif plate == 2:
        Parser2.single(user_id, class_, parameter)


# Запуск оброботика событий
event_handler.main(one_time_schedule)