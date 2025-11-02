#!/usr/bin/python3
from stream.output_dectalk import OUTDectalk

import subprocess

class OUTDectalkSoftware(OUTDectalk):
    """DECTalk software receiver for interaction

    Inherits original DECTalk features but replaces output with call to software version.
    """

    def write(self,text):
        """Write data to serial port to DECTalk"""

        # Santize text
        text = self.clean(text)

        # Send data to DECTalk
        subprocess.run(["say", "-a", text])
        return

