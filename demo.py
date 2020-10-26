#!/usr/bin/env python3

import requests
import time
import argparse
import os
import json
import pymysql

from requests.compat import urljoin
from datetime import datetime

class BotHandler(object):
    """
        BotHandler is a class which implements all back-end of the bot.
        It has tree main functions:
            'get_updates' — checks for new messages
            'send_message' – posts new message to user
            'get_answer' — computes the most relevant on a user's question
    """

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
 

    def get_updates(self, offset=None, timeout=30):
        params = {"timeout": timeout, "offset": offset}
        raw_resp = requests.get(urljoin(self.api_url, "getUpdates"), params)
        try:
            resp = raw_resp.json()
        except json.decoder.JSONDecodeError as e:
            print("Failed to parse response {}: {}.".format(raw_resp.content, e))
            return []

        if "result" not in resp:
            return []
        return resp["result"]

    def send_message(self, chat_id, text):
        params = {"chat_id": chat_id, "text": text}
        return requests.post(urljoin(self.api_url, "sendMessage"), params)

    def get_answer(self, question):
        if question == '/start':
            return "Hi, I am your project bot. How can I help you today?"
        return "Welcome Back"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='')
    return parser.parse_args()


def is_unicode(text):
    return len(text) == len(text.encode())

class DBManagement(object):
    def __init__(self, username,password,dbName):
        self.db = pymysql.connect("localhost",username,password,dbName)
        self.cursor=self.db.cursor()

    def insertIntoRecords(self,itsNo,pageNo,pages,miqatId,recType):
        sql = """INSERT INTO RECORDS(ITS_ID,PAGE_NO,PAGES,MIQAT_ID,REC_TYPE) VALUES("""+str(itsNo)+""","""+str(pageNo)+""","""+str(pages)+""","""+str(miqatId)+""",'"""+recType+"""')"""
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except Exception as ex:
            self.db.rollback()
            print(ex)

        return False

    def insertIntoMiqats(self,miqatName):
        sql = """INSERT INTO MIQATS(MIQAT_NAME) VALUES('"""+miqatName+"""')"""
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except Exception as ex:
            self.db.rollback()
            print(ex)

        return False

    def getMiqatById(self,miqatId):
        sql = "SELECT * FROM MIQATS  WHERE MIQAT_ID="+str(miqatId)
        miqat=""
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if(len(results)==0):
                return "No such Miqat Found"

            for row in results:
                miqat=row[1]

        except Exception as ex:
            print(ex)
            return "Error: unable to fetch data"

        return miqat

    def insertIntoKhatamRecords(self,miqatId,month,year,pages,khatam):
        sql = """INSERT INTO KHATAM_RECORDS(MIQAT_ID,MONTH,YEAR,PAGE_COUNT,KHATAM_COUNT) VALUES("""+str(miqatId)+""","""+str(month)+""","""+str(year)+""","""+str(pages)+""","""+str(khatam)+""")"""
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except Exception as ex:
            self.db.rollback()
            print(ex)

        return False

    def updateKhatamRecords(self,miqatId,month,year,pages,khatam):
        sql = """UPDATE KHATAM_RECORDS SET PAGE_COUNT="""+str(pages)+""",KHATAM_COUNT="""+str(khatam)+""" WHERE MIQAT_ID="""+str(miqatId)+""" AND MONTH="""+str(month)+""" AND YEAR="""+str(year)
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True
        except Exception as ex:
            self.db.rollback()
            print(ex)

        return False

    def getKhatamRecordByMiqat(self,miqatId,month,year):
        sql="""SELECT * FROM KHATAM_RECORDS WHERE MIQAT_ID="""+str(miqatId)+""" AND MONTH="""+str(month)+""" AND YEAR="""+str(year)
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if(len(results)==0 or len(results)>=2):
                return None

            return results[0]

        except Exception as ex:
            print(ex)
            return None


class DBService(object):
    def __init__(self, dbObject):
        self.dbObj=dbObject

    def insertNewRecordForPages(self,list):
        if(self.dbObj.insertIntoRecords(list[0],list[3][0],list[3][1],list[1][0],list[3][2])):
            record=self.dbObj.getKhatamRecordByMiqat(list[1][0],list[1][1],list[1][2])
            if(not record is None):
                newPageCount=record[3]+list[3][1]
                newKhatam=record[4]
                if(newPageCount>=604):
                    newKhatam=newKhatam+1
                    newPageCount=newPageCount-604

                if(self.dbObj.updateKhatamRecords(record[0],record[1],record[2],newPageCount,newKhatam)):
                    return True

        return False



class MiqatManger(object):
    def __init__(self):
        self.miqatId=1
        self.month=0
        self.year=0

    def getCurrentMiqat(self):
        return (self.miqatId,self.month,self.year)



class Allocation(object):
    """
    Class description will be mentioned soon
    """
    
    def __init__(self, url):
        self.api_url = url
        self.pages=1
        self.cancelledList=[] #This list records recitations which were cancelled and allots them when new user comes.
        self.recitationsDict={}


    def enterInDict(self,chatId,itsId,miqat):
        tempList=[]
        tempList.append(itsId)
        tempList.append(miqat)
        tempList.append(datetime.now()) # Timestamp will help us in deleting those entries in recitationsDict which are not touched in last 2(threshold could be changed) hours 
        self.recitationsDict[chatId]=tempList
        return "Your account is now active. Use / or /help for a list of options. \n \n Note: The bot will allocate pages according to the Misri Quran script."

    def checkKey(self,chatId):
        if chatId in self.recitationsDict:
            return True
        else:
            return False

    def assignPages(self,chatId,record):
        list=self.recitationsDict[chatId]
        list.append(record)
        list.append("Alloted")

        self.recitationsDict[chatId]=list

        if(record[0]+record[1]>=606):
            return "Your page allocation for TODAY is as follows: \n \nPage/Safa No: "+str(record[0])+"  to  Page/Safa No: "+str(604)+"\n"+self.api_url+str(record[0])+"\n AND \n Page/Safa No: "+str(1)+"to Page/Safa No: "+str(record[1]-(604-record[0]+1))+"\n"+self.api_url+str(1)+"\n \nReply\n'Done' - if recitation is completed or \n'Cancel' - if you are unable to recite."
        else:
            return "Your page allocation for TODAY is as follows: \n \nPage/Safa No: "+str(record[0])+"  to  Page/Safa No: "+str(record[0]+record[1]-1)+"\n"+self.api_url+str(record[0])+"\n \nReply\n'Done' - if recitation is completed or \n'Cancel' - if you are unable to recite."


    def allocatePages(self,chatId,pages):
        if(not self.checkKey(chatId)):
            return "Please Enter your ITS Id to activate your account"

        if(len(self.cancelledList)!=0):
            for record in self.cancelledList:
                if(record[1]==pages and record[2]=="P"):
                    tRecord=record
                    self.cancelledList.remove(tRecord)
                    return self.assignPages(chatId,tRecord)

        
        if(self.pages+pages>=606):
            # bot.send_message(chat_id,"Your page allocation for TODAY is as follows: \n \nPage/Safa No: "+str(pages)+"  to  Page/Safa No: "+str(pages+2)+"\n"+page_url+str(pages)+"\n Recite remaining pages from this Link \n"+page_url+str(1)+"\n If you want to recite next time than type '/start'")
            tupple=(self.pages,pages,"P")
            self.pages=self.pages+pages-604
            return self.assignPages(chatId,tupple)
        else:
            # bot.send_message(chat_id,"Your page allocation for TODAY is as follows: \n \nPage/Safa No: "+str(pages)+"  to  Page/Safa No: "+str(pages+2)+"\n"+page_url+str(pages)+"\n \nReply\n'Done' - if recitation is completed or \n'Cancel' - if you are unable to recite.")
            tupple=(self.pages,pages,"P")
            self.pages=self.pages+pages
            if(self.pages==605):
                self.pages=1
            return self.assignPages(chatId,tupple)

    def checkForAllocation(self,chatId):
        if(not self.checkKey(chatId)):
            return False

        list=self.recitationsDict[chatId]
        if(len(list)>=4):
            return True

        return False  

    def showDict(self):
        print("Dictionary: ")
        print(self.recitationsDict)
        print("Cancel List: ")
        print(self.cancelledList)              
        
    def doneRecitation(self,chatId,dbServiceObj):
        if(not self.checkKey(chatId)):
            return "Please Enter your ITS Id to activate your account"

        if(not self.checkForAllocation(chatId)):
            return "Please use / or /help to allocate Recitation"

        list=self.recitationsDict[chatId]
        list[4]="Done"
        self.recitationsDict[chatId]=list
        self.showDict()
        if(not dbServiceObj.insertNewRecordForPages(list)):
            return "Recitation Submission Failed"
        
        return "Recitation Submitted Successfully"

    def cancelRecitation(self,chatId,miqat):
        if(not self.checkKey(chatId)):
            return "Please Enter your ITS Id to activate your account"

        if(not self.checkForAllocation(chatId)):
            return "Please use / or /help to allocate Recitation"

        list=self.recitationsDict[chatId]
        record=list[3]
        if(miqat==list[1]):
            self.cancelledList.append(record)
        del self.recitationsDict[chatId]
        self.showDict()
        return "Recitation Cancelled"

def main():
    args = parse_args()
    token = args.token

    if not token:
        if not "TELEGRAM_TOKEN" in os.environ:
            print("Please, set bot token through --token or TELEGRAM_TOKEN env variable")
            return
        token = os.environ["TELEGRAM_TOKEN"]

    bot = BotHandler(token)
    pages=1
    quran_api_url="http://www.easyquran.com/quran-jpg/htmlpage2.php?uri=" # Page specific url
    allocationObj=Allocation(quran_api_url)
    databaseObj=DBManagement("root","yaahusain","qm_bot")
    dbServiceObj=DBService(databaseObj)
    miqatMangObj=MiqatManger()

    print("Ready to talk!")
    offset = 0
    while True:
        updates = bot.get_updates(offset=offset)
        for update in updates:
            print("An update received.")
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                if "text" in update["message"]:
                    text = update["message"]["text"]
                    if is_unicode(text):
                        print("Text: {}".format(text))
                        if(text=="/start"):
                            bot.send_message(chat_id,"Please enter your ITS ID to proceed further. \n Shukran")
                        elif(len(text)==8 and text.isdigit()):
                            bot.send_message(chat_id,allocationObj.enterInDict(chat_id,text,miqatMangObj.getCurrentMiqat()))
                            
                        elif(text=="/" or text=="/help"):
                            bot.send_message(chat_id,"You may use following commands.\n \n /onesipara- Use this command to get one sipara allocated for recitation.\n /onepage-Use this command to get one safa/page allocated for recitation.\n /threepages - Use this command to get three pages allocated for recitation.\n /fivepages - Use this command to get five pages allocated for recitation.\n /tenpages - Use this command to get ten pages allocated for recitation.\n /fifteenpages - Use this command to get fifteen pages allocated for recitation.\n /help - Use this command to get list of available commands.\n /contact - Use this command to send your queries/suggestions/feedbacks.")
                        elif(text=="/onepage"):
                            bot.send_message(chat_id,allocationObj.allocatePages(chat_id,1))
                            
                        elif(text=="/threepages"):
                            bot.send_message(chat_id,allocationObj.allocatePages(chat_id,3))
                           
                        elif(text=="Done" or text=="done" or text=="DONE"):
                            bot.send_message(chat_id,allocationObj.doneRecitation(chat_id,dbServiceObj))

                        elif(text=="Cancel" or text=="cancel" or text=="CANCEL"):
                            bot.send_message(chat_id,allocationObj.cancelRecitation(chat_id,miqatMangObj.getCurrentMiqat()))

                        else:
                            bot.send_message(chat_id,"Please Enter Proper Input")
                        
                    else:
                        bot.send_message(chat_id, "Hmm, you are sending some weird characters to me...")

                    allocationObj.showDict()
            offset = max(offset, update['update_id'] + 1)
        time.sleep(1)

if __name__ == "__main__":
    main()