#!/usr/bin/env python3

import requests
import time
import argparse
import os
import json

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


class Allocation(object):
    """
    Class description will be mentioned soon
    """
    
    def __init__(self, url):
        self.api_url = url
        self.pages=1
        self.cancelledList=[] #This list records recitations which were cancelled and allots them when new user comes.
        self.recitationsDict={}


    def enterInDict(self,chatId,itsId):
        tempList=[]
        tempList.append(itsId)
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
        if(not self.checkKey(chat_id)):
            return "Please Enter your ITS Id to activate your account"

        if(len(self.cancelledList)!=0):
            for record in self.cancelledList:
                if(record[1]==pages):
                    tRecord=record
                    self.cancelledList.remove(tRecord)
                    return self.assignPages(chatId,tRecord)

        else:
            if(self.pages+pages>=606):
                # bot.send_message(chat_id,"Your page allocation for TODAY is as follows: \n \nPage/Safa No: "+str(pages)+"  to  Page/Safa No: "+str(pages+2)+"\n"+page_url+str(pages)+"\n Recite remaining pages from this Link \n"+page_url+str(1)+"\n If you want to recite next time than type '/start'")
                tupple=(self.pages,pages)
                self.pages=self.pages+pages-604
                return self.assignPages(chatId,tupple)
            else:
                # bot.send_message(chat_id,"Your page allocation for TODAY is as follows: \n \nPage/Safa No: "+str(pages)+"  to  Page/Safa No: "+str(pages+2)+"\n"+page_url+str(pages)+"\n \nReply\n'Done' - if recitation is completed or \n'Cancel' - if you are unable to recite.")
                tupple=(self.pages,pages)
                self.pages=self.pages+pages
                if(self.pages==605):
                    self.pages=1
                return self.assignPages(chatId,tupple)

    def checkForAllocation(self,chatId):
        if(not self.checkKey(chatId)):
            return False

        list=self.recitationsDict[chatId]
        if(len(list)==4):
            return True

        return False  

    def showDict(self):
        print(self.recitationsDict)              
        
    def doneRecitation(self,chatId):
        if(not self.checkKey(chatId)):
            return "Please Enter your ITS Id to activate your account"

        if(not self.checkForAllocation(chatId)):
            return "Please use / or /help to allocate Recitation"

        list=self.recitationsDict[chatId]
        list[3]="Done"
        self.recitationsDict[chatId]=list
        self.showDict()
        return "Recitation Submitted Successfully"

    def cancelRecitation(self,chatId):
        if(not self.checkKey(chatId)):
            return "Please Enter your ITS Id to activate your account"

        if(not self.checkForAllocation(chatId)):
            return "Please use / or /help to allocate Recitation"

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
                            bot.send_message(chat_id,allocationObj.enterInDict(chat_id,text))
                            
                        elif(text=="/" or text=="/help"):
                            bot.send_message(chat_id,"You may use following commands.\n \n /onesipara- Use this command to get one sipara allocated for recitation.\n /onepage-Use this command to get one safa/page allocated for recitation.\n /threepages - Use this command to get three pages allocated for recitation.\n /fivepages - Use this command to get five pages allocated for recitation.\n /tenpages - Use this command to get ten pages allocated for recitation.\n /fifteenpages - Use this command to get fifteen pages allocated for recitation.\n /help - Use this command to get list of available commands.\n /contact - Use this command to send your queries/suggestions/feedbacks.")
                        elif(text=="/onepage"):
                            bot.send_message(chat_id,allocationObj.allocatePages(chat_id,1))
                            
                        elif(text=="/threepages"):
                            bot.send_message(chat_id,allocationObj.allocatePages(chat_id,3))
                           
                        elif(text=="Done" or text=="done" or text=="DONE"):
                            bot.send_message(chat_id,allocationObj.doneRecitation(chat_id))

                        elif(text=="Cancel" or text=="cancel" or text=="CANCEL"):
                            bot.send_message(chat_id,allocationObj.cancelRecitation(chat_id))

                        else:
                            bot.send_message(chat_id,"Please Enter Proper Input")
                        
                    else:
                        bot.send_message(chat_id, "Hmm, you are sending some weird characters to me...")
            offset = max(offset, update['update_id'] + 1)
        time.sleep(1)

if __name__ == "__main__":
    main()