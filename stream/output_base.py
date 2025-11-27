#!/usr/bin/python3
from stream.api_base import APIbase


class OUTBase(APIbase):
    """Simple CLI output receiver
    """

    def __init__(self):
        super().__init__(None)
        self.service_name = "Base"

    def receive_donate(self,data):
        """Output message to CLI for donate"""
        print(data["from_name"]+" gave "+data["amount"]+" and said "+data["message"])
        return

    def receive_interact(self,data):
        """Output message to CLI for interaction"""
        print(data["from_name"]+" did "+data["kind"]+" and said "+data["message"])
        return
