import nextcord
from discord.ext import commands
from nextcord import *
from cogs import settings

from cogs.settings import Settings


class Groups(commands.Cog):
    def __init__(self, bot, con, cur, config):
        self.bot = bot
        self.con = con
        self.cur = cur
        self.config = config

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     pass

    # @commands.Cog.listener()
    # async def on_member_join(self, member):
    #     pass

    # @commands.Cog.listener()
    # async def on_member_remove(self, member):
        # channels = await Settings.get_user_channels(self, member.id)
        # for channel in channels:
        #     print(channel)
        #     try:
        #         await self.bot.get_channel(channel).delete()
        #     except:
        #         print(f"Der Kanal mit der ID {channel} wurde nicht gefunden. Ist er bereits gelöscht? "
        #               f"Ich lösche ihn jetzt aus der Dantenbank")
        #
        #     await Settings.remove_user_channels(self, member.id, channel)

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     # channels = await self.get_user_channels(message.author.id)
    #     # print(channels)
    #     pass

    @commands.command(
        # aliases=["inv", "invite"],
        help="Erstellt eine Einladung",
        usage="#channel",
    )
    async def create_group(self, ctx, name):
        categorys = await self.fetch_categorys(ctx)
        role = await ctx.guild.create_role(name=name)
        overwrites_default = nextcord.PermissionOverwrite.from_pair(Permissions.none(), Permissions.all())
        overwrites_role_rw = nextcord.PermissionOverwrite.from_pair(Permissions.text(), Permissions.none())
        overwrites_role_ro = nextcord.PermissionOverwrite(view_channel=True, read_messages=True,
                                                          read_message_history=True, send_messages=False,
                                                          create_private_threads=False, create_public_threads=False,
                                                          manage_messages=False)
        overwrites_role_voice = nextcord.PermissionOverwrite.from_pair(Permissions.voice(), Permissions.none())
        overwrites_role_rw.view_channel = True
        overwrites_role_voice.view_channel = True
        overwrites = {
            ctx.guild.default_role: overwrites_default,
            role: overwrites_role_rw,
        }
        overwrites_ro = {
            ctx.guild.default_role: overwrites_default,
            ctx.guild.get_role(self.config["admin_role_id"]): nextcord.PermissionOverwrite.from_pair(Permissions.text(), Permissions.none()),
            role: overwrites_role_ro,
        }
        overwrites_voice = {
            ctx.guild.default_role: overwrites_default,
            role: overwrites_role_voice,
        }
        category = await ctx.guild.create_category(name, overwrites=overwrites, position=categorys[-1].position-1)
        await category.create_text_channel("Ankündigungen", overwrites=overwrites_ro)
        await category.create_text_channel("Allgemein", overwrites=overwrites)
        await category.create_text_channel("IC", overwrites=overwrites)
        await category.create_text_channel("Chronik", overwrites=overwrites)
        await category.create_text_channel("Offtopic", overwrites=overwrites)
        await category.create_voice_channel("Talk", overwrites=overwrites_voice)
        await category.create_voice_channel("Privat", user_limit=2, overwrites=overwrites_voice)
        self.cur.execute(f"INSERT INTO 'groups' ('groupname','category_id', 'role_id') VALUES ('{name}', {category.id}, {role.id});")
        self.con.commit()

    @commands.command(
        aliases=["remove_group"],
        help="Erstellt eine Einladung",
        usage="@rolle",
    )
    async def delete_group(self, ctx, group: nextcord.Role):
        self.cur.execute(f"SELECT category_id from 'groups' WHERE role_id = {group.id}")
        category = self.bot.get_channel(self.cur.fetchone()[0])
        channels = category.channels
        for channel in channels:
            self.cur.execute(f"DELETE FROM 'user_channels' WHERE channel = {channel.id}")
            await channel.delete()
        await category.delete()
        await group.delete()
        self.cur.execute(f"DELETE FROM 'groups' WHERE role_id = {group.id}")
        self.con.commit()

    @commands.command(
        # aliases=["inv", "invite"],
        help="Füge einen User einer Gruppe hinzu.",
        usage="@user [In einem channel in dem der User anpingbar ist]",
    )
    async def add_user(self, ctx, member: nextcord.Member, group: nextcord.Role):
        self.cur.execute(f"SELECT category_id from 'groups' WHERE role_id = {group.id}")
        category = self.bot.get_channel(self.cur.fetchone()[0])
        for channel in category.channels:
            if channel.name.lower() == member.name.lower():
                await ctx.channel.send(f"Der Spieler {member.name} ist scheinbar bereits Mitglied der Gruppe {group.name}!")
                break
        else:
            overwrites_role_hidden = nextcord.PermissionOverwrite.from_pair(Permissions.none(), Permissions.all())
            overwrites_role_rw = nextcord.PermissionOverwrite.from_pair(Permissions.text(), Permissions.none())
            overwrites_role_rw.view_channel = True
            overwrites = {
                ctx.guild.default_role: overwrites_role_hidden,
                group: overwrites_role_hidden,
                ctx.guild.get_role(self.config["admin_role_id"]): overwrites_role_rw,
                member: overwrites_role_rw
            }
            channel = await category.create_text_channel(member.name, overwrites=overwrites)
            await member.add_roles(group)
            settings.Settings.store_user_channels(self, member.id, channel.id)

    @commands.command(
        aliases=["delete_user"],
        help="Entfernt einen User aus einer Gruppe.",
        usage="@user [In einem channel in dem der User anpingbar ist]",
    )
    async def remove_user(self, ctx, member: nextcord.Member, group: nextcord.Role):
        self.cur.execute(f"SELECT category_id from 'groups' WHERE role_id = {group.id}")
        category = self.bot.get_channel(self.cur.fetchone()[0])
        category_channels = category.channels
        self.cur.execute(f"SELECT channel from 'user_channels' WHERE userid = {member.id}")
        user_channels = self.cur.fetchall()
        for channel in category_channels:
            if (channel.id,) in user_channels:
                self.cur.execute(f"DELETE FROM 'user_channels' WHERE channel = {channel.id}")
                await channel.delete()
                await member.remove_roles(group)
                self.con.commit()
                break
        else:
            await ctx.channel.send(f"Der Spieler {member.name} ist scheinbar kein Mitglied der Gruppe {group.name}!")

    async def fetch_categorys(self, ctx):
        channels = await ctx.guild.fetch_channels()
        categorys = []
        for channel in channels:
            if channel.type == nextcord.ChannelType.category:
                categorys.append(channel)
        categorys.sort(key=lambda x: x.position)
        return categorys

    async def cog_check(self, ctx):
        self.cur.execute(f"SELECT userid FROM 'admins';")
        admins = self.cur.fetchall()
        return (ctx.guild.owner_id == ctx.message.author.id) or ((ctx.author.id,) in admins)


def setup(bot, **extras):
    con = extras["sqlitecon"]
    cur = extras["sqlitecur"]
    config = extras["config"]
    bot.add_cog(Groups(bot, con, cur, config))
