#!/usr/bin/python3
from stream.api_base import APIbase
try:
    from twitchAPI.twitch import Twitch
    from twitchAPI.eventsub.websocket import EventSubWebsocket
    from twitchAPI.type import AuthScope
    from twitchAPI.helper import first
    from twitchAPI.oauth import UserAuthenticationStorageHelper
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
import bleach, re


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
        self.sub_skip = {}
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
            AuthScope.CHAT_EDIT,
            AuthScope.USER_READ_CHAT,
            AuthScope.CHANNEL_BOT,
            AuthScope.USER_BOT
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
        self.eventsub = EventSubWebsocket(self.api)
        self.eventsub.start()

        # Get chat interface
        self.chat = await Chat(self.api, initial_channel=['TechTangents'])

        # Register callbacks for pubsub actions
        self.uuid_points = await self.eventsub.listen_channel_points_custom_reward_redemption_add(self.user.id, self.callback_channel_points_custom_reward_redemption_add)
        self.uuid_notification = await self.eventsub.listen_channel_chat_notification(self.user.id, self.user.id, self.callback_channel_chat_notification)


        self.chat.register_event(ChatEvent.MESSAGE, self.callback_chat)

        self.replay_register("callback_chat_data", self.callback_chat, dictConvert=True)
        self.replay_register("callback_channel_chat_notification", self.callback_channel_chat_notification, dictConvert=True)
        self.replay_register("callback_channel_points_custom_reward_redemption_add", self.callback_channel_points_custom_reward_redemption_add, dictConvert=True)

        self.delay_callback("replay_check",1000,self.replay_check)
        self.chat.start()

        self.badge_custom={}
        for badge in await self.api.get_chat_badges(self.user.id):
            self.badge_custom[badge.set_id]=badge.to_dict()

        self.log("get_chat_badges",json.dumps(self.badge_custom))

        self.badge_global={}
        for badge in await self.api.get_global_chat_badges():
            self.badge_global[badge.set_id]=badge.to_dict()
        self.log("get_global_chat_badges",json.dumps(self.badge_global))
        return


    async def disconnect(self):
        """Gracefully disconnect from Twith API"""

        # End pubsub connections
        #await self.pubsub.unlisten(self.uuid_notification)
        #await self.pubsub.unlisten(self.uuid_points)
       # await self.pubsub.unlisten(self.uuid_subs)
        await self.eventsub.stop()

        # End chat
        self.chat.stop()

        # Close API
        await self.api.close()

        await self.cancel_delays()
        return


    async def callback_chat(self, chat: ChatMessage):

        chat_data = {}
        chat_data["text"] = chat.text
        chat_data["emotes"] = chat.emotes
        chat_data["bits"] = chat.bits
        chat_data["sent_timestamp"] = chat.sent_timestamp
        chat_data["user"] = {}
        chat_data["user"]["color"] = chat.user.color
        chat_data["user"]["name"] = chat.user.name
        chat_data["user"]["display_name"] = chat.user.display_name
        chat_data["user"]["mod"] = chat.user.mod
        chat_data["user"]["id"] = chat.user.id
        chat_data["user"]["icons"] = self.badge_prep(chat.user.badges)
        self.log("callback_chat_data",json.dumps(chat_data))
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
                "text": chat.text,
                "html": self.message_prep(chat),
                "donate": chat.bits,
                "uid": "twitch-"+str(chat.user.id),
                "icons": self.badge_prep(chat.user.badges),
                "clean": True
            }

        if chat.bits > 0:
            # Send data to receivers
            self.emit_donate({
                "from_name":message['from'],
                "uid": "twitch-"+str(chat.user.id),
                "amount":str(chat.bits)+"b",
                "message":message['text']
                })

        if chat.user.mod or chat.user.display_name == "TechTangents":
            print("Mod chat: "+message["text"][0:1])
            if message["text"][0:1] == "!":
                self.emit_interact({
                    "from_name":chat.user.display_name,
                    "uid": "twitch-"+str(chat.user.id),
                    "kind":"Mod Chat Command",
                    "message":message["text"]
                    })

        response = self.emit_chat(message)
        for r in response:
            print("Iterating Response")
            if "reply" in r:
                await chat.reply(r["reply"])
        return


    def badge_prep(self,badge_data):
        if badge_data is None:
            return
        badge_urls=[]
        for key, value in badge_data.items():
            for badge in self.badge_global[key]["versions"]:
                if badge["id"] == value:
                    badge_urls.append(badge["image_url_2x"])

        return badge_urls


    def message_prep(self,message_data, html=True):

        # https://static-cdn.jtvnw.net/emoticons/v2/emotesv2_d13b51bc41cb4b91a08bbcac18f28395/default/dark/1.0
        pprint(message_data.emotes)
        emote_replace = {}

        if message_data.emotes is not None:
            for emote_id, emote_pos in message_data.emotes.items():
                emote_replace[emote_id] = message_data.text[int(emote_pos[0]["start_position"]):int(emote_pos[0]["end_position"])+1]

        text = bleach.clean(message_data.text,tags={})

        if html:
            print("HTML Processing")
            text = self.string_url_link(text)

            if len(emote_replace) > 0:
                for emote_id, emote_text in emote_replace.items():
                    text = text.replace(emote_text,f"<img src=\"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/1.0\"/>")

            print("HTML: " +text)
        return text

    def sub_prep(self,event_data):
        # Applies to all
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
            # Only: Channel Subscription Message
            sub_len="for "+str(int(event_data.cumulative_months))+" months"
        else:
            # Only: Channel Subscribe
            line += " as "+sub_type+" for the first time"
            return line

        # Only: Channel Subscription Gift
        if hasattr(event_data, "total"):
            #gift sub
            line += " gave "+sub_type+" subs to "+event_data.total+" viewers "
        elif hasattr(event_data, "message"):
            # Only: Channel Subscription Message
            line += " subbed as "+sub_type+" "+sub_len+" and says "+self.message_prep(data.event,html=False)
        return line


    async def callback_channel_subscribe(self,data):
        # https://pytwitchapi.dev/en/stable/modules/twitchAPI.object.eventsub.html#twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent

        ## Triggers
        # First time subs
        # Resubs (sometimes?) - Need to filter


        self.log("callback_channel_subscribe",json.dumps(data.to_dict()))

        if data.event.is_gift:
            # Exit if this is a gift sub to prefer the gift callback only
            return

        # self.emit_donate(data.event.user_name,
        #                     str(data.event.tier)+"s",
        #                     self.sub_prep(data.event)
        #                     )

    async def callback_subscription_gift(self,data):
        # https://pytwitchapi.dev/en/stable/modules/twitchAPI.object.eventsub.html#twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent


        ## Triggers
        # Gift subs

        self.log("callback_subscription_gift",json.dumps(data.to_dict()))

        # self.emit_donate(data.event.user_name,
        #                     str(data.event.tier)+"s",
        #                     self.sub_prep(data.event)
        #                     )


    async def callback_subscription_message(self,data):
        # https://pytwitchapi.dev/en/stable/modules/twitchAPI.object.eventsub.html#twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent

        ## Triggers
        # Resubsfrom

        self.log("callback_subscription_message",json.dumps(data.to_dict()))

        # self.emit_donate(data.event.user_name,
        #                     str(data.event.tier)+"s",
        #                     self.sub_prep(data.event)
        #                     )


    async def callback_channel_points_custom_reward_redemption_add(self,data):
        # https://pytwitchapi.dev/en/stable/modules/twitchAPI.object.eventsub.html#twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent

        ## Triggers
        # Resubsfrom

        if hasattr(data,"to_dict"):
            self.log("callback_channel_points_custom_reward_redemption_add",json.dumps(data.to_dict()))


        # Send data to receivers
        self.emit_interact({
            "from_name":data.event.user_name,
            "uid":"twitch-"+data.event.user_id,
            "kind":data.event.reward.title,
            "message":""+str(data.event.user_input)
            })

        # self.emit_donate(data.event.user_name,
        #                     str(data.event.tier)+"s",
        #                     self.sub_prep(data.event)
        #

    async def callback_channel_chat_notification(self,data):
        # https://pytwitchapi.dev/en/stable/modules/twitchAPI.object.eventsub.html#twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent

        ## Triggers
        # Resubs

        if hasattr(data,"to_dict"):
            self.log("callback_channel_chat_notification",json.dumps(data.to_dict()))

        # self.emit_donate(data.event.user_name,
        #                     str(data.event.tier)+"s",
        #                     self.sub_prep(data.event)
        #                     )
        sub_types = ["sub","resub","community_sub_gift","gift_paid_upgrade","prime_paid_upgrade","pay_it_forward","sub_gift"]

        if data.event.notice_type in sub_types:
            # Valid sub type
            if data.event.notice_type == "community_sub_gift":
                self.sub_skip[data.event.chatter_user_name]+=data.event.community_sub_gift.total
                data.event.community_sub_gift.sub_tier=int(data.event.community_sub_gift.sub_tier)*int(data.event.community_sub_gift.total),

            if data.event.notice_type == "sub_gift" and self.sub_skip[data.event.chatter_user_name] > 0:
                self.sub_skip[data.event.chatter_user_name]-=1
                return

            if data.event.message.text != "":
                if data.event.notice_type == "sub":
                    value = data.event.sub.sub_tier
                elif data.event.notice_type == "resub":
                    value = data.event.resub.sub_tier
                elif data.event.notice_type == "community_sub_gift":
                    value = data.event.community_sub_gift.sub_tier
                else:
                    value = 1000

                self.emit_donate({
                    "from_name":data.event.chatter_user_name,
                    "uid":"twitch-"+data.event.chatter_user_id,
                    "amount":str(value)+"s",
                    "message":data.event.system_message + " and says " +data.event.message.text
                    })
            else:
                self.emit_donate({
                    "from_name":data.event.chatter_user_name,
                    "uid":"twitch-"+data.event.chatter_user_id,
                    "amount":str(value)+"s",
                    "message":data.event.system_message
                    })

        announce_types = ["announcement","raid"]

        if data.event.notice_type in announce_types:

            if data.event.message.text != "":
                self.emit_donate({
                    "from_name":data.event.chatter_user_name,
                    "uid":"twitch-"+data.event.chatter_user_id,
                    "amount":str(1)+"s",
                    "message":data.event.message.text
                    })
            else:
                self.emit_donate({
                    "from_name":data.event.chatter_user_name,
                    "uid":"twitch-"+data.event.chatter_user_id,
                    "amount":str(1)+"s",
                    "message":data.event.system_message
                    })


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
        self.emit_donate({
            "from_name":data['user_name'],
            "amount":str(data['sub_plan'])+"s",
            "message":line
            })
        return

