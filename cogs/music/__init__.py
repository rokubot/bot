import asyncio
import copy
import datetime
import io
import math
import random
import time
import typing

import aiohttp
import async_timeout
import discord
import pomice
from discord.ext import commands, menus, tasks

import config
from ext.converter import SimpleTimeConverter


class Player(pomice.Player):
    """Custom pomice Player class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.context: commands.Context = None
        self.dj: discord.Member = None

        self.queue = asyncio.Queue()
        self.controller = None
        self.message = None

        self.waiting = False
        self.updating = False
        self.loop = False

        self.old_track = None

        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()

    def set_context(self, ctx: commands.Context):
        self.context = ctx
        self.dj = ctx.author

    async def do_next(self) -> None:
        if self.is_playing or self.waiting:
            return
        # Clear the votes for a new song...
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        if self.loop:
            track = self.old_track

        else:
            try:
                self.waiting = True
                with async_timeout.timeout(180):
                    track = await self.queue.get()
            except asyncio.TimeoutError:
                # No music has been played for 5 minutes, cleanup and disconnect...
                return await self.teardown()

        await self.play(track)
        self.waiting = False
        # Invoke our players controller...
        await self.invoke_controller()

    async def build_image(self):
        """Method which creates image for player"""
        track = self.current
        if not track:
            return

        params = {
            'title': track.title,
            'thumbnail_url': track.thumbnail,
            'seconds_played': self.position / 1000,
            'total_seconds': track.length / 1000,
            'line_1': f'Uploaded by: {track.author}',
            'line_2': f'Requested by: {track.requester}',
        }
        r = await self.bot.session.get("https://api.jeyy.xyz/discord/player", params=params)
        if r.status != 200:
            self.bot.logger.info(f'{r.status} {(await r.json())}')
            return None
        image = io.BytesIO(await r.read())
        return discord.File(image, 'player.png')

    async def invoke_controller(self) -> None:
        """Method which updates or sends a new player controller."""
        if self.updating:
            return

        self.updating = True

        if not self.controller:
            image = await self.build_image()
            embed = None
            if image is None:
                embed = self.build_embed()
            self.controller = InteractiveController(player=self)
            self.message = await self.context.send(embed=embed, file=image, view=self.controller)

        else:
            self.controller.stop()
            await self.controller.disable_all()

            image = await self.build_image()
            embed = None
            if image is None:
                embed = self.build_embed()
            self.controller = InteractiveController(player=self)
            self.message = await self.context.send(embed=embed, file=image, view=self.controller)

        self.updating = False

    def build_embed(self) -> typing.Optional[discord.Embed]:
        """Method which builds our players controller embed."""
        track = self.current
        if not track:
            return

        qsize = self.queue.qsize()

        pbar = ""
        tlpbar = round(track.length // 15)
        pppbar = round(self.position // tlpbar)

        for i in range(15):
            if i == pppbar:
                pbar += "🔘"
            else:
                pbar += "▬"

        embed = discord.Embed(title='Now Playing:', colour=config.color, timestamp=datetime.datetime.utcnow())
        embed.description = f'\n**[{track.title}]({track.uri})**\n\n'
        embed.set_thumbnail(url=track.thumbnail or "https://google.com")
        embed.add_field(name='Duration', value=str(pbar), inline=False)
        embed.add_field(name='Queue Length', value=str(qsize))
        embed.add_field(name='Volume', value=f'**`{self.volume}%`**')
        embed.add_field(name='DJ', value=self.dj.mention)
        embed.set_footer(text=f'Requested By : {track.requester}')
        return embed

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""

        if self.controller:
            self.controller.stop()
            await self.controller.disable_all()

        await self.destroy()

    @property
    def position(self) -> float:
        """Property which returns the player's position in a track in milliseconds"""
        current = self._current.original

        if not self.is_playing or not self._current:
            return 0

        if self.is_paused:
            return min(self._last_position, current.length)

        difference = (time.time() * 1000) - self._last_update

        last_pos = self._last_position if self._last_position else 0
        position = last_pos + difference

        if position > current.length:
            return 0

        return min(position, current.length)


class InteractiveController(discord.ui.View):
    """The Players interactive controller menu class."""

    def __init__(self, *, player: Player):
        super().__init__(timeout=None)
        self.player = player
        self.bot = self.player.context.bot

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.guild:  # Music only works in Servers
            return Falsr

        member = interaction.user
        if not member:
            return False

        if member not in interaction.guild.get_channel(int(self.player.channel.id)).members:
            return False

        return True

    async def disable_all(self):
        """Disable all buttons"""
        for child in self.children:
            child.disabled = True
        await self.player.message.edit(view=self)

    @discord.ui.button(label='⏸️')
    async def pause_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Pause button"""
        player = self.player
        ctx = player.context

        if player.is_paused:
            command = self.bot.get_command('resume')
            button.label = '⏸️'

        else:
            command = self.bot.get_command('pause')
            button.label = '▶️'
        try:
            check = await command.can_run(ctx)
            await command(ctx)
        except Exception as e:
            await self.player.context.channel.send(e)
        else:
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label='\u23F9')
    async def stop_command(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Stop button."""
        command = self.bot.get_command('stop')
        ctx = self.player.context

        try:
            check = await command.can_run(ctx)
            await command(ctx)
        except Exception as e:
            await self.player.context.channel.send(e)
        else:
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label='\u23ED')
    async def skip_command(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Skip button."""
        command = self.bot.get_command('skip')
        ctx = self.player.context

        try:
            check = await command.can_run(ctx)
            await command(ctx)
        except Exception as e:
            await self.player.context.channel.send(e)

    @discord.ui.button(label='\U0001f501')
    async def loop_command(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Loop button."""
        ctx = self.player.context
        command = self.bot.get_command('loop')

        try:
            check = await command.can_run(ctx)
            await command(ctx)
        except Exception as e:
            await self.player.context.channel.send(e)

    @discord.ui.button(label='\U0001F500')
    async def shuffle_command(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Shuffle button."""
        ctx = self.player.context
        command = self.bot.get_command('shuffle')

        try:
            check = await command.can_run(ctx)
            await command(ctx)
        except Exception as e:
            await self.player.context.channel.send(e)

    # @discord.ui.button(label='\u2795')
    # async def volup_button(self, button: discord.ui.Button, interaction: discord.Interaction):
    # """Volume up button"""
    # ctx = self.player.context
    # command = self.bot.get_command('vol_up')

    # try:
    # check = await command.can_run(ctx)
    # await command(ctx)
    # except Exception as e:
    # await self.player.context.channel.send(e)

    # @discord.ui.button(label='\u2796')
    # async def voldown_button(self, button: discord.ui.Button, interaction: discord.Interaction):
    # """Volume down button."""
    # ctx = self.player.context
    # command = self.bot.get_command('vol_down')

    # try:
    # check = await command.can_run(ctx)
    # await command(ctx)
    # except Exception as e:
    # await self.player.context.channel.send(e)

    # @discord.ui.button(label='\U0001F1F6 Queue')
    # async def queue_command(self, payload: discord.RawReactionActionEvent):
    # """Player queue button."""
    # message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    # ctx = await self.bot.get_context(message)

    # command = self.bot.get_command('queue')

    # try:
    # check = await command.can_run(ctx)
    # await command(ctx)
    # except Exception as e:
    # await self.player.context.channel.send(e)


class PaginatorSource(menus.ListPageSource):
    """Player queue paginator class."""

    def __init__(self, entries, *, per_page=8):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: menus.Menu, page):
        embed = discord.Embed(title='Coming Up...', colour=config.color)
        embed.description = '\n'.join(f'`{index}. {title}`' for index, title in enumerate(page, 1))

        return embed

    def is_paginating(self):
        # We always want to embed even on 1 page of results...
        return True


class Music(commands.Cog, name="Music", command_attrs=dict(hidden=True)):
    """Enjoy listening to music with your friends!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.emoji = '🎧'
        self.session = None
        self.bot.pomice = pomice.NodePool()
        self.leave_dead_vcs.start()
        self.bot.loop.create_task(self.start_nodes())

    def cog_unload(self):
        self.leave_dead_vcs.stop()
        self.bot.loop.create_task(self.destroy_nodes())

    async def destroy_nodes(self):
        """Destroy all players and disconnect from lavalink"""

        nodes = self.bot.pomice.nodes.copy().values()
        for node in nodes:
            await node.disconnect()

        if self.session:
            await self.session.close()

    @tasks.loop(minutes=10)
    async def leave_dead_vcs(self):
        """A task to leave vcs with no members"""

        for node in self.bot.pomice.nodes.values():
            for player in node.players.copy().values():
                channel = player.channel
                if channel is None:
                    await player.teardown()

                if not any(not member.bot for member in channel.members):
                    await player.teardown()
                    await player.context.send("Everyone left me alone in VC  Leaving VC...")

    @leave_dead_vcs.before_loop
    async def wait_to_start_task(self):
        await self.bot.wait_until_ready()

    async def start_nodes(self) -> None:
        """Connect and intiate nodes."""

        await self.bot.wait_until_ready()

        if self.bot.pomice.node_count > 0:
            await self.destroy_nodes()  # destroying old nodes

        self.session = aiohttp.ClientSession()
        nodes = config.nodes

        for n in nodes.values():
            node = await self.bot.pomice.create_node(bot=self.bot, session=self.session, **n)
            self.bot.dispatch('node_ready', node)

    @commands.Cog.listener()
    async def on_node_ready(self, node):
        self.bot.logger.info(f'{node._identifier} is ready!')

    @commands.Cog.listener('on_pomice_track_stuck')
    @commands.Cog.listener('on_pomice_track_end')
    @commands.Cog.listener('on_pomice_track_exception')
    async def on_player_stop(self, player: Player, track, _):
        await player.do_next()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Changing DJ on Voice State Update"""

        await self.bot.wait_until_ready()

        if (guild := member.guild) is None:
            return

        player: Player = guild.voice_client
        if not player:
            return

        if member == guild.me and after.channel is None:
            return await player.teardown()

        if member.bot:
            return

        if not player.channel or not player.context:
            return await player.teardown()

        channel = player.channel
        if member == player.dj and after.channel is None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    async def cog_check(self, ctx: commands.Context):
        """Cog wide check, which disallows commands in DMs."""

        if not ctx.guild:
            raise commands.NoPrivateMessage('Music commands are not available in Private Messages.')
            return False

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        """Coroutine called before command invocation.
        We mainly just want to check whether the user is in the players controller channel.
        """

        await self.bot.wait_until_ready()
        player: Player = ctx.voice_client

        if ctx.command.name == 'connect':
            return

        if not player:
            return

        if self.is_privileged(ctx):
            return

        channel = player.channel
        if not channel:
            return

        if player.is_connected:
            if ctx.author not in channel.members:
                raise commands.BadArgument(f'{ctx.author.mention}, you must be in **{channel.name}** to use voice commands.')

    def required(self, ctx: commands.Context):
        """Method which returns required votes based on amount of members in a channel."""

        player: Player = ctx.voice_client
        channel = player.channel
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.qualified_name == 'stop':
            if len(channel.members) == 3:
                required = 2

        return required

    def is_privileged(self, ctx: commands.Context):
        """Check whether the user is an Admin or DJ."""
        player: Player = ctx.voice_client

        return player.dj is ctx.author or ctx.author.guild_permissions.administrator

    @commands.hybrid_command()
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Connect to a voice channel."""
        player: Player = ctx.voice_client

        if player and player.is_connected:
            return await ctx.send('Bot is already connected.')

        channel = getattr(ctx.author.voice, 'channel', channel)
        if channel is None:
            raise commands.BadArgument("You must be in a voice channel or provide one to connect to.")

        await ctx.author.voice.channel.connect(cls=Player)
        player: Player = ctx.voice_client
        player.set_context(ctx)

        if isinstance(channel, discord.StageChannel):
            msg = await ctx.send('I need to be stage speaker to start playing music... Invite me to stage speaker.')
            await ctx.me.request_to_speak()

            def check(mem, before, after):
                return mem == ctx.me and after.suppress == False and mem.guild.id == ctx.guild.id

            try:
                mem, before, after = await self.bot.wait_for('voice_state_update', check=check, timeout=100)

            except asyncio.TimeoutError:
                raise commands.BadArgument("Took so long. Can't wait for you any longer, Aborting... ")

            finally:
                await msg.delete()
        else:
            try:
                await ctx.me.edit(deafen=True)
            except discord.HTTPException:
                pass
        await ctx.send(f"{config.tick} **Connected to {channel.mention}**")

    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: commands.clean_content):
        """Play or queue a song with the given query."""

        if not ctx.voice_client:
            await ctx.invoke(self.connect)

        player: Player = ctx.voice_client

        hack = discord.AllowedMentions.none()
        query = query.strip('<>')
        tracks = await player.get_tracks(query, ctx=ctx)

        if not tracks:
            return await ctx.send('No songs were found with that query. Please try again.', allowed_mentions=hack)

        if isinstance(tracks, pomice.Playlist):
            for track in tracks.tracks:
                await player.queue.put(track)

            await ctx.send(
                f'\n **🎶 Added {tracks.name}' f' with `{tracks.track_count}` songs to the queue.**', allowed_mentions=hack
            )
        else:
            await ctx.send(f'\n **🎶 Added {tracks[0].title}  to the queue**', allowed_mentions=hack)
            await player.queue.put(tracks[0])

        if not player.is_playing:
            await player.do_next()

    @commands.hybrid_command()
    async def pause(self, ctx: commands.Context):
        """Pause the currently playing song."""

        if not (player := ctx.voice_client):
            return await ctx.send('Bot is not connected to any voice channel.')

        if player.is_paused:
            return await ctx.send('Music is already paused.')

        if self.is_privileged(ctx):
            await ctx.send('An admin or DJ has paused the player.')
            player.pause_votes.clear()

            return await player.set_pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            await ctx.send('Vote to pause passed. Pausing player.', delete_after=10)
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to pause the player.', delete_after=15)

    @commands.hybrid_command()
    async def resume(self, ctx: commands.Context):
        """Resume a currently paused player."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.send('Bot is not connected to any voice channel.')

        if not player.is_paused:
            return await ctx.send('Music is not paused')

        if self.is_privileged(ctx):
            await ctx.send('An admin or DJ has resumed the player.')
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            await ctx.send('Vote to resume passed. Resuming player.')
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to resume the player.', delete_after=15)

    @commands.hybrid_command()
    async def skip(self, ctx: commands.Context):
        """Skip the currently playing song."""
        player: Player = ctx.voice_client

        if not player.is_connected:
            raise commands.BadArgument("Bot is not connected to Voice Channel.")

        if player.loop:
            player.skip_votes.clear()
            return await ctx.send('The song is in loop and cannot be skipped until loop')
        if self.is_privileged(ctx):
            await ctx.send('An admin or DJ has skipped the song.')
            player.skip_votes.clear()

            return await player.stop()

        if player.current is None:
            return await ctx.send("Currrently not playing any song to skip")

        if ctx.author == player.current.requester:
            await ctx.send('The song requester has skipped the song.')
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send('Vote to skip passed. Skipping song.')
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.send(f'{ctx.author.mention} has voted to skip the song.', delete_after=15)

    @commands.hybrid_command(aliases=['dc', "disconnect"])
    async def stop(self, ctx: commands.Context):
        """Stop the music and leaves the voice channel."""
        player: Player = ctx.voice_client

        if not player:
            raise commands.BadArgument("Bot is not connected to any Voice Channel.")

        if self.is_privileged(ctx):
            await ctx.send('An admin or DJ has stopped the music.')
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send('Vote to stop passed. Stopping the music.')
            return await player.teardown()
        else:
            await ctx.send(f'{ctx.author.mention} has voted to stop the player.', delete_after=15)

    @commands.hybrid_command(aliases=['vol'])
    async def volume(self, ctx: commands.Context, *, vol: int):
        """Change the players volume, between 1 and 100."""
        player: Player = ctx.voice_client

        if not player:
            raise commands.BadArgument("Bot is not connected to Voice Channel.")

        if not self.is_privileged(ctx):
            return await ctx.send('Only the DJ or admins may change the volume.')

        if not 0 < vol <= 200:
            return await ctx.send('Please enter a value between 1 and 200.')

        await player.set_volume(vol)
        await ctx.send(f'Set the volume to **{vol}**%')

    @commands.hybrid_command(aliases=['mix'])
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the players queue."""
        player: Player = ctx.voice_client

        if not player:
            raise commands.BadArgument("Bot is not connected to Voice Channel.")

        if player.queue.qsize() < 3:
            return await ctx.send('Add more songs to the queue before shuffling.')

        if self.is_privileged(ctx):
            await ctx.send('An admin or DJ has shuffled the playlist.')
            player.shuffle_votes.clear()
            return random.shuffle(player.queue._queue)

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send('Vote to shuffle passed. Shuffling the playlist.')
            player.shuffle_votes.clear()
            random.shuffle(player.queue._queue)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to shuffle the playlist.', delete_after=15)

    @commands.command(hidden=True)
    async def vol_up(self, ctx: commands.Context):
        """Command used for volume up button."""
        player: Player = ctx.voice_client

        if not player:
            return

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume + 10) / 10)) * 10

        if vol > 200:
            vol = 200
            await ctx.send('Maximum volume reached', delete_after=7)

        await player.set_volume(vol)

    @commands.command(hidden=True)
    async def vol_down(self, ctx: commands.Context):
        """Command used for volume down button."""
        player: Player = ctx.voice_client

        if not player:
            return

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume - 10) / 10)) * 10

        if vol < 0:
            vol = 0
            await ctx.send('Player is currently muted', delete_after=10)

        await player.set_volume(vol)

    @commands.command(name="loop", aliases=['repeat'])
    async def _loop(self, ctx):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player:
            return await ctx.send('Bot is not connected to any voice channel.')

        if not self.is_privileged(ctx):
            return await ctx.send('Only the DJ or admins can turn on/off loop.')

        if not player.is_playing:
            return await ctx.send('No songs are being played to loop')

        if player.loop:
            player.loop = False
            await ctx.send(
                f'You have **turned off** the loop `{player.current}`', allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            player.loop = True
            await ctx.send(f'You have **looped** `{player.current}`', allowed_mentions=discord.AllowedMentions.none())
            player.old_track = player.current

    @commands.hybrid_command(aliases=['eq'])
    async def equalizer(self, ctx: commands.Context, *, equalizer: str):
        """Change the players equalizer."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.send('Bot is not connected to any voice channel.')

        if not self.is_privileged(ctx):
            return await ctx.send('Only the DJ or admins may change the equalizer.')

        eqs = {
            'flat': wavelink.Equalizer.flat(),
            'boost': wavelink.Equalizer.boost(),
            'metal': wavelink.Equalizer.metal(),
            'piano': wavelink.Equalizer.piano(),
        }

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.send(f'Invalid EQ provided. Valid EQs:\n\n{joined}')

        await ctx.send(f'Successfully changed equalizer to {equalizer}', delete_after=15)
        await player.set_eq(eq)

    @commands.hybrid_command(aliases=['q', 'que'])
    async def queue(self, ctx: commands.Context):
        """Display the players queued songs."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.send("Bot is not connected VC")

        if player.queue.qsize() == 0:
            return await ctx.send('There are no more songs in the queue.', delete_after=15)

        entries = [track.title for track in player.queue._queue]
        pages = PaginatorSource(entries=entries)
        paginator = menus.MenuPages(source=pages, timeout=None, delete_message_after=True)

        await paginator.start(ctx)

    @commands.hybrid_command(aliases=['np', 'now_playing', 'current'])
    async def nowplaying(self, ctx: commands.Context):
        """Update the player controller."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.send("Bot is not connected to any voice channel")

        if not player.is_playing:
            return await ctx.send("Bot is not playing any music")

        if player.context:
            player.context.channel = ctx.channel

        await player.invoke_controller()

    @commands.hybrid_command(name='changedj')
    async def swap_dj(self, ctx: commands.Context, *, member: discord.Member):
        """Swap the current DJ to another member in the voice channel."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.send('Player is not connected.')

        if not self.is_privileged(ctx):
            return await ctx.send('Only admins and the DJ may use this command.', delete_after=15)

        members = self.bot.get_channel(int(player.channel_id)).members

        if member not in members:
            return await ctx.send(f'{member} is not currently in voice, so can not be a DJ.', delete_after=15)

        if member == player.dj:
            return await ctx.send('Cannot swap DJ to the current DJ... :)', delete_after=15)

        if member.bot:
            return await ctx.send('Cannot make a bot as DJ', delete_after=15)

        if member:
            player.dj = member
            return await ctx.send(f'{member.mention} is now the DJ.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
