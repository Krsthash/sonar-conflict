import asyncio
import datetime
import json
import threading
import time
import logging
from functools import partial, wraps

import discord
import requests
from discord.ext import commands, tasks

BOT = discord.Client(intents=discord.Intents().all())

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
LISTENING_CHANNEL = None
SHIP_SYNC_INFO = []
LAST_UPDATE_AT = None
LAST_SEND_AT = None
MSGS_PROCESSED = []
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
    global LAST_UPDATE_AT
    global LAST_SEND_AT
    try:
        SERVER = BOT.guilds[1]
    except IndexError:
        print("Server not found.")
    print("ON_READY!")
    on_msg.start()
    api_listener.start()  # Starts the loop.
    LAST_UPDATE_AT = time.time()
    LAST_SEND_AT = time.time()
    update_game.start()
    bot_started = True

    log.info("Connected.")


@execute
def fetch_channel_object(id):
    """
    Example function to demonstrate how the api_listener function executes commands.
    """
    print("Fetching channel...")
    return SERVER.get_channel(id)


@execute
def get_all_channel_names():
    return SERVER.channels


@execute
def do_something(something):
    """
    Example function to demonstrate how the api_listener function executes commands.
    """
    print("Doing something...")
    print(something)
    print("Did something.")
    return "Test!"


@tasks.loop(seconds=2)
async def on_msg():
    global UPDATE_INFO
    global TORPEDO_INFO
    global SHIP_SYNC_INFO
    global LAST_UPDATE_AT
    global MSGS_PROCESSED
    if not LISTENING_CHANNEL:
        return
    headers = {"authorization": f"Bot {TOKEN}"}
    r = requests.get(f'https://discord.com/api/v9/channels/{LISTENING_CHANNEL.id}/messages?limit=2',
                     headers=headers)
    json_ = json.loads(r.text)
    messages = []
    for item in json_:
        messages.append(item)
    for msg in messages:
        if msg is None:
            print("No msgs!")
            return
        if msg in MSGS_PROCESSED:
            print("Already seen this message.", msg['content'])
            return
        log.info(f"Message! {msg}")
        print(f"MESSAGE FOUND...{PLAYER}, {msg['content']},{msg}")
        if str(msg['content']) == "":
            print("Possible attachments message found!")
            if len(msg['attachments']):
                print("Has attachments!")
                print(msg['attachments'])
                r = requests.get(url=msg['attachments'][0]['url'])
                print(r)
                print(r.text)
                print(r.content)
                msg['content'] = f"MISSION-INFORMATION{r.content}"  # .read()
                ON_MESSAGE_BUFFER.append(msg)
        elif str(msg['content'][1]) != str(PLAYER):
            if msg['content'][2] == ']':
                ON_MESSAGE_BUFFER.append(msg)
                if msg['content'][4] == '[':
                    print("UPDATE MSG!", msg['content'][1], PLAYER)
                    LAST_UPDATE_AT = time.time()
                    UPDATE_INFO = msg['content'][3:].replace('[', '').replace(']', '').replace(' ', '').split('AND')[
                        0].split(',')
                    TORPEDO_INFO = msg['content'][3:].split('AND')[1:-1]
                    temp = []
                    for info in TORPEDO_INFO:
                        temp.append(info.replace('[', '').replace(']', '').replace(' ', '').split(','))
                    TORPEDO_INFO = temp
                    SHIP_SYNC_INFO = msg['content'][3:].split('SYUI')[-1]
                elif msg['content'].count("Player has died."):
                    UPDATE_INFO = "PLAYER HAS DIED"
        MSGS_PROCESSED.append(msg)
        if len(MSGS_PROCESSED) > 100:
            MSGS_PROCESSED = MSGS_PROCESSED[98:]


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
    print("Removing old games...")
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
        await asyncio.sleep(1)


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
    return message


@tasks.loop(seconds=1)
async def update_game():
    global bot_started
    if not bot_started:
        print("Bot not started!")
        return
    global LAST_UPDATE_AT
    if LAST_UPDATE_AT:
        if time.time() - LAST_UPDATE_AT > 10:
            print("Connection problems!", time.time()-LAST_UPDATE_AT)
    """
    Every update that goes to the other player *MUST* be sent through this function to ensure efficiency.
    """
    global SEND_INFO
    global LAST_SEND_AT
    # log.info(f'update game running.. {PLAYER}, {SEND_INFO}')
    # print(f'update game running.. {PLAYER}, {SEND_INFO}')
    if SEND_INFO:
        if len(SEND_INFO.split("%!%")) > 1:
            print("FILE SEND INFO!")
            await CHANNEL.send(file=discord.File(SEND_INFO.split("%!%")[-1]))
            log.info("SENT SEND FILE INFO.")
            print(f"SENT FILE INFO, {PLAYER}")
            SEND_INFO = None
        else:
            d = await CHANNEL.send(SEND_INFO)
            LAST_SEND_AT = time.time()
            log.info(f"SENT SEND INFO. {PLAYER}, {d}")
            print(f"SENT INFO, {PLAYER}, {d}")
            SEND_INFO = None


@tasks.loop(seconds=1)
async def api_listener():
    """
    Listens for any new commands in the execution queue.
    Upon finding new commands it executes them and removes them from the queue.
    """
    # print(f"API LISTENER WORKING...{PLAYER}")
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
