#!/usr/bin/python3
from stream.api_base import APIbase
try:
    from twitchAPI.twitch import Twitch
    from twitchAPI.eventsub import EventSub
    from twitchAPI.helper import first
    from twitchAPI.oauth import UserAuthenticationStorageHelper
    from twitchAPI.type import AuthScope
    from twitchAPI.chat import Chat, ChatMessage, ChatEvent
except:
    print("No Twitch API")
    class ChatMessage(object):

        def __init__(self):
            self.totally_real_member = 0


from pprint import pprint
import asyncio
from uuid import UUID
import json
from pathlib import PurePath
import glob, os


class APItwitch(APIbase):
    """Twitch API with signal emitters for bits, subs, and point redeems

    Manages authentication and creating messages from API events to use elsewhere
    """

    def __init__(self,key_path=None,log=False,auth_token=None):
        """Init with file path"""
        super().__init__(key_path)
        self.service_name = "Twitch"
        self.auth_token = auth_token
        self.buffer_subs = []
        self.sub_coalesce_delay = 500
        


    async def connect(self):
        """Connect to Twith API"""
        print("Connect to twitch")
        self.api = await Twitch(self.client_id, self.client_secret)

        # Scope for API to allow reading different data types
        #TODO - Update Scopes
        target_scope = [
            AuthScope.CHANNEL_READ_REDEMPTIONS,
            AuthScope.BITS_READ,
            AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
            AuthScope.CHAT_READ,
            AuthScope.CHAT_EDIT
        ]

        # Build user auth with local storage
        helper = UserAuthenticationStorageHelper(self.api,
                                              target_scope,
                                              storage_path=PurePath(self.auth_token))
        # Connect to API
        await helper.bind()

        # Get user for channel to watch
        self.user = await first(self.api.get_users(logins=['TechTangents']))

        # Starting up EventSub
        #self.eventsub = EventSub(self.api)
        #self.eventsub.start()

        # Get chat interface
        self.chat = await Chat(self.api, initial_channel=['TechTangents'])

        # Register callbacks for pubsub actions
        #self.uuid_points = await self.pubsub.listen_channel_subscription_message(self.user.id, self.callback_points)
        #self.uuid_bits = await self.pubsub.listen_bits(self.user.id, self.callback_bits)
        #self.uuid_subs = await self.pubsub.listen_channel_subscriptions(self.user.id, self.callback_subs)


        self.chat.register_event(ChatEvent.MESSAGE, self.callback_chat)
        self.delay_callback("log_replay", 1000, self.log_replay)
        self.chat.start()

        return

    async def log_replay(self):
        # Check for point redeem
        for file in glob.glob("test-twitch/*_points.log"):
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    data = json.load(f)
                    await self.callback_points("1337", data)
                os.remove(file)
        
        # Check for bit cheer
        for file in glob.glob("test-twitch/*_bits.log"):
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    data = json.load(f)
                    await self.callback_bits("1337", data)
                os.remove(file)

        # Check for subs
        for file in glob.glob("test-twitch/*_subs.log"):
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    print("Sending Sub")
                    data = json.load(f)
                    await self.callback_subs("1337", data)
                os.remove(file)

        self.delay_callback("log_replay", 1000, self.log_replay)


    async def disconnect(self):
        """Gracefully disconnect from Twith API"""

        # End pubsub connections
        #await self.pubsub.unlisten(self.uuid_points)
       # await self.pubsub.unlisten(self.uuid_bits)
       # await self.pubsub.unlisten(self.uuid_subs)
        self.eventsub.stop()

        # End chat
        self.chat.stop()

        # Close API
        await self.api.close()

        await self.cancel_delays()
        return

    async def callback_points(self, uuid: UUID, data: dict):
        """Point redeem handler"""
        self.log("callback_points",json.dumps(data))

        # Validate user provided text
        if 'user_input' in data['data']['redemption']:
            text=str(""+str(data['data']['redemption']['user_input']))
        else:
            text=""

        # Send data to receivers
        self.emit_interact(data['data']['redemption']['user']['display_name'],
                            data['data']['redemption']['reward']['title'],
                            text
                            )
        return

    async def callback_chat(self, chat: ChatMessage):

        if chat.user.color == None:
             # Create random colors from names
            color="#"
            for c in list((chat.user.name+"mmm").replace(" ","").lower()[:3].encode('ascii')):
                c=(c-80)
                c=c*6
                color+=str(hex(c))[2:]
        else:
            color = chat.user.color

        message={
                "from": chat.user.display_name,
                "color": color,
                "text": self.message_prep(chat),
                "donate": chat.bits
            }

        self.log("callback_chat",json.dumps(message))
        if chat.user.mod or chat.user.display_name == "TechTangents":
            print("Mod chat: "+message["text"][0:1])
            if message["text"][0:1] == "!":
                self.emit_interact(chat.user.display_name,
                                    "Mod Chat Command",
                                    message["text"]
                                    )
        self.emit_chat(message)
        return


    async def callback_bits(self, uuid: UUID, data: dict):
        """Bit cheer handler"""
        self.log("callback_bits",json.dumps(data))

        # Send data to receivers
        self.emit_donate(data['data']['user_name'],
                            str(data['data']['bits_used'])+"b",
                            data['data']['chat_message']
                            )
        return

    async def message_prep(message_data):

        # https://static-cdn.jtvnw.net/emoticons/v1/$EMOTE_ID/1.0

        message_html = message_data.text

        return message_html

    async def sub_prep(event_data):

        line = event_data.user_name
        # Get plain english version of sub level
        sub_type=""
        if (str(event_data.tier) == "1000"):
            sub_type="tier one"
        if (str(event_data.tier) == "2000"):
            sub_type="tier two"
        if (str(event_data.tier) == "3000"):
            sub_type="tier three"
        if (str(event_data.tier) == "Prime"):
            sub_type="prime"

        sub_len=""
        if hasattr(event_data, "cumulative_months"):
            sub_len="for "+str(int(event_data.cumulative_months))+" months"
        else:
            sub_len="for the first time"


        if hasattr(event_data, "total") or (hasattr(event_data, "is_gift") and event_data.is_gift):
            #gift sub
        elif hasattr(event_data, "message"):
            # self sub
            line += " subbed as "+sub_type+" "+sub_len+" and says "+self.sub_prep(data.event)
        return line

    async def callback_subscription_message(data):
        # https://pytwitchapi.dev/en/stable/modules/twitchAPI.object.eventsub.html#twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent

        self.emit_donate(data.event.user_name,
                            str(data.event.tier)+"s",
                            self.sub_prep(data.event)
                            )

    async def callback_flush_subs(self):

        if len(self.buffer_subs) == 1:
            await self.callback_sub_single("1337",self.buffer_subs[0])
            self.buffer_subs.pop(0)
        else:
            gift_data={}
            gift_data['context'] = "subgift"
            gift_data['display_name']=""
            gift_count=0
            for data in  self.buffer_subs:
                if str(data['context']) ==  "subgift":
                    if gift_data['display_name'] == "":
                        gift_data['display_name'] = data['display_name']
                        gift_data['user_name'] = data['user_name']
                        gift_data['sub_plan'] = data['sub_plan']

                    if gift_data['display_name'] == data['display_name']:
                        gift_count+=1
                    else:
                        gift_data['recipient_display_name'] = str(gift_count) + " viewers"
                        await self.callback_sub_single("1337",gift_data)
                        gift_data['display_name'] = data['display_name']
                        gift_data['user_name'] = data['user_name']
                        gift_data['sub_plan'] = data['sub_plan']
                        gift_count=1

            if gift_data['display_name'] != "":
                gift_data['recipient_display_name'] = str(gift_count) + " viewers"
                await self.callback_sub_single("1337",gift_data)

            self.buffer_subs.clear()


    async def callback_sub_single(self, uuid: UUID, data: dict):
        """Subscription handler"""
        self.log("callback_subs",json.dumps(data))

        # Determine length of sub
        sub_len=""
        if ('benefit_end_month' in data and data['benefit_end_month'] != 0):
            sub_len="for "+str(int(data['benefit_end_month'])+1)+" months"
        if ('multi_month_duration' in data and data['multi_month_duration'] > 1):
            sub_len="for "+str(data['multi_month_duration'])+" months"

        # Sub type and build output message
        line=""
        if str(data['context']) ==  "subgift":
            line=str(data['display_name'])
            line += " gave a "+sub_type+" gift sub "+sub_len+" to "+str(data['recipient_display_name'])
        elif str(data['context']) ==  "anonsubgift" or str(data['context']) ==  "anonresubgift":
            line += "Anonymous gifter gave a "+sub_type+" gift sub "+sub_len+" to "+str(data['recipient_display_name'])
        else:
            line=str(data['display_name'])
            line += " subbed as "+sub_type+" "+sub_len+" and says "+str(data['sub_message']['message'])
            if data['display_name'] == "baljemmett":
                line.replace("sub","subb")

        # Send data to receivers
        print("emitting sub")
        self.emit_donate(data['user_name'],
                            str(data['sub_plan'])+"s",
                            line
                            )
        return

