#!/usr/bin/python3
from stream.api_base import APIbase

import googleapiclient.discovery
import googleapiclient.errors

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

from pprint import pprint
import json
import httplib2
from pathlib import PurePath
import glob, os
from iso4217 import Currency


""" Youtube Live Chat API Logic

Init API:
1. Connect to API
2. Get list of live broadcasts
3. Check if is active

If active broadcast
1. Get initial list of chat messages
2. store page token
3. wait ms delay
4. requst chat update
5. goto 2


This means the youtube API is going to need its own rolling interupt for querying
the server to get updated chats. When the broadcast ends I suspect the API will
continue to provide blank page tokens and delays, some method may be needed to
check for when the stream ends.

"""
class APIyoutube(APIbase):
    """Twitch API with signal emitters for bits, subs, and point redeems

    Manages authentication and creating messages from API events to use elsewhere
    """

    def __init__(self,key_path=None,log=False,auth_token=None):
        """Init with file path"""
        super().__init__(key_path)
        self.service_name = "Youtube"
        self.auth_token = auth_token

        # Stream info
        self.broadcasts=[]
        self.broadcast_index=0
        self.broadcast_active=False
        self.chat_token=None
        self.chat_slow=1
        self.chat_slow_add=0
        self.chat_slow_refresh=20


    async def connect(self):
        """Connect to Twith API"""
        print("Connect to youtube")

        api_service_name = "youtube"
        api_version = "v3"

        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

        flow = OAuth2WebServerFlow(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=scopes,
            redirect_uri="http://localhost"
        )

        # TODO - Fix token location
        storage = Storage(self.auth_token)
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            flags = argparser.parse_args(args=[])
            credentials = run_flow(flow, storage, flags)

        self.api = googleapiclient.discovery.build(
            api_service_name, api_version,
            http=credentials.authorize( httplib2.Http() )
        )


        self.delay_callback("get_broadcasts", 1000, self.get_broadcasts)
        self.delay_callback("log_replay", 1000, self.log_replay)
        return

    async def log_replay(self):
        # Check for subs
        for file in glob.glob("test-youtube/*_chat.log"):
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    print("Sending Chat")
                    data = json.load(f)
                    await self.callback_chat(data)
                os.remove(file)

        self.delay_callback("log_replay", 1000, self.log_replay)

    async def disconnect(self):
        """Google is read only, no need to disconnect"""

        await self.cancel_delays()
        return


    def b_active(self, status):
        """ Validate stream is active """
        s={
            "complete": False,
            "created": False,
            "ready": False,
            "revoked": False,
            "testStarting": True,
            "testing": True,
            "live": True,
            "liveStarting": True,
        }
        return s[status]


    async def get_broadcasts(self):
        """ Get a list of all current broadcasts on a channel.
            Get the index of the first active broadcast.

            Start chat polling if there is am active broadcast
        """
        self.broadcast_active=False

        print("Broadcast Query")
        request = self.api.liveBroadcasts().list(
            part="snippet,contentDetails,status",
            broadcastType="all",
            mine=True
        )

        broadcasts = request.execute() # fill with API call

        self.log("broadcasts",json.dumps(broadcasts))
        self.broadcasts=[]
        self.broadcast_index=0
        print("Broadcast List:")
        print(pprint(broadcasts))
        i=0
        if broadcasts['items']:
            for b in broadcasts['items']:
                #print(pprint(b))
                # Data structure: https://developers.google.com/youtube/v3/live/docs/liveBroadcasts#resource-representation

                # Get index of first live active stream
                if self.b_active(b["status"]['lifeCycleStatus']) and not self.broadcast_active:
                    self.broadcast_index=i
                    self.broadcast_active=True

                self.broadcasts.append(
                    {
                    "id":b['id'],
                    "chat":b["snippet"]['liveChatId'],
                    "status":b["status"]['lifeCycleStatus']
                    }
                )

                i+=1


        if self.broadcast_active:
            # Start checking for chat
            print("Found Broadcast: "+self.broadcasts[self.broadcast_index]['id'])
            self.delay_callback("chat_polling", 1000, self.chat_update)
        else:
            self.chat_token=None

            # Continue checking for broadcast
            print("No active broadcasts found")
            self.delay_callback("get_broadcasts", 60000, self.get_broadcasts)


    def set_broadcast_pos(self,num):
        """ Override selected broadcast based on index
        """
        self.broadcast_index=num

    def set_chat_refresh_delay(self, delay):
        """ Option to slow down chat even more because the quota is limited
        """
        self.chat_slow_add = delay

    async def chat_update(self):
        """ Get chat messages based on page token
            Reruns after polling delay

            If there are no new messages check if stream is still live
        """
        print("chat update")
        request = self.api.liveChatMessages().list(
            liveChatId=self.broadcasts[self.broadcast_index]['chat'],
            pageToken="" if self.chat_token is None else self.chat_token,
            part="snippet,authorDetails"
        )
        chat = request.execute() # fill with API call
        self.log("chat",json.dumps(chat))

        self.chat_token = chat['nextPageToken']

        # Check for chat messages
        if len(chat['items']) > 0:

            # Reset slow scaling
            self.chat_slow = 1

            await self.callback_chat(chat)

            print("chat wait"+str(chat['pollingIntervalMillis']))
            # Get next batch of messages
            self.delay_callback("chat_polling", chat['pollingIntervalMillis']+100+self.chat_slow_add, self.chat_update)


        else:
            self.chat_slow += 1

            if self.chat_slow_refresh > self.chat_slow:
                # Slow chat scaling, increase update delay length to save API quota
                self.delay_callback("chat_polling", chat['pollingIntervalMillis']*self.chat_slow+self.chat_slow_add, self.chat_update)
            else:
                self.chat_slow = 1
                # Check if stream is live
                self.delay_callback("get_broadcasts", 30000, self.get_broadcasts)

        return

    async def callback_chat(self, chat):

        # Go through all messages
        for c in chat['items']:

            print("chat:")
            #print(pprint(c))
            c['authorDetails']['displayName']=c['authorDetails']['displayName'].replace("@","")
            # Create random colors from names
            color="#"
            letters=str(c['authorDetails']['displayName']).lower()[:3]
            print(letters)
            for col in list(letters.encode('ascii',errors='ignore')):
                col=(col-80)
                col=col*6
                color+=str(hex(col))[2:]

            message={
                    "from": c['authorDetails']['displayName'].encode('utf-8',errors='ignore').decode('utf-8'),
                    "uid": "youtube-"+c['authorDetails']['channelId'],
                    "color": color,
                    "text": str(c['snippet']['displayMessage']),
                    "donate": 0 # not currently used
                }
            #self.log("callback_chat",json.dumps(message))
            self.emit_chat(message)

            # Handle superchats
            if str(c['snippet']['type']) == "superChatEvent" :

                value = int(c['snippet']['superChatDetails']['amountMicros']) / 1000000

                # If the value is integral, convert it to an int
                if value == int(value):
                    value = int(value)

                # Build name to also state donate value
                name = c['authorDetails']['displayName'].encode('utf-8',errors='ignore').decode('utf-8')
                name += " gave " + str(value) + " " + Currency(c['snippet']['superChatDetails']['currency']).currency_name + " and "

                # Send data to receivers
                self.emit_donate({
                    "from_name":name,
                    "amount":str(value)+"b", # Youtube UI enforces min already
                    "message":c['snippet']['superChatDetails']['userComment']
                    })
