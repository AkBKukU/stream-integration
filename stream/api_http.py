#!/usr/bin/python3
from stream.api_base import APIbase

from flask import Flask
from flask import request
from flask import send_file
from flask import redirect
from flask import make_response
import logging

from multiprocessing import Process

import os
import bleach
import json
from num2words import num2words
from datetime import datetime

class APIhttp(APIbase):
    """Twitch API with signal emitters for bits, subs, and point redeems

    Manages authentication and creating messages from API events to     use elsewhere
    """

    def __init__(self,key_path=None,log=False):
        super().__init__(key_path)
        """Init with file path"""
        self.service_name = "HTTP"

        self.app = Flask("The Web: Now with 100% More OOP")
        self.app.logger.disabled = True
        log = logging.getLogger('werkzeug')
        log.disabled = True

        # Define routes in class to use with flask
        self.app.add_url_rule('/','home', self.index)
        self.app.add_url_rule('/api/donate.json','api-donate', self.apiDonate)
        self.app.add_url_rule('/api/chat.json','api-chat', self.apiChat)
        self.app.add_url_rule('/api/interact.json','api-interact', self.apiInteract)
        self.app.add_url_rule('/chat/','chat', self.chat)
        self.app.add_url_rule('/chat/chat.json','data', self.chatJsonChat)
        self.app.add_url_rule('/read/','read', self.read)
        self.app.add_url_rule('/dono/','dono', self.dono)
        self.app.add_url_rule('/dono/subs.json','dono-subs', self.donoJsonSubs)
        self.app.add_url_rule('/dono/dono.css','dono-css', self.donoCss)
        self.app.add_url_rule('/read/read.css','read-css', self.readCss)
        self.app.add_url_rule('/read/chat.json','read-data', self.readJsonChat)
        self.app.add_url_rule('/read/subs.json','read-subs', self.readJsonSubs)
        self.app.add_url_rule('/window/','window', self.window)
        self.app.add_url_rule('/window/window.css','window-css', self.windowCss)
        self.app.add_url_rule('/window/window.js','window-js', self.windowJs)
        self.app.add_url_rule('/window/chat.json','window-chat', self.windowJsonChat)
        self.app.add_url_rule('/window/subs.json','window-subs', self.windowJsonSubs)
        self.app.add_url_rule('/window/poll.json','window-poll', self.windowJsonPoll)

        # Set headers for server
        self.app.after_request(self.add_header)

        self.poll_filter=json.load(open('stream/http/vote-filter.json'))

        self.chat = []
        self.subs = []
        self.donateall = []
        self.poll = {}
        self.poll_output = {}
        self.poll_valid = []
        self.poll_threshold = 3

        self.api_chat = []
        self.api_interact = []
        self.api_donate = []
        self.json_api_chat='/tmp/stream_api_chat.json'
        if os.path.isfile(self.json_api_chat):
            os.remove(self.json_api_chat)
        self.json_api_interact='/tmp/stream_api_interact.json'
        if os.path.isfile(self.json_api_interact):
            os.remove(self.json_api_interact)
        self.json_api_donate='/tmp/stream_api_donate.json'
        if os.path.isfile(self.json_api_donate):
            os.remove(self.json_api_donate)

        self.json_chat= '/tmp/stream_http_chat.json'
        self.json_donateall= '/tmp/stream_http_donateal.json'
        self.json_subs= '/tmp/stream_http_subs.json'
        self.json_poll= '/tmp/stream_http_poll.json'
        self.host = "0.0.0.0"

        

    def set_host(self,host_ip):
        self.host = host_ip

    def add_header(self,r):
        """
        Force the page cache to be reloaded each time
        """
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    async def poll_check(self):
        # If there are self.poll_threshold identical messages in self.poll start poll and add
        # message to valid after, if there are 10 other identical messages add new valid option
        # and display if voter messages after voting ignore, unless valid vote number

        poll_count={}
        for k, v in self.poll.items():
            if v not in poll_count:
                poll_count[v] = 1
            else:
                poll_count[v] += 1

        for poll_option in poll_count:
            if poll_count[poll_option] >= self.poll_threshold:
                if poll_option not in self.poll_valid:
                    self.poll_valid.append(poll_option)

        if self.poll_valid and self.poll_output["valid"] == False:
            print("####### Poll started with valid options:")
            self.poll_output["valid"] = True
        if self.poll_valid:
            poll_data = {}
            for opt in self.poll_valid:
                if opt not in poll_count:
                    poll_count[opt] = 0
                print(opt+": "+str(poll_count[opt]))
                poll_data[opt] = poll_count[opt]
            self.poll_output["data"] = poll_data
            self.poll_output["rar"] = self.poll

            with open(self.json_poll, 'w', encoding="utf-8") as output:
                output.write(json.dumps(self.poll_output))

            self.poll_output["remaining"] -= 1
            if (self.poll_output["remaining"] < 1):
                # Poll over
                self.delay_callback("poll_clear", 10000, self.poll_clear)

                win = max(poll_count, key=poll_count.get)
                # Send data to receivers
                self.emit_interact("api",
                    "Poll Results",
                    win
                    )

                self.receive_donate("api","1s","Poll Over ["+win+"] Wins")
                return

            # Valid poll started, display with html

        self.delay_callback("poll_check", 1000, self.poll_check)
        return

    async def poll_clear(self):
        self.poll = {}
        self.poll_total = 0
        self.poll_valid = []
        self.poll_output = {}
        self.poll_output["title"] = "Dynamic Poll"
        self.poll_output["remaining"] = 30
        self.poll_output["valid"] = False
        with open(self.json_poll, 'w', encoding="utf-8") as output:
            output.write(json.dumps(self.poll_output))
        self.delay_callback("poll_check", 1000, self.poll_check)
        return

    def poll_vote(self, from_name, text):
        return_state = "show"

        if text in self.poll_filter["whole"]:
            text = self.poll_filter["whole"][text]

        for key, value in self.poll_filter["replace"].items():
            text = text.replace(key,value)

        ## Vote by number
        try:
            # Set vote if matches valid index
            if int(text) < len(self.poll_valid)+1 and int(text) > 0:
                # Getting vote word by index to store makes this easier
                self.poll[from_name] = self.poll_valid[int(text)-1]

                # Subtract or add time to make poll faster but fair
                win = max(self.poll_output["data"], key=self.poll_output["data"].get)
                if win == self.poll[from_name]:
                    self.poll_output["remaining"] -= 2
                if win != self.poll[from_name]:
                    self.poll_output["remaining"] += 1
            # Convert vote into word
            elif int(text) > 0:
                self.poll[from_name] = num2words(int(text))

            return return_state
        except ValueError:
            pass


        # Haven't chated since last poll
        if from_name not in self.poll:
            # record anything
            self.poll[from_name] = text

            # If vote was valid subtract or add time to make poll faster but fair
            if self.poll[from_name] in self.poll_valid:
                win = max(self.poll_output["data"], key=self.poll_output["data"].get)
                if win == text:
                    self.poll_output["remaining"] -= 2
                if win != self.poll[from_name]:
                    self.poll_output["remaining"] += 1
            return return_state

        ## Change Vote
        # Set new vote if matches valid
        if text in self.poll_valid:
            old_vote = self.poll[from_name]
            self.poll[from_name] = text


            # If old vote was invalid
            # subtract or add time to make poll faster but fair
            if old_vote not in self.poll_valid:
                win = max(self.poll_output["data"], key=self.poll_output["data"].get)
                if win == text:
                    self.poll_output["remaining"] -= 2
                if win != self.poll[from_name]:
                    self.poll_output["remaining"] += 1
            return return_state

        # Update old vote and new vote are not valid
        if self.poll[from_name] not in self.poll_valid:
            self.poll[from_name] = text
            return return_state

        # No valid votes yet, update vote
        if not self.poll_valid:
            self.poll[from_name] = text
            return return_state

        return "show"

    async def connect(self):
        """ Run Flask in a process thread that is non-blocking """
        print("Starting Flask")
        self.web_thread = Process(target=self.app.run, kwargs={"host":self.host,"port":5001})
        self.web_thread.start()
        self.delay_callback("poll_clear", 100, self.poll_clear)

    def disconnect(self):
        """ Send SIGKILL and join thread to end Flask server """
        self.web_thread.terminate()
        self.web_thread.join()

    def poll_config(self,title):
        self.poll_output["title"] = title
        self.poll_output["remaining"] += 60
        if self.poll_output["remaining"] > 180:
            self.poll_output["remaining"] = 180


    def index(self):
        """ Simple class function to send HTML to browser """
        return """
<a href="/chat/"><h2>Chat</h2></a>
<a href="/read/"><h2>Read</h2></a>
<a href="/window/"><h2>Window</h2></a>
<a href="/dono/"><h2>Dono List</h2></a>
        """

    def dono(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/dono-list.html")

    def donoCss(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/dono.css")

    def read(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/chat-read.html")


    def readCss(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/read.css")

    def chat(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/chat-view.html")

    def readJsonChat(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_chat):
            return send_file(self.json_chat)
        else:
            return send_file("stream/http/blank")

    def readJsonSubs(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_donateall):
            return send_file(self.json_donateall)
        else:
            return send_file("stream/http/blank")

    def donoJsonSubs(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_donateall):
            return send_file(self.json_donateall)
        else:
            return send_file("stream/http/blank")

    def chatJsonChat(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_chat):
            return send_file(self.json_chat)
        else:
            return send_file("stream/http/blank")

    def window(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/window.html")

    def windowCss(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/window.css")

    def windowJs(self):
        """ Simple class function to send HTML to browser """
        return send_file("stream/http/window.js")

    def windowJsonChat(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_chat):
            return send_file(self.json_chat)
        else:
            return send_file("stream/http/blank")

    def windowJsonSubs(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_subs):
            return send_file(self.json_subs)
        else:
            return send_file("stream/http/blank")

    def windowJsonPoll(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_poll):
            return send_file(self.json_poll)
        else:
            return send_file("stream/http/blank")

    def apiChat(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_api_chat):
            return send_file(self.json_api_chat)
        else:
            return send_file("stream/http/blank")

    def apiDonate(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_api_donate):
            return send_file(self.json_api_donate)
        else:
            return send_file("stream/http/blank")

    def apiInteract(self):
        """ Simple class function to send JSON to browser """
        if os.path.exists(self.json_api_interact):
            return send_file(self.json_api_interact)
        else:
            return send_file("stream/http/blank")

    def receive_donate(self,from_name,amount,message,benefits=None):
        """Output message to CLI for chat"""
        
        # Add to host API data
        if (from_name != "api"):
            if len(self.api_donate) > 30:
                self.api_donate.pop(0)

            self.api_donate.append(
                    {
                        "timestamp":datetime.now().isoformat().replace(":","-"),
                        "from":from_name,
                        "amount":amount, 
                        "text":message
                    }
                )
            with open(self.json_api_donate, 'w', encoding="utf-8") as output:
                output.write(json.dumps(self.api_donate))

        # Handle web display
        message = bleach.clean(message,tags={})

        print ("something Recieved: "+amount)
        # Subs
        if amount.endswith("b"):
            # No action on bits
            self.donateall.append({"timestamp":str(datetime.now().isoformat()).replace(":","-"),"from":from_name, "text":message})

            if len(self.donateall) > 50:
                self.donateall.pop(0)

            with open(self.json_donateall, 'w', encoding="utf-8") as output:
                output.write(json.dumps(self.donateall))
            return

        print ("HTTP Sub Recieved")

        self.subs.append({"timestamp":str(datetime.now().isoformat()).replace(":","-"),"from":from_name, "text":message})
        self.donateall.append({"timestamp":str(datetime.now().isoformat()).replace(":","-"),"from":from_name, "text":message})

        if len(self.subs) > 30:
            self.subs.pop(0)

        if len(self.donateall) > 50:
            self.donateall.pop(0)

        with open(self.json_subs, 'w', encoding="utf-8") as output:
            output.write(json.dumps(self.subs))

        with open(self.json_donateall, 'w', encoding="utf-8") as output:
            output.write(json.dumps(self.donateall))
        return

    def receive_chat(self,data):
        """Output message to CLI for chat"""
        
        # Add to host API data
        if len(self.api_chat) > 30:
            self.api_chat.pop(0)

        if "html" in data:
            data["text"] = data["html"]

        self.api_chat.append(
                {
                    "timestamp":datetime.now().isoformat().replace(":","-"),
                    "from":data["from"],
                    "text":data["text"],
                    "color":data["color"],
                    "donate":data["donate"]
                }
            )
        with open(self.json_api_chat, 'w', encoding="utf-8") as output:
            output.write(json.dumps(self.api_chat))

        # Web display data
        if "clean" in data and data["clean"] == True:
            print("HTML preformatted message recieved")
        else:
            data["text"] = bleach.clean(data["text"],tags={})
        self.chat.append(data)
        if self.poll_vote(data["from"], data["text"].lower().strip()) == "hide":
            return

        if len(self.chat) > 30:
            self.chat.pop(0)

        with open(self.json_chat, 'w', encoding="utf-8") as output:
            output.write(json.dumps(self.chat))
        return

    def receive_interact(self,from_name,kind,message):
        # Add to host API data
        if len(self.api_interact) > 30:
            self.api_interact.pop(0)

        self.api_interact.append(
                {
                    "timestamp":datetime.now().isoformat().replace(":","-"),
                    "from":from_name,
                    "kind":kind,
                    "text":message
                }
            )
        with open(self.json_api_interact, 'w', encoding="utf-8") as output:
            output.write(json.dumps(self.api_interact))



        if kind == "Mod Chat Command":
            if message.find("!poll") == 0:
                self.poll_config(message.lower().replace("!poll","").strip())
                print("Poll title change: "+message)
