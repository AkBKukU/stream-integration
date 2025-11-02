#!/usr/bin/python3
from stream.output_base import OUTBase

import serial
import re

class OUTDectalk(OUTBase):
    """DECTalk receiver for interaction

    Sends messages over serial to a DECTalk with some bootstrapping to make it work better
    """

    def __init__(self,serial_port='/dev/ttyUSB0'):
        super().__init__()
        self.service_name = "DECTalk"
        self.serial_port = serial_port
        self.write("DECTalk is now on line")

    def prefix(self,text):
        prefix="[:punct none]"
        return prefix

    def postfix(self,text):
        if "[:nh]" in text:
            postfix=str('[:nh][:dv ap 90 pr 0].[:rate 140]BY YOUR COMMAND.[:np][:pp 0 :cp 0][:rate 200][:say line][:punct none][:pitch 35][:phoneme off][:volume set 33]\r\n')
        else:
            postfix=str('[:nh][:dv ap 90 pr 0].[:rate 140]END OF LINE.[:np][:pp 0 :cp 0][:rate 200][:say line][:punct none][:pitch 35][:phoneme off][:volume set 33]\r\n')
        return postfix


    def write(self,text):
        """Write data to serial port to DECTalk"""

        # Santize text
        text = self.clean(text)

        # Send data to DECTalk
        with serial.Serial(self.serial_port,9600,timeout=1) as ser:
            ser.write( bytes(self.prefix()+str(text)+self.postfix(),'ascii',errors='ignore') )
        return


    def clean(self,text):
        """Clean up text before sending to DECTalk"""

        """Note:
        It is pretty much impossible to fully counteract abusive text sent to a DECTalk,
        especially a real hardware device. Phoneme mode will allow making custom words
        defeating any filtering. This is more for removing lazy attempts to break it.
        """
        text = text.replace("google", "")
        text = text.replace("alexa", "")
        text = text.replace("siri", "")
        text = text.replace("cylon", "seyelon")
        text = text.replace(":period", ":rate")
        text = text.replace(":comma", ":rate")
        text = re.sub(":volume\s+set", ":np] . Volume Override[:rate ",text)
        text = text.replace("%p","[:phoneme arpabet speak on]").replace("%P","[:phoneme arpabet speak on]")
        text = text.replace("%c","[:nh][:dv ap 90 pr 0][:rate 140]").replace("%C","[:nh][:dv ap 90 pr 0][:rate 140]")

        return text


    def receive_donate(self,from_name,amount,message,benefits=None):
        """Respond to bit and sub messages"""

        # Bits
        if amount.endswith("b"):
            amount = amount.replace("b","")
            # Set minimum donation at 100 bits to trigger DECTalk
            if int(amount) < 200:
                return

            # Send nessage
            self.write(from_name+" says "+message)

        # Subs
        if amount.endswith("s"):
            # Send nessage
            self.write(message)
        return

    def receive_interact(self,from_name,kind,message):
        """Respond to interactions"""

        # Note: I don't use the point rewards for DECTalk currently
        if kind == "API Test":
            self.write(from_name+" did "+kind+" and said "+message)
        return


    def receive_chat(self,data):
        """Output message to CLI for chat"""

        self.write(data["text"])
        return
