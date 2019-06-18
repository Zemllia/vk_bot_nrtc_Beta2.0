import psycopg2

import time
from datetime import datetime

conn = psycopg2.connect(
                                    host='95.79.50.190',
                                    database='Test',
                                    user='sergey',
                                    password='743790644ftG'
                                    )
c = conn.cursor()

print('Connect ...')

i = 0
while True:
    c.execute("INSERT INTO test (id, data) VALUES (%i, '%s')" % (i, str(datetime.today())))
    conn.commit()
    print(i)
    time.sleep(60*60)
    i += 1