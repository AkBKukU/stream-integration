#!/usr/bin/python3
from stream.api_twitch import APItwitch

from pprint import pprint
import asyncio
from uuid import UUID
import json
import time
import os
import glob
from datetime import datetime
import random

from multiprocessing import Process, Manager, Value, Array

class APItwitchTest(APItwitch):
    """Twitch API test

    An empty twitch test class that extends the full class. Looks for json
    data from log files in "test/" folder.
    """

    def __init__(self,key_path=None,log=False,auth_token=None):
        """Init with file path"""
        super().__init__(key_path)
        self.service_name = "TwitchTest"
        self.procs = []
        self.fake_votes=[
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go North",
                "Go South",
                "Go South",
                "Go South",
                "Go South",
                "Go South",
                "Go South",
                "Go South",
                "Eat Sword https://google.com",
                "Pet Grue http://akbkuku.org",
                "Lick Dirt https://zombo.com",
                "Stab self with sword https://xkcd.com",
                "jump in chasm https://caps.wiki",
                "eat egg",
                "look",
                "1",
                "1",
                "1",
                "1",
                "1",
                "1",
                "1",
                "1",
                "2",
                "2",
                "2",
                "throw sword"
                ]
        self.fake_names=[
            {"from":"Fred","color":""},
            {"from":"Felicia","color":""},
            {"from":"Bob","color":""},
            {"from":"Betty","color":""},
            {"from":"James","color":""},
            {"from":"Jane","color":""},
            {"from":"Lorem","color":""},
            {"from":"ipsum","color":""},
            {"from":"dolor","color":""},
            {"from":"sit","color":""},
            {"from":"amet","color":""},
            {"from":"more","color":""},
            {"from":"less","color":""},
            {"from":"vim","color":""},
            {"from":"fstab","color":""},
            {"from":"dir","color":""},
            {"from":"type","color":""},
            {"from":"Z AA","color":""},
            {"from":"A ZA","color":""},
            {"from":"A AZ","color":""},
            {"from":"A","color":""}
        ]

    async def process(self):
        """multiprocess background task to look for test files"""


        # Create random colors from names
        random.shuffle(self.fake_names)
        random.shuffle(self.fake_votes)
        color="#"
        for c in list((self.fake_names[0]["from"]+"mmm").replace(" ","").lower()[:3].encode('ascii')):
            c=(c-80)
            c=c*6
            color+=str(hex(c))[2:]

        # Build chat message
        message={
                "from": self.fake_names[0]["from"],
                "uid": "twitchtest-"+self.fake_names[0]["from"],
                "color": color,
                "text": self.fake_votes[0]+"",
                "time": str(datetime.now().isoformat()).replace(":","-"),
                "donate": 0
            }
        self.emit_chat(message)
        self.delay_callback("fake_data", 1000, self.process)
        return


    async def connect(self):
        """Override parent API connection and start background test"""
        print("Not Connecting to twitch")
        #self.delay_callback("fake_data", 1000, self.process)
        #self.delay_callback("log_replay", 1000, self.log_replay)
        return


    async def disconnect(self):
        """Override parent API connection and end background test"""
        print("Not Disconnecting to twitch")

        # Force any background processes to end
        for proc in self.procs:
            proc.terminate()
        return

