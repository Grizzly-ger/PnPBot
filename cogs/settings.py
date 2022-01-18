import json

import nextcord
from nextcord import *
from nextcord.ext import commands


class Settings(commands.Cog):
    def __init__(self, bot, con, cur, config):
        self.bot = bot
        self.con = con
        self.cur = cur
        self.config = config

    @commands.Cog.listener()
    async def on_ready(self):
        self.cur.execute("CREATE TABLE IF NOT EXISTS 'user_channels' ("
                         "'id' INTEGER NOT NULL UNIQUE,"
                         "'userid'	INTEGER NOT NULL,"
                         "'channel'	INTEGER NOT NULL,"
                         "PRIMARY KEY('id' AUTOINCREMENT)"
                         ");")
        self.cur.execute("CREATE TABLE IF NOT EXISTS 'settings' ("
                         "'id'	INTEGER NOT NULL UNIQUE,"
                         "'key'	TEXT NOT NULL UNIQUE,"
                         "'value'	TEXT NOT NULL,"
                         "'is_int'	INTEGER NOT NULL,"
                         "PRIMARY KEY('id' AUTOINCREMENT)"
                         ");")
        self.cur.execute("CREATE TABLE IF NOT EXISTS 'foundry_worlds' ("
                         "'id'	INTEGER NOT NULL UNIQUE,"
                         "'world'	TEXT NOT NULL UNIQUE,"
                         "'name'	TEXT NOT NULL UNIQUE,"
                         "PRIMARY KEY('id' AUTOINCREMENT)"
                         ");")
        self.cur.execute("CREATE TABLE IF NOT EXISTS 'groups' ("
                         "'id'	INTEGER NOT NULL UNIQUE,"
                         "'groupname'	TEXT NOT NULL,"
                         "'category_id'	INTEGER NOT NULL UNIQUE,"
                         "'role_id'	INTEGER NOT NULL UNIQUE,"
                         "PRIMARY KEY('id' AUTOINCREMENT)"
                         ");")
        self.cur.execute("CREATE TABLE IF NOT EXISTS 'admins' ("
                         "'id'	INTEGER NOT NULL UNIQUE,"
                         "'userid'	INTEGER NOT NULL UNIQUE,"
                         "PRIMARY KEY('id' AUTOINCREMENT)"
                         ");")
        self.con.commit()

        self.cur.execute("SELECT key, value, is_int FROM 'settings';")
        rows = self.cur.fetchall()
        for row in rows:
            self.config[row[0]] = row[1] if (row[2] == 0) else int(row[1])

        if "guild_id" not in self.config:
            print("Die Guild-ID muss noch gesetzt werden")
        if "bot_channel_id" not in self.config:
            print("Der Bot-Message-Channel muss noch gesetzt werden")
        if "invite_category_id" not in self.config:
            print("Invite-Tree muss noch gesetzt werden")
        else:
            self.config["invite_category"] = self.bot.get_channel(self.config["invite_category_id"])
            self.config["default_invite_channel"] = self.bot.get_channel(self.config["default_invite_channel_id"])
        if "admin_role_id" not in self.config:
            print("Die Admin(GM)-Role-id muss noch gesetzt werden!")

    @commands.command(
        # aliases=["r"],
        help="Legt den Invite-Tree fest. Dort werden die Invite-Channels erstellt.",
        usage="category_id",
    )
    @commands.is_owner()
    async def set_invite_tree(self, ctx):
        # cat = async
        if "guild_id" in self.config:
            self.config["invite_category"] = ctx.channel.category
            self.config["default_invite_channel"] = ctx.channel

            if self.config["invite_category"] is not None:
                self.cur.execute(f"INSERT OR REPLACE INTO 'settings' (key, value, is_int) VALUES"
                                 f"('invite_category_id',{ctx.channel.category_id}, 1), "
                                 f"('default_invite_channel_id', {ctx.channel.id}, 1);")
                self.con.commit()
        else:
            await ctx.send("Du musst zuerst die Guild ID festlegen!")

    @commands.command(
        # aliases=["r"],
        help="Legt die Invite-Category fest. Dort werden die Invite-Channels erstellt.",
        usage="category_id",
    )
    @commands.is_owner()
    async def set_guild_id(self, ctx):
        # cat = async
        self.config["guild_id"] = ctx.channel.guild.id
        self.cur.execute(
            f"INSERT OR REPLACE INTO 'settings' (key, value, is_int) VALUES('guild_id',{self.config['guild_id']}, 1);")
        self.con.commit()

    @commands.command(
        # aliases=["r"],
        help="Legt den akutellen Channel für Bot-Messages fest.",
        # usage="category_id",
    )
    @commands.is_owner()
    async def set_bot_channel(self, ctx):
        self.config["overhead_category_id"] = ctx.channel.category_id
        self.config["bot_channel_id"] = ctx.channel.id
        self.cur.execute(f"INSERT OR REPLACE INTO 'settings' (key, value, is_int) "
                         f"VALUES('overhead_category_id',{self.config['overhead_category_id']}, 1),"
                         f"('bot_channel_id',{self.config['bot_channel_id']}, 1);")
        self.con.commit()

    @commands.command(
        # aliases=["r"],
        help="Setzt die angegebene Rolle als Admin Rolle",
        usage="@role",
    )
    @commands.is_owner()
    async def set_admin_role(self, ctx, role: nextcord.Role):
        self.config["admin_role_id"] = role.id
        self.cur.execute(f"INSERT OR REPLACE INTO 'settings' (key, value, is_int) "
                         f"VALUES('admin_role_id',{self.config['admin_role_id']}, 1);")
        self.con.commit()

    @commands.command(
        # aliases=["r"],
        help="Fügt einen User als Admin hinzu",
        usage="@user",
    )
    @commands.is_owner()
    async def add_admin(self, ctx, user: nextcord.Member):
        await user.add_roles(ctx.guild.get_role(self.config["admin_role_id"]))
        self.cur.execute(f"INSERT OR REPLACE INTO 'admins' (userid) "
                         f"VALUES({user.id});")
        self.con.commit()

    @commands.command(
        # aliases=["r"],
        help="Entfernt einen User als Admin",
        usage="@user",
    )
    @commands.is_owner()
    async def remove_admin(self, ctx, user: nextcord.Member):
        await user.remove_roles(ctx.guild.get_role(self.config["admin_role_id"]))
        self.cur.execute(f"DELETE FROM 'admins' WHERE userid ={user.id};")
        self.con.commit()

    @commands.command()
    async def check(self, ctx):
        await ctx.channel.send("Check!")

    async def get_user_channels(self, userid: int):
        self.cur.execute(f"SELECT channel FROM 'user_channels' WHERE userid = {userid};")
        channels = []
        try:
            rows = self.cur.fetchall()
        except:
            pass
        else:
            for row in rows:
                channels.append(row[0])
        return channels

    def store_user_channels(self, userid: int, channelid: int):
        self.cur.execute(f"INSERT INTO 'user_channels' ('userid','channel') VALUES ({userid},'{channelid}');")
        self.con.commit()

    def remove_user_channels(self, userid: int, channelid: int):
        self.cur.execute(f"DELETE FROM 'user_channels' WHERE userid = {userid} AND channel = {channelid};")
        self.con.commit()

    async def cog_check(self, ctx):
        self.cur.execute(f"SELECT userid FROM 'admins';")
        admins = self.cur.fetchall()
        return (ctx.guild.owner_id == ctx.message.author.id) or ((ctx.author.id,) in admins)


def setup(bot, **extras):
    con = extras["sqlitecon"]
    cur = extras["sqlitecur"]
    config = extras["config"]
    bot.add_cog(Settings(bot, con, cur, config))
