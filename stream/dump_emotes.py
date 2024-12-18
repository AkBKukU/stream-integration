"""Twitch Emotes Dumping Script

This script is designed to pull twitch emotes from several sources and dump them into a single JSON file. It current supports Twitch global and channel emotes, 7TV emotes, and BetterTTV emotes. It also supports saving individual emote maps to their own JSON files, for debugging purposes, or other future integrations.

The rational here is that emotes don't change often, and in a bandwidth constrained environment, it's better to have a single file that can be cached, rather than looking it up every time. If a more up to date solution is required, this code can be used as a basis to build enpoints in the stream integration that can be called on demand, instead.

This script requires a Twitch client ID and secret, which can be obtained by registering a Twitch application at https://dev.twitch.tv/console/apps/create. The client ID and secret can be passed in as command line arguments. Unfortunately, Twitch doesn't make these 100% public endpoints available without logging in, so this is the best we can do.
"""

import argparse
import requests
import json
import os

def get_twitch_access_token(client_id, client_secret):
    token_url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    response = requests.post(token_url, params=params)
    response_json = response.json()

    if "access_token" in response_json:
        return response_json["access_token"]
    else:
        print("Failed to obtain access token.")
        print(response_json)
        exit()

def fetch_twitch_emotes(client_id, client_secret, channel_name, save_location, save_individual_maps, enable_7tv, enable_better_ttv):
    access_token = get_twitch_access_token(client_id, client_secret)
    emotes_map = {}
    
    # Twitch Headers
    headers = {"Client-ID": client_id, "Authorization": f"Bearer {access_token}"}

    # Fetch Twitch global emotes
    twitch_global_emotes_url = "https://api.twitch.tv/helix/chat/emotes/global"
    twitch_global_emotes = requests.get(twitch_global_emotes_url, headers=headers).json()["data"]
    
    emotes_map.update({f"{emote['name']}": {"source": "twitch", "id": emote["id"], "urls": emote["images"]} for emote in twitch_global_emotes})

    print(f"Found {len(twitch_global_emotes)} global emotes.")

    # Fetch Twitch channel emotes
    twitch_channel_url = f"https://api.twitch.tv/helix/users?login={channel_name}"
    twitch_channel_id = requests.get(twitch_channel_url, headers=headers).json()["data"][0]["id"]
    twitch_channel_emotes_url = f"https://api.twitch.tv/helix/chat/emotes?broadcaster_id={twitch_channel_id}"
    twitch_channel_emotes = requests.get(twitch_channel_emotes_url, headers=headers).json()["data"]
    
    emotes_map.update({f"{emote['name']}": {"source": f"twitch-channel-{twitch_channel_id}", "id": emote["id"], "urls": emote["images"]} for emote in twitch_channel_emotes})

    print(f"Found {len(twitch_channel_emotes)} channel emotes.")

    # Fetch 7TV emotes
    if enable_7tv:
        print("7TV emotes are currently disabled due to lack of documentation and API being dumb.")
        # seven_tv_url = "https://api.7tv.app/v2/emotes/global"
        # seven_tv_emotes = requests.get(seven_tv_url).json()
        # emotes_map.update({f"{emote['name']}": {"source": "7tv", "url": emote["urls"]["2"]} for emote in seven_tv_emotes})
        # print(f"Found {len(seven_tv_emotes)} 7tv emotes.")

    # Fetch BetterTTV emotes
    if enable_better_ttv:
        better_ttv_url = "https://api.betterttv.net/3/cached/emotes/global"
        better_ttv_emotes = requests.get(better_ttv_url).json()

        emotes_map.update({
            f"{emote['code']}": {
                "source": "betterttv",
                "id": emote["id"],
                "urls": {
                    "url_1x": f"https://cdn.betterttv.net/emote/{emote['id']}/1x",
                    "url_2x": f"https://cdn.betterttv.net/emote/{emote['id']}/2x",
                    "url_3x": f"https://cdn.betterttv.net/emote/{emote['id']}/3x",
                }
            } for emote in better_ttv_emotes
        })

        print(f"Found {len(better_ttv_emotes)} BetterTTV emotes.")

    # Save individual emote maps
    if save_individual_maps:
        
        # Get a list of all the sources
        sources = set([emote_info["source"] for emote_info in emotes_map.values()])

        # For each source, filter down to just those emotes and save a separate file
        for source in sources:
            source_emotes = {emote_name: emote_info for emote_name, emote_info in emotes_map.items() if emote_info["source"] == source}

            with open(os.path.join(save_location, f"{source}.json"), "w") as file:
                json.dump(source_emotes, file, indent=2)

    # Save combined emotes map
    with open(os.path.join(save_location, "emotes.json"), "w") as file:
        json.dump(emotes_map, file, indent=2)

def print_usage():
    print("Usage:")
    print("python fetch_emotes.py <channel_name> <save_location> --save-individual-maps --enable-7tv --enable-better-ttv --client-id <your_client_id> --client-secret <your_client_secret>")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch emotes from various sources.")
    parser.add_argument("channel_name", type=str, help="Twitch channel name")
    parser.add_argument("save_location", type=str, help="Directory to save emotes maps")
    parser.add_argument("--save-individual-maps", action="store_true", help="Save individual emote maps")
    parser.add_argument("--enable-7tv", action="store_true", help="Enable 7TV emotes")
    parser.add_argument("--enable-better-ttv", action="store_true", help="Enable BetterTTV emotes")
    parser.add_argument("--client-id", type=str, help="Twitch client ID")
    parser.add_argument("--client-secret", type=str, help="Twitch client secret")

    args = parser.parse_args()

    if not args.channel_name or not args.save_location or not args.client_id or not args.client_secret:
        print_usage()
        exit()

    fetch_twitch_emotes(args.client_id, args.client_secret, args.channel_name, args.save_location, args.save_individual_maps, args.enable_7tv, args.enable_better_ttv)
