#!/usr/bin/python3

from stream.output_base import OUTBase

from playsound import playsound

class OUTSound(OUTBase):
    """Simple CLI output receiver
    """

    def receive_interact(self,from_name,kind,message):
        """Output message to CLI for interaction"""
        if kind == "Edit Mark":
            print("BEEEEEEEEEEEEEEEEEEEEEEEEEEEP")
            playsound("stream/sound/440Hz-30s.wav",False)
        if from_name == "center" and message == "press":
            print("BEEEEEEEEEEEEEEEEEEEEEEEEEEEP")
            playsound("stream/sound/440Hz-30s.wav",False)
        return
