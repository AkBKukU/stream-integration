#!/usr/bin/python3
from stream.api_base import APIbase

import urllib.request, json

import urllib.error

class APIserver(APIbase):
    """API Base for signal emitters

    Manages loading API keys, logging, and registering signal recievers
    """

    def __init__(self,key_path=None,log=False,server_url=None):
        """Init with file path"""
        super().__init__(key_path)
        self.service_name = "Server API"
        self.server_url = server_url

        self.api_chat = []
        self.api_interact = []
        self.api_donate = []
        self.api_buffer = 30
        self.update_rate = 500



    async def connect(self):
        self.delay_callback("get_chat", self.update_rate, self.get_chat)
        self.delay_callback("get_donate", self.update_rate, self.get_donate)
        self.delay_callback("get_interact", self.update_rate, self.get_interact)

    async def get_chat(self):
        try:
            with urllib.request.urlopen(self.server_url+"/api/chat.json") as url:
                data = json.load(url)



            for i in range(0,len(data)):
                newmessage=True
                for j in range(0,len(self.api_chat)):
                    if data[i]["timestamp"] == self.api_chat[j]["timestamp"]:
                        newmessage=False

                if newmessage:
                    if len(self.api_chat) > self.api_buffer:
                        self.api_chat.pop(0)
                    self.api_chat.append(data[i])
                    message={
                        "from": data[i]["from"],
                        "color": data[i]["color"],
                        "text": data[i]["text"],
                        "donate": data[i]["donate"]
                    }
                    self.emit_chat(message)


            self.delay_callback("get_chat", self.update_rate, self.get_chat)
        except Exception as e:
            self.delay_callback("get_chat", self.update_rate, self.get_chat)
            return

    async def get_donate(self):
        try:
            with urllib.request.urlopen(self.server_url+"/api/donate.json") as url:
                data = json.load(url)



            for i in range(0,len(data)):
                newmessage=True
                for j in range(0,len(self.api_donate)):
                    if data[i]["timestamp"] == self.api_donate[j]["timestamp"]:
                        newmessage=False

                if newmessage:
                    if len(self.api_donate) > self.api_buffer:
                        self.api_donate.pop(0)
                    self.api_donate.append(data[i])

                    self.emit_donate(data[i]['from'],
                        str(data[i]['amount']),
                        data[i]['text']
                        )


            self.delay_callback("get_donate", self.update_rate, self.get_donate)

        except Exception as e:
            self.delay_callback("get_donate", self.update_rate, self.get_donate)
            return

    async def get_interact(self):
        try:
            with urllib.request.urlopen(self.server_url+"/api/interact.json") as url:
                data = json.load(url)



            for i in range(0,len(data)):
                print(data[i]["from"])
                newmessage=True
                for j in range(0,len(self.api_interact)):
                    if data[i]["timestamp"] == self.api_interact[j]["timestamp"]:
                        newmessage=False

                if newmessage:
                    if len(self.api_interact) > self.api_buffer:
                        self.api_interact.pop(0)
                    self.api_interact.append(data[i])

                    self.emit_interact(data[i]['from'],
                        data[i]['kind'],
                        data[i]['text']
                        )


            self.delay_callback("get_interact", self.update_rate, self.get_interact)

        except Exception as e:
            self.delay_callback("get_interact", self.update_rate, self.get_interact)
            return



