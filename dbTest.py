#!/usr/bin/python3

import pymysql

# Open database connection
db = pymysql.connect("localhost","root","yaahusain","demo1")

cursor = db.cursor()

sql = """CREATE TABLE EMPLOYEE (
   FIRST_NAME  CHAR(20) NOT NULL,
   LAST_NAME  CHAR(20),
   AGE INT,
   INCOME FLOAT )"""

cursor.execute(sql)
print(db)
# disconnect from server
db.close()

