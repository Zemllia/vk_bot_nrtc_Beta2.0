import message_sender

from event_handler import messages

from parsers.parser1 import parser1
from parsers.parser2 import parser2


Sender = message_sender.Sender()
Sender.start()

Parser1 = parser1.Parser(Sender.add)
Parser1.start()

Parser2 = parser2.Parser(Sender.add)
Parser2.start()


def one_time_schedule(user_id, plate, class_, parameter, first_time=False):
    if plate == 1:
        Parser1.single(user_id, class_, parameter, first_time)

    elif plate == 2:
        Parser2.single(user_id, class_, parameter, first_time)


messager = messages.Start(one_time_schedule)
messager.Start()

