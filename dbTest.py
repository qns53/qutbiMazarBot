#!/usr/bin/python3

import pymysql

# Open database connection
db = pymysql.connect("localhost","root","yaahusain","demo1")

cursor = db.cursor()

sql = """INSERT INTO EMPLOYEE(FIRST_NAME,
   LAST_NAME, AGE,INCOME)
   VALUES ('Mac', 'Mohan', 20, 2000.23)"""
try:
   # Execute the SQL command
   cursor.execute(sql)
   # Commit your changes in the database
   db.commit()
except:
   # Rollback in case there is any error
   db.rollback()

print(db)
# disconnect from server
db.close()

