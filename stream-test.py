#!/usr/bin/env python3
# Production Imports
from stream.api_twitch import APItwitch
#from stream.api_youtube import APIyoutube
#from stream.output_dectalk import OUTDectalk
#from stream.output_call import OUTCall
#from stream.output_sound import OUTSound
#from stream.output_json import OUTJson


# Test Imports
#from stream.api_twitch_test import APItwitchTest as APItwitch
#from stream.output_base import OUTBase as OUTDectalk

from stream.api_http import APIhttp
#from stream.api_footpedal import APIfootpedal

import asyncio
import signal
from pathlib import Path

global loop_state
loop_state = True

async def main_loop():
    """ Blocking main loop to provide time for async tasks to run"""
    global loop_state
    while loop_state:
        await asyncio.sleep(1)


async def main():
    """ Start connections to async modules """

    # Setup CTRL-C signal to end programm
    signal.signal(signal.SIGINT, exit_handler)
    print('Press Ctrl+C to exit program')

    # Start async modules
    L = await asyncio.gather(
        twitch.connect(),
        http.connect(),
#        footpedal.connect(),
#        youtube.connect(),
        main_loop()
    )


def exit_handler(sig, frame):
    """ Handle CTRL-C to gracefully end program and API connections """
    global loop_state
    print('You pressed Ctrl+C!')
    loop_state = False



# Setup modules
#outtest = OUTDectalk()
#outtest.actionmap_load("actionmap.json")
#outsound = OUTSound()
#outsound.actionmap_load("actionmap_sound.json")
#jsdata = OUTJson()
#jsdata.actionmap_load("actionmap_json.json")
#footpedal = APIfootpedal(vid = 0x05f3,pid = 0x00FF)
#outcall = OUTCall("192.168.1.219")
http = APIhttp()
twitch = APItwitch(
    key_path=str(Path.home())+"/.api/twitch.json",
    auth_token=str(Path.home())+"/.api/twitch_auth.json"
)
#youtube = APIyoutube(
#    key_path=str(Path.home())+"/.api/youtube.json",
#    auth_token=str(Path.home())+"/.api/youtube_auth.json"
#)

# Connect modules
# twitch.register_interact(outtest.receive_interact)
# twitch.register_chat(outtest.receive_chat)
twitch.register_chat(http.receive_chat)
twitch.register_donate(http.receive_donate)
# #twitch.register_interact(outcall.receive_interact)
# twitch.register_donate(outtest.receive_donate)

#youtube.register_chat(http.receive_chat)
#footpedal.register_interact(outsound.receive_action)
#footpedal.register_interact(outtest.receive_action)
#footpedal.register_interact(jsdata.receive_action)

# Start non async
#http.connect()
#http.poll_check()

asyncio.run(main())

# Run after CTRL-C
http.disconnect()
asyncio.run(twitch.disconnect())
#asyncio.run(footpedal.disconnect())
#asyncio.run(youtube.connect())


