#!/usr/bin/python3

from stream.output_base import OUTBase

import json

class OUTJson(OUTBase):
    """Simple CLI output receiver
    """
    def __init__(self,log=False,vid=None,pid=None):
        """Init with file path"""
        super().__init__()
        self.actions["output"]=self.action_output


    def action_output(self,data,data_fixed):

        with open(data_fixed["filepath"], 'w', encoding="utf-8") as output:
            output.write(json.dumps(data_fixed["data"]))
