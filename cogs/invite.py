import nextcord
from discord.ext import commands
from nextcord import *

from cogs.settings import Settings


class Invite(commands.Cog):
    def __init__(self, bot, con, cur, config):
        self.bot = bot
        self.con = con
        self.cur = cur
        self.config = config

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        overwrites_default = nextcord.PermissionOverwrite.from_pair(Permissions.none(), Permissions.all())
        overwrites_role_rw = nextcord.PermissionOverwrite.from_pair(Permissions.text(), Permissions.none())
        overwrites_role_rw.view_channel = True
        overwrites = {
            member.guild.default_role: overwrites_default,
            member: overwrites_role_rw,
            self.bot.guild.get_role(self.config["admin_role_id"]): overwrites_role_rw,
        }
        channel = await self.config["invite_category"].create_text_channel(member.name, overwrites=overwrites)

        embed = nextcord.Embed(color=nextcord.Colour.dark_green(), title="Willkommen",
                               description=f"Danke, dass du der Einladung gefolgt bist. "
                                           f"Alles weitere kommt dann vom GM!")
        await channel.send(embed=embed)
        Settings.store_user_channels(self,member.id, channel.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channels = await Settings.get_user_channels(self, member.id)
        for channel in channels:
            try:
                await self.bot.get_channel(channel).delete()
            except:
                print(f"Der Kanal mit der ID {channel} wurde nicht gefunden. Ist er bereits gelöscht? "
                      f"Ich lösche ihn jetzt aus der Dantenbank")
            Settings.remove_user_channels(self, member.id, channel)

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     channels = await self.get_user_channels(message.author.id)
    #     print(channels)
    #     pass

    @commands.command(
        aliases=["inv", "invite"],
        help="Erstellt eine Einladung",
        usage="#channel",
    )
    async def einladung(self, ctx):
        invitelink = await self.config["default_invite_channel"].create_invite(max_uses=1, max_age=60 * 60 * 24 * 7)
        await self.bot.get_channel(self.config["bot_channel_id"]).send(invitelink)

    async def cog_check(self, ctx):
        self.cur.execute(f"SELECT userid FROM 'admins';")
        admins = self.cur.fetchall()
        return (ctx.guild.owner_id == ctx.message.author.id) or ((ctx.author.id,) in admins)


def setup(bot, **extras):
    con = extras["sqlitecon"]
    cur = extras["sqlitecur"]
    config = extras["config"]
    bot.add_cog(Invite(bot, con, cur, config))
