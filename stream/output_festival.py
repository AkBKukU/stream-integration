#!/usr/bin/python3

# Requires
# sudo apt-get install python3 python3-dev festival festival-dev
# pip install pyfestival

from stream.output_base import OUTBase

import festival

class OUTFestival(OUTBase):
    """Simple CLI output receiver
    """

    def __init__(self):
        self.service_name = "Festival"

    def receive_donate(self,data):
        """Output message as audio for donate"""
        festival.sayText(data["from_name"]+" gave "+data["amount"]+" and said "+data["message"])
        return

    def receive_interact(self,data):
        """Output message as audio for interaction"""
        festival.sayText(data["from_name"]+" did "+data["kind"]+" and said "+data["message"])
        return
