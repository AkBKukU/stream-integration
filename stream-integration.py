#!/usr/bin/python3
# Production Imports
#from stream.api_twitch import APItwitch
#from stream.output_dectalk import OUTDectalk
#from stream.output_call import OUTCall


# Test Imports
from stream.api_twitch_test import APItwitchTest as APItwitch
from stream.output_base import OUTBase as OUTDectalk

from stream.api_http import APIhttp

import asyncio
import signal
from pathlib import Path

global loop_state
loop_state = True

async def main_loop():
    global loop_state
    while loop_state:
        await asyncio.sleep(1)


async def main():
    signal.signal(signal.SIGINT, exit_handler)
    print('Press Ctrl+C to exit program')
    L = await asyncio.gather(
        outtest.connect(),
        twitch.connect(),
        main_loop()
    )

def exit_handler(sig, frame):
    global loop_state
    print('You pressed Ctrl+C!')
    loop_state = False
    http.disconnect()



outtest = OUTDectalk()
#outcall = OUTCall("192.168.1.219")
http = APIhttp()


print("Starting Stream Integration")
twitch = APItwitch(str(Path.home())+"/.api/twitch.json")
twitch.register_interact(outtest.receive_interact)
twitch.register_chat(outtest.receive_chat)
twitch.register_chat(http.receive_chat)
#twitch.register_interact(outcall.receive_interact)

#twitch.register_donate(outtest.receive_donate)

http.connect()

asyncio.run(main())

# Run after CTRL-C
asyncio.run(twitch.disconnect())


