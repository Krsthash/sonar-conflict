import asyncio
import datetime
import threading
import time
import logging
from functools import partial, wraps

import discord
from discord.ext import commands, tasks

BOT = commands.Bot(command_prefix="!", intents=discord.Intents().all())

# -------- GLOBAL VARIABLES -------- #
bot_started = False
toExecute = []
TOKEN = "OTM5NjM1MDI5Mjg0Mzg4OTI1.G7Z0nG.hsYenG13h9l24pCI9xJQzvpqhlzf0S33yiXaVA"
SERVER: discord.Guild
PLAYER = None
OPPONENT = None
ON_MESSAGE_BUFFER = []
ALLOW_WAIT = True
UPDATE_INFO = None
SEND_INFO = None
TORPEDO_INFO = []
CHANNEL = None
# ---------------------------------- #


# --------- Logging for debugging -------- #
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt="[%(asctime)s %(levelname)s]: %(message)s",
                              datefmt="%d-%m-%Y - %H:%M:%S")
fh = logging.FileHandler("log.log", "w")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)
log.info("\nStarting up...")
# ------------------------------------------


def execute(function):
    """
    A decorator, which appends the function with its arguments to the list.
    Should not be called standalone.
    """

    @wraps(function)  # Allows us to still access name and docstring of the wrapped function
    def wrapper(*args, **kwargs):
        func_list = [partial(function, *args, **kwargs), [None]]
        toExecute.append(func_list)
        log.info("Appended")
        log.info(toExecute)

        while toExecute[toExecute.index(func_list)][1] == [None]:
            time.sleep(0.5)
        result = toExecute[toExecute.index(func_list)][1]
        toExecute.pop(toExecute.index(func_list))
        return result

    return wrapper


@BOT.event
async def on_ready():
    global bot_started
    global SERVER
    global CHANNEL
    try:
        SERVER = BOT.guilds[1]
    except IndexError:
        print("Server not found.")
    CHANNEL = SERVER.get_channel(1084976743565234289)
    api_listener.start()  # Starts the loop.
    update_game.start()
    bot_started = True

    log.info("Connected.")


@execute
def do_something(something):
    """
    Example function to demonstrate how the api_listener function executes commands.
    """
    print("Doing something...")
    print(something)
    print("Did something.")
    return "Test!"


@BOT.event
async def on_message(msg):
    global UPDATE_INFO
    global TORPEDO_INFO
    log.info(f"Message! {msg}")
    print(f"MESSAGE FOUND...{PLAYER}")
    # ON_MESSAGE_BUFFER.append(msg)
    if str(msg.content[1]) != str(PLAYER) and msg.channel.id == 1084976743565234289:
        if msg.content[2] == ']':
            print("UPDATE MSG!", msg.content[1], PLAYER)
            UPDATE_INFO = msg.content[3:].replace('[', '').replace(']', '').replace(' ', '').split(',')
        elif msg.content[2] == '-':
            print("TOPEDO MESSAGE!")
            TORPEDO_INFO = msg.content[11:].replace('[', '').replace(']', '').replace(' ', '').split(',')




@execute
async def send_message(message: str, channel_id: int):
    """
    Sends a message to the specified Discord channel.

    :param message: The message content.
    :param channel_id: The id of the channel it needs to send to.
    """
    log.info("Sending the message...")
    msg = await SERVER.get_channel(channel_id).send(message)
    log.info(f"Sent message: {msg}")
    log.info("Message sent.")
    return msg


@execute
async def get_last_message(channel_id: int):
    messages = []
    async for msg in BOT.get_channel(channel_id).history(limit=1):
        messages.append(msg)
    return messages[0]


@execute
async def create_channel(channel_name: str) -> int:
    channel_id = await SERVER.create_text_channel(channel_name)
    return channel_id.id


@execute
async def remove_old_games():
    """
    Removes all text channels associated with games older than 2 hours.
    """
    current_time = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    log.info(f"Current time: {current_time}")
    log.info("Channels:")
    for channel in SERVER.channels:
        if channel.name[:4] == "game":
            timestamp = channel.name.split("-")[-1]
            timestamp = int(timestamp)
            log.info(f"Channel: {channel.name} Timestamp: {timestamp}")
            if current_time - timestamp > 7200:
                log.info("Channel will be deleted.")
                await channel.delete()
                log.info("Channel deleted.")


@execute
async def wait_for_message():
    """
    Waits until the bot receives a new message.
    """
    global ALLOW_WAIT

    log.info("Waiting for message...")
    while not len(ON_MESSAGE_BUFFER):
        await asyncio.sleep(0.5)
        if not ALLOW_WAIT:
            log.info("Waiting for message aborted.")
            return None
    message = ON_MESSAGE_BUFFER[0]
    ON_MESSAGE_BUFFER.pop(0)
    log.info("Awaited the message!")
    return


@tasks.loop(seconds=2)
async def update_game():
    """
    Every update that goes to the other player *MUST* be sent through this function to ensure efficiency.
    """
    global SEND_INFO
    log.info(f'update game running.. {PLAYER}, {SEND_INFO}')
    print(f'update game running.. {PLAYER}, {SEND_INFO}')
    if SEND_INFO:
        await CHANNEL.send(SEND_INFO)
        log.info("SENT SEND INFO.")
        print(f"SENT INFO, {PLAYER}")


@tasks.loop(seconds=1)
async def api_listener():
    """
    Listens for any new commands in the execution queue.
    Upon finding new commands it executes them and removes them from the queue.
    """
    print(f"API LISTENER WORKING...{PLAYER}")
    if len(toExecute):
        for function in toExecute:
            try:
                if function[1] == [None]:
                    result = None
                    if asyncio.iscoroutinefunction(function[0].func):
                        try:
                            result = await function[0]()
                        except Exception as E:
                            log.error(E)
                    else:
                        try:
                            result = function[0]()
                        except Exception as E:
                            log.error(E)
                    function[1] = result
            except AttributeError as e:
                print("Function does not exist.")
                print(e)


async def start_bot():
    """
    Starts the discord bot.
    """
    await BOT.start(TOKEN)
