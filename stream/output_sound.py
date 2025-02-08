#!/usr/bin/python3

from stream.output_base import OUTBase

from playsound import playsound

class OUTSound(OUTBase):
    """Simple CLI output receiver
    """
    def __init__(self,log=False,vid=None,pid=None):
        """Init with file path"""
        super().__init__()
        self.actions["play_file"]=self.action_play_file

    def receive_interact(self,from_name,kind,message):
        """Output message to CLI for interaction"""
        if kind == "Edit Mark":
            print("BEEEEEEEEEEEEEEEEEEEEEEEEEEEP")
            playsound("stream/sound/440Hz-30s.wav",False)
        return

    def action_play_file(self,data,data_fixed):
            print("Playing sound: "+data_fixed["filepath"])
            playsound(data_fixed["filepath"],False)
