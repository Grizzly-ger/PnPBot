import datetime
import glob
import json

import nextcord
import urllib3
from bs4 import BeautifulSoup
from nextcord import *
from nextcord.ext import tasks, commands
import socket

from cogs.settings import Settings


class Foundry(commands.Cog):
    def __init__(self, bot, con, cur, config, foundryurl, host, port):
        self.bot = bot
        self.con = con
        self.cur = cur
        self.foundryurl = foundryurl
        self.HOST = host
        self.PORT = port
        self.config = config
        self.status = {}

    def cog_unload(self):
        self.foundry_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.bot.get_channel(self.config["player_display_channel"])
            self.bot.get_channel(self.config["world_display_channel"])
        except:
            print("World und/oder Player Display Channel müssen noch festgelegt werden")
        else:
            self.foundry_task.start()

    @commands.command()
    async def foundry_state(self, ctx):
        await self.parse_foundry()
        if self.status["active"] is None:
            message = "Aktuell ist Foundry nicht erreichbar."
        elif self.status["active"]:
            message = f"Aktuell ist die Welt **{self.status['world']}** geladen und es sind **{self.status['users']}** SpielerInnen online."
        else:
            message = "Aktuell ist keine Welt geladen"
        await ctx.channel.send(message)

    @tasks.loop(minutes=1.0)
    async def foundry_task(self):
        await self.parse_foundry()
        player_display_channel = self.bot.get_channel(self.config["player_display_channel"])
        world_display_channel = self.bot.get_channel(self.config["world_display_channel"])
        if self.status["active"] is None:
            world_name = "Foundry ist offline"
            users_display_channel_name = "Foundry ist offline"
        elif self.status["active"]:
            self.cur.execute(f"SELECT name FROM 'foundry_worlds' WHERE world = '{self.status['world']}';")
            try:
                row = self.cur.fetchone()[0]
                world_name = f"Welt: {row}"
            except:
                world_name = f"Unbekannte Welt: {self.status['world']}"
            users_display_channel_name = f"Online Users: {self.status['users']}"
        else:
            world_name = "Setup Modus"
            users_display_channel_name = "Setup Modus"

        if player_display_channel.name != str(users_display_channel_name):
            await player_display_channel.edit(name=users_display_channel_name)
        if world_display_channel.name != world_name:
            await world_display_channel.edit(name=world_name)

    @commands.command(
        aliases=["swdc"],
        help="Legt den Audiochannel in dem sich der Author befindet als World Display Channel fest",
        # usage="category_id",
    )
    @commands.is_owner()
    async def set_world_display_channel(self, ctx):
        if ctx.author.voice:
            voicechannel = ctx.author.voice.channel
            message = f"Der World Display Channel wurde festgelegt"
            self.cur.execute(f"INSERT OR REPLACE INTO 'settings' (key, value, is_int) "
                             f"VALUES('world_display_channel',{voicechannel.id}, 1);")
            self.con.commit()
        else:
            message = "Du bist mit keinem Audiokanal verbunden!"
        await ctx.channel.send(message)

    @commands.command(
        aliases=["spdc"],
        help="Legt den Audiochannel in dem sich der Author befindet als Player Display Channel fest",
        # usage="category_id",
    )
    @commands.is_owner()
    async def set_player_display_channel(self, ctx):
        if ctx.author.voice:
            voicechannel = ctx.author.voice.channel
            message = f"Der Player Display Channel wurde festgelegt"
            self.cur.execute(f"INSERT OR REPLACE INTO 'settings' (key, value, is_int) "
                             f"VALUES('player_display_channel',{voicechannel.id}, 1);")
            self.con.commit()
        else:
            message = "Du bist mit keinem Audiokanal verbunden!"
        await ctx.channel.send(message)

    @commands.command(
        aliases=["afw"],
        help="Speichert den gewünschten Namen zu einer Welt",
        usage="world \"World Name\"",
    )
    @commands.is_owner()
    async def add_foundry_world(self, ctx, world: str, name: str):
        self.cur.execute(f"INSERT OR REPLACE INTO 'foundry_worlds' (world, name) "
                         f"VALUES('{world}','{name}');")
        self.con.commit()

    @commands.command(
        aliases=["cfw"],
        help="Speichert den gewünschten Namen zu einer Welt",
        usage="world \"World Name\"",
    )
    async def change_foundry_world(self, ctx, id: int):
        import socket

        self.cur.execute(f"SELECT world,name FROM 'foundry_worlds' WHERE id = {id};")
        try:
            if id == 0:
                row = (None, "Setup")
            else:
                row = self.cur.fetchone()
        except:
            message = "Diese Welt ist nicht in der Datenbank vorhanden!"
        else:
            world = row[0]
            name = row[1]
            await self.parse_foundry()
            if self.status["world"] == world:
                message = f"Die Welt **{name}** ist bereits aktiv!"
            elif (self.status["users"] is not None) and (self.status["users"] >= 1):
                message = f"Es sind noch Spieler in der aktuellen Welt eingeloggt."
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket:
                    socket.settimeout(30)
                    socket.connect((self.HOST, self.PORT))
                    socket.sendall(f"setworld {world}".encode())
                    data = socket.recv(1048576)
                    message = data.decode()
                    if message is None:
                        message = "Das ändern der Welt hat nicht geklappt. Läuft der Socket?"
                    socket.sendall("exit".encode())
        await ctx.channel.send(message)

    @commands.command(
        aliases=["rfw"],
        help="Löscht eine Welt aus der Datanbank anhand der Nummer",
        usage="number",
    )
    @commands.is_owner()
    async def remove_foundry_world(self, ctx, id: int):
        self.cur.execute(f"DELETE FROM 'foundry_worlds' WHERE id = {id};")
        self.con.commit()

    @commands.command(
        aliases=["lfw"],
        help="Zeigt alle gespeichterten Foundry Welten",
        # usage="world \"World Name\"",
    )
    async def list_foundry_world(self, ctx):
        self.cur.execute(f"SELECT id,world,name FROM 'foundry_worlds';")
        rows = self.cur.fetchall()
        message = ""
        if len(rows) >= 1:
            rows.insert(0, (0, "Setup", "Setup"))
            for row in rows:
                message += f"{row[0]}: {row[1]} -> {row[2]}\n"
        else:
            message = "Keine Welten gespeichert!"
        embed = nextcord.Embed(title="Liste der bekannten Welten", description=message)
        await ctx.channel.send(embed=embed)

    async def parse_foundry(self):
        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        urllib3.disable_warnings()
        status = {}
        try:
            response = http.request('GET', self.foundryurl, timeout=5.0)
            soup = BeautifulSoup(response.data, 'html.parser')
            status = json.loads(soup.text)
        except:
            status["active"] = None
        if not status["active"] or status["active"] is None:
            status["world"] = None
            status["users"] = None
        self.status = status

    async def cog_check(self, ctx):
        self.cur.execute(f"SELECT userid FROM 'admins';")
        admins = self.cur.fetchall()
        return (ctx.guild.owner_id == ctx.message.author.id) or ((ctx.author.id,) in admins)


def setup(bot, **extras):
    con = extras["sqlitecon"]
    cur = extras["sqlitecur"]
    config = extras["config"]
    foundryurl = extras["foundryurl"]
    host = extras["socketip"]
    port = extras["socketport"]
    bot.add_cog(Foundry(bot, con, cur, config, foundryurl, host, port))
