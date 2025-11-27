#!/usr/bin/python3
from stream.api_base import APIbase
from stream.keyat.interface import Interface as KAT
import re
import time


class OUTKAT(APIbase):
    """Simple CLI output receiver
    """

    def __init__(self,serial_port='/dev/ttyUSB0'):
        super().__init__(None)
        self.service_name = "KeyAT"
        self.banned = [
            "q",
            "quit",
            ]
        self.remove = [
            "\\",
            "quit",
            "save",
            "restore",
            "restart",
            "restar",
            "script",
            "resta",
            "q.",
            ".q",
            ".",
            ]
        self.serial_port = serial_port

    def receive_chat(self,data):
        """Output message to CLI for donate"""
        keyat = KAT(self.serial_port)
        keyat.send(data["from"]+": "+data["text"]+"\n")
        return

    def receive_interact(self,data):
        """Output message to CLI for interaction"""
        keyat = KAT(self.serial_port)
        if data["kind"] == "Send Command" or data["kind"] == "Poll Results":

            data["message"] = data["message"].encode("ascii",errors="ignore").decode()
            data["message"] = re.sub('\\bq\\b', '', data["message"])
            data["message"] = data["message"].replace('~', '')
            data["message"] = data["message"].replace('^', '')
            data["message"] = data["message"].strip()
            data["message"] = data["message"].lower()
            if data["message"] in self.banned:
                return

            for bad in self.remove:
                if bad in data["message"]:
                    return
            keyat.send(data["message"][:32]+"\n")
            print("Command (from [" +data["from_name"]+ "]): " + data["message"][:32])
        if data["kind"] == "Status Command":
            keyat.send("i"+"\n")
            time.sleep(3)
            keyat.send("diagnose"+"\n")
            time.sleep(3)
            keyat.send("look"+"\n")
            time.sleep(3)

        return



    def receive_donate(self,data):
        """Respond to bit and sub messages"""

        data["message"] = data["message"].strip()
        data["message"] = data["message"].lower()

        # Bits
        if data["amount"].endswith("b"):
            data["amount"] = data["amount"].replace("b","")

            if int(data["amount"]) == 25:
                print("Maybe Restart: " + data["message"])
                if "restart" in data["message"]:
                    keyat = KAT(self.serial_port)
                    keyat.send("restart\nY\n")
                    return
        return
