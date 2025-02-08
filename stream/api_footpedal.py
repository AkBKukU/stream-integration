#!/usr/bin/python3
from stream.api_base import APIbase

import hid

class APIfootpedal(APIbase):
    """API Base for signal emitters

    Manages loading API keys, logging, and registering signal recievers
    """

    def __init__(self,log=False,vid=None,pid=None):
        """Init with file path"""
        super().__init__(None)
        self.vid = vid
        self.pid = pid

        self.left = False
        self.center = False
        self.right = False

        self.run = True


    async def connect(self):
        self.dev = hid.device()
        self.dev.open(self.vid, self.pid)

        print ("Footpedal active")
        self.delay_callback("check_input", 1000, self.check_input)

    async def disconnect(self):
        self.run = False
        await self.cancel_delay("check_input")

    async def check_input(self):

        self.delay_callback("check_input", 1100, self.check_input)
        r=self.dev.read(10,1000)
        if len(r) > 1:
            if not self.left and (r[0] & 0b1) > 0:
                print("Left Pressed")
                # Send data to receivers
                self.emit_interact(
                            "left",
                            "",
                            "press"
                            )
            elif self.left and (r[0] & 0b1) == 0:
                print("Left released")
                self.emit_interact(
                            "left",
                            "",
                            "release"
                            )
            self.left = (r[0] & 0b1) == 1;

            if not self.center and (r[0] & 2) > 0:
                print("center Pressed")
                self.emit_interact(
                            "center",
                            "",
                            "press"
                            )
            elif self.center and (r[0] & 2) == 0:
                print("center released")
                self.emit_interact(
                            "center",
                            "",
                            "release"
                            )
            self.center = (r[0] & 2) == 2;

            if not self.right and (r[0] & 4) > 0:
                print("right Pressed")
                self.emit_interact(
                            "right",
                            "",
                            "press"
                            )
            elif self.right and (r[0] & 4) == 0:
                print("right released")
                self.emit_interact(
                            "right",
                            "",
                            "release"
                            )
            self.right = (r[0] & 4) == 4;

            await self.cancel_delay("check_input")
            self.delay_callback("check_input", 1, self.check_input)


    def test(self):
        self.dev.open()


