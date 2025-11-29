#!/usr/bin/python3
from stream.output_base import OUTBase

import os
import re
import json
from pprint import pprint
import sqlite3
from flask import send_file


class APIGameNTF(OUTBase):
    """No Tangible Function collecting game

    viewers will be able to buy representations of computers I own and have them
    as badges next to there name in the on screen overlay.
    """


    def __init__(self):
        super().__init__()
        self.service_name = "NTF Game"
        self.base_URL = "https://chat.techtangents.net"

        # Database Path setup
        if not os.path.exists("ntf/"):
             os.makedirs("ntf/")
        if not os.path.exists("ntf/images/"):
             os.makedirs("ntf/images/")

        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()

        # Initialize DB if empty
        res = cur.execute("SELECT name FROM sqlite_master")
        if res.fetchone() is None:
            # Build DB
            cur.execute("CREATE TABLE ntf(key INTEGER PRIMARY KEY ASC, ntf_name, ntf_image, value, player_key INTEGER)")
            cur.execute("CREATE TABLE player(key INTEGER PRIMARY KEY ASC, uid TEXT, player_name, balance INTEGER)")
            cur.execute("CREATE TABLE purchases(key INTEGER PRIMARY KEY ASC, player_key INTEGER, ntf_key INTEGER, spent INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)") #TODO - Add timestamp

            with db:
                # Create no-owner player
                cur.execute(f'INSERT INTO player(uid, player_name, balance) VALUES( ?,?,?)',("0", "Unowned", 0))




    def emit_routes(self):
        """ Emit Routes for including in HTTP viewer

        """
        return [
                {
                    "name": "NTF Game",
                    "uri": "/ntf/",
                    "callback": self.http_index,
                    "major": True
                },
                {
                    "name": "NTF Game Images",
                    "uri": "/ntf/images/<file>",
                    "callback": self.image,
                    "major": False
                }
            ]


    def http_index(self):
        """ Main page for viewing game details

        """

        # Connect to DB
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()

        output = """
<style>
table img
{
    height: 1.35em;
}
</style>
<div id="info">
<h1> No Tangible Function Collecting Game </h1>
<p>This is a collecting game where players accumulate credits and use them to bid
on NTFs of the hardware in my collection. The only thing you are getting is a
record in a database that shows you are tied to that image. The images are shown
in the on screen chat next to your username with other badges you have.</p>

<p>To use your points chat when the stream is live with "!bid" followed by the
name of the NTF you want to get. </p>
</div>
        """
        # == NTFs ==
        res = cur.execute("SELECT ntf.ntf_name, ntf.ntf_image, ntf.value, player.player_name FROM ntf INNER JOIN player ON ntf.player_key = player.key ORDER BY ntf.value DESC")
        data = res.fetchall()
        if len(data) > 0:
            # Display data as table
            output += "<h2>NTFs:</h2><table>"
            output += "<tr><th>Name</th><th>Image</th><th>Value</th><th>Owner</th></tr>"
            for row in data:
                output += f'<tr id=\"{row[0]}\">'
                output += f'<td>{row[0]}</td><td><a href=\"/ntf/images/{row[1]}\"><img src=\"/ntf/images/{row[1]}\"></a></td><td>{row[2]}</td><td><a href=\"#{row[3]}\">{row[3]}</a></td>'
                output += f'</tr>'
            output += "</table>"

        else:
            output += "<h2>No NTFs Found</h2>"


        # == Players ==
        res_players = cur.execute("SELECT player.player_name,player.balance,player.key FROM player")
        data = res_players.fetchall()

        if len(data) > 0:
            output += "<h2>Players:</h2><table>"
            output += "<tr><th>Name</th><th>Balance</th><th>Net Worth</th><th>Owned</th></tr>"
            sortable=[]
            for row in data:
                if row[0] == "Unowned":
                    continue
                # Get owned ntfs
                res_ntfs = cur.execute(f'SELECT ntf_image,ntf_name,value FROM ntf WHERE player_key = ?',[str(row[2])])
                ntfs = res_ntfs.fetchall()
                net_worth = int(row[1])

                output_ntfs=""
                ntf_sortable=[]
                if len(ntfs) > 0:
                    for col in ntfs:
                        ntf_sortable.append({"name":col[1],"image":col[0]})
                        net_worth += int(col[2])

                sortable.append({
                    "name":row[0],
                    "balance":row[1],
                    "net_worth":net_worth,
                    "ntfs":ntf_sortable,
                    })

            sorted_data = sorted(sortable, key=lambda d: d['net_worth'], reverse=True)


            for row in sorted_data:

                output += f'<tr id=\"{row["name"]}\">'
                output += f'<td>{row["name"]}</td><td>{row["balance"]}</td><td>{row["net_worth"]}</td>'
                output += f'<td>'
                if len(row["ntfs"]) > 0:
                    for col in row["ntfs"]:
                        output += f'<a href=\"#{col["name"]}\"><img src=\"/ntf/images/{col["image"]}\"></a>'
                output += f'</td>'

                output += f'</tr>'
            output += "</table>"


        else:
            output += "<h2>No Playerss Found</h2>"

        # == Purchases ==
            #cur.execute("CREATE TABLE purchases(key INTEGER PRIMARY KEY ASC, player_key INTEGER, ntf_key INTEGER, spent INTEGER)")
        res = cur.execute("SELECT  purchases.timestamp, ntf.ntf_name, ntf.ntf_image, purchases.spent,player.player_name FROM purchases INNER JOIN player ON purchases.player_key = player.key INNER JOIN ntf ON purchases.ntf_key = ntf.key ORDER BY purchases.timestamp DESC LIMIT 100")
        data = res.fetchall()
        if len(data) > 0:
            output += "<h2>Purchases:</h2><table>"
            output += "<tr><th>Timestamp</th><th>Name</th><th>Image</th><th>Cost</th><th>Buyer</th></tr>"
            for row in data:
                # output += f"<tr id=\"{row[0]}\">"
                # output += f"<td>{row[0]}</td><td>{row[1]}</td>"
                for col in row:
                        if ".jpg" in str(col):
                            output += f'<td><img src=\"/ntf/images/{col}\"></td>'
                        else:
                            output += f'<td>{col}</td>'
                output += f'</tr>'
            output += "</table>"

        else:
            output += "<h2>No Purchases Found</h2>"

        output+="""
<h3> More Details </h3>
<ul>
<li>You can gain points by redeeming channel points on Twitch, chatting on
Youtube, or donating on any platform.</li>

<li> If you want to suggest new NTFs, post in the
<a href=\"https://discord.gg/E6xgGs6\">#tt-live channel of my Discord Server</a>.
Keep in mind it can only be of hardware I own because I need to own the rights to
the images to display them on stream. If you want to make a request for an NTF
more likely to happen, take a screenshot of the subject and crop it square and
post it with your suggestion on Discord.
</li>

<li>In order to outbid an already owned NTF you need to bid at least 20 percent more
than the current value.</li>

<li><p> There are three different actions a "!bid" command will perform. Here are
examples of them </p>

<table>
<tr>
    <th>Command</th><th>Circumstance</th><th>Outcome</th>
</tr>
<tr>
    <td>!bid 500 Atari 520ST</th><td>Player wants to buy NTF for 500 points</td><td>If the NTF value is less than the bid and they have the balance, they will win the NTF and the new value will be their bid.</td>
</tr>
<tr>
    <td>!bid Atari 520ST</th><td>Player wants to buy NTF at minimum cost</td><td>Bid value is set to 1.20X current NTF value</td>
</tr>
<tr>
    <td>!bid 100 Atari 520ST</th><td>Player already owns NTF</td><td>They add 100 points to the value of NTF</td>
</tr>
</table>
</li>

</ul>

        """

        return output


    def image(self,file=None):
        """ Send image file from path to client """

        return send_file(f'ntf/images/{file}')


    def db_add_NTF(self, ntf_name, ntf_image):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        print("Adding "+ntf_name+ ntf_image)
        ntf_key=self.db_get_ntf_key(ntf_name)
        if ntf_key is not None:
            return
        # ntf_name, ntf_image, value, player_key
        with db:
            cur.execute(f'INSERT INTO ntf(ntf_name, ntf_image, value, player_key) VALUES( ?,?,1,1)',(ntf_name, ntf_image))


    def db_update_ntf_owner_value(self, ntf_key, player_key,value):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            try:
                cur.execute(f'UPDATE ntf SET player_key = ?, value = ? WHERE key = ?',(player_key,value,ntf_key))
            except Exception as e:
                print(f'Error: {e}')


    def db_update_ntf_rename(self, ntf_name_old, ntf_name_new):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            try:
                cur.execute(f'UPDATE ntf SET ntf_name = ? WHERE ntf_name = ?',(ntf_name_new,ntf_name_old))
            except Exception as e:
                print(f'Error: {e}')

    def db_get_ntfs_player(self, player_key):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            res = cur.execute(f'SELECT ntf_name, ntf_image FROM ntf WHERE player_key = ?',[str(player_key)])
            data = res.fetchall()
            return data


    def db_get_ntf_key(self, ntf_name):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            res = cur.execute(f'SELECT ntf.key FROM ntf WHERE ntf_name = ?',[str(ntf_name)])
            data = res.fetchone()
            if data is None:
                return None
            else:
                return data[0]

    def db_get_ntf_value(self, ntf_key):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            res = cur.execute(f'SELECT ntf.value FROM ntf WHERE key = ?',[str(ntf_key)])
            data = res.fetchone()
            return data[0]

    def db_get_ntf_owner(self, ntf_key):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            res = cur.execute(f'SELECT ntf.player_key FROM ntf WHERE key = ?',[str(ntf_key)])
            data = res.fetchone()
            return data[0]



    def db_add_player(self, uid, player_name, balance):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            cur.execute(f'INSERT INTO player(uid, player_name, balance) VALUES( ?,?,?)',(uid, player_name, balance))


    def db_update_player_balance(self, uid, balance_difference):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            try:
                cur.execute(f'UPDATE player SET balance = balance + ? WHERE uid = ?',(int(balance_difference),str(uid)))
            except Exception as e:
                print(f'Error: {e}')


    def db_update_player_balance_name(self, name, balance_difference):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            try:
                cur.execute(f'UPDATE player SET balance = balance + ? WHERE player_name = ?',(int(balance_difference),str(name)))
            except Exception as e:
                print(f'Error: {e}')


    def db_get_player_balance(self, uid):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            try:
                res = cur.execute(f'SELECT balance FROM player WHERE uid = ?',[str(uid)])
                data = res.fetchone()
                return data[0]
            except Exception as e:
                print(f'Error: {e}')
                return None


    def db_get_player_key(self, uid):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            res = cur.execute(f'SELECT player.key FROM player WHERE uid = ?',[str(uid)])
            data = res.fetchone()
            if data is None:
                return False
            else:
                return data[0]



    def db_add_purchase(self, player_key, ntf_key,spent):
        db = sqlite3.connect("ntf/ntf-game.db")
        cur = db.cursor()
        # ntf_name, ntf_image, value, player_key
        with db:
            try:
                cur.execute(f'INSERT INTO purchases(player_key, ntf_key,spent) VALUES( ?,?,?)',( player_key, ntf_key,spent))
            except Exception as e:
                print(f'Error: {e}')
                return None


    def game_purchase(self,player_uid,ntf_name,bid):
        print(f'game_purchase [{player_uid}][{ntf_name}][{bid}]')

        # Get keys from names
        ntf_key=self.db_get_ntf_key(ntf_name)
        player_key=self.db_get_player_key(player_uid)

        if bid < 0:
            return {"status":False,"error":"Get lost"}

        # Get NTF and confirm exists
        if ntf_key is None:
            print("NTF not found")
            return {"status":False,"error":"NTF not found"}
        print("got key")

        # Get NTF value and check bid is enough
        ntf_value=self.db_get_ntf_value(ntf_key)

        if bid == 0:
            # Bid not provided, assume minimum to own
            bid = int(ntf_value*1.2)

        if bid < int(ntf_value*1.2):
            print(f'Bid not enough: {bid} , {ntf_value*1.2}')
            return {"status":False,"error":"Bid insufficient, at least "+str(ntf_value*1.2)+" needed"}

        # Check player can afford bid and balance
        balance = float(self.db_get_player_balance(player_uid))
        print(f'Check player can afford bid and balance | {bid} < {balance}')
        if bid > balance:
            print("player too poor")
            return {"status":False,"error":"Balance insufficient"}




        # Update owner
        print("Update owner")
        if self.db_get_ntf_owner(ntf_key) == player_key:
            # Already owns, add bid to existing value
            print("Already owns, add bid to existing value")
            self.db_update_ntf_owner_value( ntf_key, player_key,int(ntf_value+bid))
        else:
            print("got value")


            self.db_update_ntf_owner_value( ntf_key, player_key,bid)

        # Charge player
        print("Charge player")
        self.db_update_player_balance(player_uid, -1*bid)

        # Log transaction
        print("Log transaction")
        self.db_add_purchase(player_key, ntf_key,bid)

        return {"status":True}


    def receive_donate(self,data):
        """Respond to bit and sub messages"""
        print("Donate NTF")

        # Bits
        if data["amount"].endswith("b"):
            if not self.db_get_player_key(data["uid"]):
                self.db_add_player(data["uid"], data["from_name"], 100)
            print("Bits")
            data["amount"] = data["amount"].replace("b","")
            # Set minimum donation at 100 bits to trigger DECTalk
            self.db_update_player_balance(data["uid"], int(data["amount"]))

        # Subs
        elif data["amount"].endswith("s"):
            if not self.db_get_player_key(data["uid"]):
                self.db_add_player(data["uid"], data["from_name"], 100)
            # Send nessage
            data["amount"] = data["amount"].replace("s","")
            print("Sub: "+data["from_name"] +" - "+data["amount"])
            self.db_update_player_balance(data["uid"], int(data["amount"]))
        else:
            print("No suffix")
            self.db_update_player_balance(data["uid"], data["amount"])
        return


    def receive_interact(self,data):
        """Respond to interactions"""

        if data["kind"] == "Add NTF":
            self.db_add_NTF(data["message"].split("|")[0], data["message"].split("|")[1])
            #self.add_replace(from_name,message)

        if data["kind"] == "Rename NTF":
            print("Rename NTF")
            self.db_update_ntf_rename(data["message"].split("|")[0], data["message"].split("|")[1])
            #self.add_replace(from_name,message)

        if data["kind"] == "Add Player":
            self.db_add_player(data["message"].split("|")[0], data["message"].split("|")[1], data["message"].split("|")[2])

        if data["kind"] == "Redeem Credit":
            if not self.db_get_player_key(data["uid"]):
                self.db_add_player(data["uid"], data["from_name"], 100)
            self.db_update_player_balance(data["uid"], 1000)

        if data["kind"] == "Redeem Credit 10X":
            if not self.db_get_player_key(data["uid"]):
                self.db_add_player(data["uid"], data["from_name"], 100)
            self.db_update_player_balance(data["uid"], 11000)


        return


    def receive_chat(self,data):
        """Output message to CLI for chat"""

        response={}

        if "youtube" in data["uid"]:
            # Give youtube chatters 50 points per chat since there are no channel points there
            if not self.db_get_player_key(data["uid"]):
                self.db_add_player(data["uid"], data["from_name"], 100)
            self.db_update_player_balance(data["uid"], 50)

        if data["text"].startswith("!bid"):
            print("Do bid")
            if not self.db_get_player_key(data["uid"]):
                self.db_add_player(data["uid"], data["from"], 100)

            if len(data["text"].split(" ")) > 2:
                print("multiple spaces")
                try:
                    bid = int(data["text"].split(" ")[1])
                    print("has bid")
                    r = self.game_purchase(data["uid"],
                                       data["text"].replace("!bid ","").replace(data["text"].split(" ")[1]+" ",""), bid)
                except ValueError:
                    print("no bid")
                    r = self.game_purchase(data["uid"],data["text"].replace("!bid ",""), 0)
            else:
                r = self.game_purchase(data["uid"],data["text"].replace("!bid ",""), 0)

            if not r["status"]:
                print("Replying with: " + r["error"])
                response["reply"] = "NTF: "+r["error"]

        player_key = self.db_get_player_key(data["uid"])
        if player_key is not None:
            ntfs = self.db_get_ntfs_player(player_key)
            if len(ntfs) > 0:
                if data["icons"] is None:
                    data["icons"] = []
                for col in ntfs:
                    data["icons"].append(self.base_URL+"/ntf/images/"+col[1])

        self.emit_chat(data)

        if data["text"].startswith("!ntf"):
            response={"reply":"Go to https://chat.techtangents.net/ntf/ find more info about the NTF collecting chat game"}
        return response
