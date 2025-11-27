#!/usr/bin/python3

from stream.output_base import OUTBase

import sys
import subprocess
import os

class OUTCall(OUTBase):
    """Simple CLI output receiver
    """

    def __init__(self,ip):
        self.service_name = "Call"
        self.txt_tmp="/tmp/tts.txt"
        self.flac_tmp="/tmp/tts.flac"
        self.wav_tmp="/tmp/tts.wav"
        self.wav8k_tmp="/tmp/tts-8k.wav"
        self.xml="/stream/output_call/audio.xml"
        self.phone_ip=ip

    def write(self, message):
        with open(self.txt_tmp, 'w', encoding="utf-8") as output:
            output.write("The message will start after this sentence.")
            output.write(message)
            output.write("Repeating message.")
            output.write(message)
            output.write("Repeating message.")
            output.write(message)
        return

    def run(self,cmd):
        #subprocess.run([sys.executable, "-c", str(cmd)])
        process = subprocess.Popen(cmd,
                     stdout = subprocess.PIPE,
                     stderr = subprocess.PIPE,
                     text = True,
                     shell = True
                     )
        std_out, std_err = process.communicate()
        std_out.strip(), std_err
        return

    def call(self):
        self.run(str("cat "+self.txt_tmp+" | text2wave -eval '(voice_cmu_us_slt_arctic_hts)' > "+self.wav_tmp))
        self.run(str("ffmpeg -y -i "+self.wav_tmp+" "+self.flac_tmp))
        self.run(str("ffmpeg -y -i "+self.flac_tmp+" -codec:a pcm_alaw -ar 8000 -ac 1 "+self.wav8k_tmp))

        self.run(str("sipp -sf "+os.getcwd()+self.xml+" "+self.phone_ip+" -s 100 -l 1 -d 30000 -m 1"))

        return

    def receive_interact(self,data):
        """Output message to CLI for interaction"""
        if kind == "Call Me!":
            self.write(data["from_name"] + " said " + data["message"])
            self.call()
        return
