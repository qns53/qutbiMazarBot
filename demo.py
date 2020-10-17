#!/usr/bin/env python3

import requests
import time
import argparse
import os
import json

from requests.compat import urljoin

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


class SimpleDialogueManager(object):
    """
    This is the simplest dialogue manager to test the telegram bot.
    Your task is to create a more advanced one in dialogue_manager.py."
    """
    
    def generate_answer(self, question): 
        return "Hello, world!" 
        

def main():
    args = parse_args()
    token = args.token

    if not token:
        if not "TELEGRAM_TOKEN" in os.environ:
            print("Please, set bot token through --token or TELEGRAM_TOKEN env variable")
            return
        token = os.environ["TELEGRAM_TOKEN"]

    #################################################################
    
    # Your task is to complete dialogue_manager.py and use your 
    # advanced DialogueManager instead of SimpleDialogueManager. 
    
    # This is the point where you plug it into the Telegram bot. 
    # Do not forget to import all needed dependencies when you do so.
    
    #simple_manager = SimpleDialogueManager()
    #bot = BotHandler(token, simple_manager)

 
    bot = BotHandler(token)
    pages=1
    page_url="http://www.easyquran.com/quran-jpg/htmlpage2.php?uri="
    ###############################################################

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
                            bot.send_message(chat_id,"Your account is now active. Use / or /help for a list of options. \n \n Note: The bot will allocate pages according to the Misri Quran script.")
                        elif(text=="/" or text=="/help"):
                            bot.send_message(chat_id,"You may use following commands.\n \n /onesipara- Use this command to get one sipara allocated for recitation.\n /onepage-Use this command to get one safa/page allocated for recitation.\n /threepages - Use this command to get three pages allocated for recitation.\n /fivepages - Use this command to get five pages allocated for recitation.\n /tenpages - Use this command to get ten pages allocated for recitation.\n /fifteenpages - Use this command to get fifteen pages allocated for recitation.\n /help - Use this command to get list of available commands.\n /contact - Use this command to send your queries/suggestions/feedbacks.")
                        elif(text=="/onepage"):
                            bot.send_message(chat_id,"Your page allocation for TODAY is as follows: \n Page/Safa No: "+str(pages)+"\n"+page_url+str(pages)+"\n Reply\n "Done" - if recitation is completed or  \n "Cancel" - if you are unable to recite.")
                            pages=pages+1
                            if(pages==605):
                                pages=1
                        elif(text=="/threepages"):
                            if(pages+3>=606):
                                bot.send_message(chat_id,"Your page allocation for TODAY is as follows: \n Page/Safa No: "+str(pages)+" to Page/Safa No: "+str(pages+2)+"\n"+page_url+str(pages)+"\n Recite remaining pages from this Link \n"+page_url+str(1)+"\n If you want to recite next time than type '/start'")
                                pages=pages+3-604
                            else:
                                bot.send_message(chat_id,"Your page allocation for TODAY is as follows: \n Page/Safa No: "+str(pages)+" to Page/Safa No: "+str(pages+2)+"\n"+page_url+str(pages)+"\n Reply\n "Done" - if recitation is completed or  \n "Cancel" - if you are unable to recite.")
                                pages=pages+3
                                if(pages==605):
                                    pages=1
                        else:
                            bot.send_message(chat_id,"Please Enter Proper Input")
                        
                    else:
                        bot.send_message(chat_id, "Hmm, you are sending some weird characters to me...")
            offset = max(offset, update['update_id'] + 1)
        time.sleep(1)

if __name__ == "__main__":
    main()