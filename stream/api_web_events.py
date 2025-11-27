#!/usr/bin/python3
from stream.output_base import OUTBase

import os
import re
import json
from pprint import pprint

from flask import Flask
from flask import request
from flask import send_file
from flask import redirect
from flask import make_response

class APIWebEvents(OUTBase):
    """Web Event Tester
    """

    def __init__(self):
        super().__init__()
        self.service_name = "Web Event Tester"

        self.html_index=f"""
<script>

function chat(event) {{
    chat_name=document.getElementById('chat_name').value;
    chat_input=document.getElementById('chat_input').value;
	fetch("/test/", {{
		method: 'post',
	   headers: {{
		   "Content-Type": "application/json",
		   'Accept':'application/json'
	   }},
	   body: JSON.stringify({{"type":"chat","chat_name":chat_name,"chat_input":chat_input}}),
	}}).then(() => {{
		// Do Nothing
	}});
}};

function interact(event) {{
    interact_name=document.getElementById('interact_name').value;
    interact_input=document.getElementById('interact_input').value;
	fetch("/test/", {{
		method: 'post',
	   headers: {{
		   "Content-Type": "application/json",
		   'Accept':'application/json'
	   }},
	   body: JSON.stringify({{"type":"interact","interact_name":interact_name,"interact_input":interact_input}}),
	}}).then(() => {{
		// Do Nothing
	}});
}};

function donate(event) {{
    donate_name=document.getElementById('donate_name').value;
    donate_amount=document.getElementById('donate_amount').value;
    donate_input=document.getElementById('donate_input').value;
	fetch("/test/", {{
		method: 'post',
	   headers: {{
		   "Content-Type": "application/json",
		   'Accept':'application/json'
	   }},
	   body: JSON.stringify({{"type":"donate","donate_name":donate_name,"donate_amount":donate_amount,"donate_input":donate_input}}),
	}}).then(() => {{
		// Do Nothing
	}});
}};

</script>
<div>
    <input type="text" id="chat_name" name="chat_name" placeholder="Add chat name here...">
    <input type="text" id="chat_input" name="chat_input" placeholder="Add chat message here...">
    <a onclick="chat(event)" >
    <input type="button" value="Send Chat">
    </a>
</div>
<div>
    <input type="text" id="interact_name" name="interact_name" placeholder="Add interact name here...">
    <input type="text" id="interact_input" name="interact_input" placeholder="Add interact message here...">
    <a onclick="interact(event)" >
    <input type="button" value="Send Interact">
    </a>
</div>
<div>
    <input type="text" id="donate_name" name="donate_name" placeholder="Add donate name here...">
    <input type="number" id="donate_amount" name="donate_amount" placeholder="Add interact message here...">
    <input type="text" id="donate_input" name="donate_input" placeholder="Add donate message here...">
    <a onclick="donate(event)" >
    <input type="button" value="Send Donate">
    </a>
</div>
</body>
"""


    def emit_routes(self):
        return [
                {
                    "name": "Web Event Tester",
                    "uri": "/test/",
                    "callback": self.http_index,
                    "major": True
                }
            ]


    def http_index(self):
        try:
            data = request.get_json()
            if data["type"]=="chat":
                message={
                        "from": data["chat_name"],
                        "color": "#00FF7F",
                        "text": data["chat_input"],
                        "donate": 0,
                        "icons": [],
                        "uid": "test-1337",
                        "clean": True
                    }
                self.emit_chat(message)
                return f"Name: {data["chat_name"]}, text: {data["chat_input"]}"

            if data["type"]=="interact":
                self.emit_interact({
                    "from_name":"Tester",
                    "uid":"test-1337",
                    "kind":data["interact_name"],
                    "message":data["interact_input"]
                    })
                print( f"interact_name: {data["interact_name"]}, interact_input: {data["interact_input"]}")
                return f"interact_name: {data["interact_name"]}, interact_input: {data["interact_input"]}"


            if data["type"]=="donate":
                # Send data to receivers
                self.emit_donate({
                    "from_name":data["donate_name"],
                    "uid": "test-1337",
                    "amount":str(data["donate_amount"])+"s",
                    "message":data["donate_input"]
                    })
                return f"interact_name: {data["interact_name"]}, interact_input: {data["interact_input"]}"

        except Exception as e:
            # Web server probably isn't running, fail silently
            return self.html_index

        return self.html_index
