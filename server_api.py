import asyncio
import datetime
import json
import logging
import time
from functools import partial, wraps
from sys import stdout

import discord
import requests
from discord.ext import tasks

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
LOOP_LOGGING = False
# ---------------------------------- #

# --------- Logging for debugging -------- #
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt="[{asctime}.{msecs:03.0f}] <{name}> ({funcName})  {levelname}: \"{message}\"",
    datefmt="%H:%M:%S",
    style="{"
)
fh = logging.FileHandler("sever.log", "w")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)
sh = logging.StreamHandler(stdout)
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
log.addHandler(sh)
loop_log = logging.getLogger('loop_logger')
if LOOP_LOGGING:
    loop_log.setLevel(logging.DEBUG)
else:
    loop_log.setLevel(logging.INFO)
loop_log.addHandler(fh)
log.debug("Starting up...")
loop_log.debug("Loop logging enabled.")


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
        log.debug(f"Appended {func_list} to execution queue.")

        while toExecute[toExecute.index(func_list)][1] == [None]:
            time.sleep(0.5)
        result = toExecute[toExecute.index(func_list)][1]
        log.debug(f"Function {func_list[0]} finished.")
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
        log.error("Server not found.")
    if not on_msg.is_running():
        on_msg.start()
    if not api_listener.is_running():
        api_listener.start()  # Starts the loop.
    # LAST_UPDATE_AT = time.time()
    # LAST_SEND_AT = time.time()
    if not update_game.is_running():
        update_game.start()
    bot_started = True

    log.info("Connected to the server.")


@execute
def fetch_channel_object(id):
    """
    Example function to demonstrate how the api_listener function executes commands.
    """
    log.debug("Fetching channel object...")
    return SERVER.get_channel(id)


@execute
def get_all_channel_names():
    return SERVER.channels


@tasks.loop(seconds=1)
async def on_msg():
    global UPDATE_INFO
    global TORPEDO_INFO
    global SHIP_SYNC_INFO
    global LAST_UPDATE_AT
    global MSGS_PROCESSED
    if not LISTENING_CHANNEL:
        return
    if LAST_UPDATE_AT:
        if time.time() - LAST_UPDATE_AT < 1:
            loop_log.debug(f"Fetch too soon. Time: {time.time() - LAST_UPDATE_AT}")
            await asyncio.sleep(1 - (time.time() - LAST_UPDATE_AT))
            loop_log.debug(f"Fetch allowed. Time: {time.time() - LAST_UPDATE_AT}")
    headers = {"authorization": f"Bot {TOKEN}"}
    r = requests.get(f'https://discord.com/api/v9/channels/{LISTENING_CHANNEL.id}/messages?limit=2',
                     headers=headers)
    json_ = json.loads(r.text)
    if LAST_UPDATE_AT:
        loop_log.debug(f"Message fetching running... [{time.time() - LAST_UPDATE_AT}]")
    else:
        loop_log.debug(f"Message initial fetching running...")
    messages = []
    for item in json_:
        messages.append(item)
    for msg in messages:
        if msg is None:
            loop_log.debug(f"Channel is empty.")
            return
        if msg in MSGS_PROCESSED:
            # print("Already seen this message.", msg['content'])
            return
        loop_log.debug(f"Fetched a new message.")
        loop_log.debug(f"Content: {msg['content']}")
        # print(f"MESSAGE FOUND...{PLAYER}, {msg['content']},{msg}")
        if str(msg['content']) == "":
            loop_log.debug("Message is empty!")
            if len(msg['attachments']):
                loop_log.debug("Message has attachments!")
                r = requests.get(url=msg['attachments'][0]['url'])
                loop_log.debug(f"Attachments fetched. Status: {r.status_code}")
                msg_ = dict(msg)
                msg_['content'] = f"MISSION-INFORMATION{r.content}"
                ON_MESSAGE_BUFFER.append(msg_)
                LAST_UPDATE_AT = time.time()
        elif str(msg['content'][1]) != str(PLAYER):
            if msg['content'][2] == ']':
                ON_MESSAGE_BUFFER.append(msg)
                if msg['content'][4] == '[':
                    loop_log.debug(f"Message contains update information.")
                    # print("UPDATE MSG!", msg['content'][1], PLAYER)
                    LAST_UPDATE_AT = time.time()
                    UPDATE_INFO = msg['content'][3:].replace('[', '').replace(']', '').replace(' ', '').split('AND')[
                        0].split(',')
                    TORPEDO_INFO = msg['content'][3:].split('AND')[1:-1]
                    temp = []
                    for info in TORPEDO_INFO:
                        temp.append(info.replace('[', '').replace(']', '').replace(' ', '').split(','))
                    TORPEDO_INFO = temp
                    SHIP_SYNC_INFO = msg['content'][3:].split('SYUI')[-1]
                    loop_log.debug(f"Message update information: ")
                    if UPDATE_INFO:
                        loop_log.debug("UPDATE_INFO")
                    if TORPEDO_INFO:
                        loop_log.debug("TORPEDO_INFO")
                    if SHIP_SYNC_INFO:
                        loop_log.debug("SHIP_SYNC_INFO")
                elif msg['content'].count("Player has died."):
                    UPDATE_INFO = "PLAYER HAS DIED"
                    loop_log.debug("Message update information: ")
                    loop_log.debug("Enemy died.")
        MSGS_PROCESSED.append(msg)
        if len(MSGS_PROCESSED) > 100:
            loop_log.debug("Clearing message cache...")
            MSGS_PROCESSED = MSGS_PROCESSED[98:]


@execute
async def send_message(message: str, channel_id: int):
    """
    Sends a message to the specified Discord channel.

    :param message: The message content.
    :param channel_id: The id of the channel it needs to send to.
    """
    log.debug("Sending the message...")
    msg = await SERVER.get_channel(channel_id).send(message)
    log.debug(f"Message sent. Message: {message}")
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
    log.debug("Removing old games...")
    current_time = int(time.mktime(datetime.datetime.utcnow().timetuple()))
    log.debug(f"Current time: {current_time}")
    log.debug("Channels:")
    for channel in SERVER.channels:
        if channel.name[:4] == "game":
            timestamp = channel.name.split("-")[-1]
            timestamp = int(timestamp)
            log.debug(f"Channel: {channel.name} Timestamp: {timestamp}")
            if current_time - timestamp > 7200:
                log.debug("Channel will be deleted.")
                await channel.delete()
                log.debug("Channel deleted.")
                await asyncio.sleep(1)


@execute
async def wait_for_message() -> any:
    """
    Waits until the bot receives a new message.
    """
    global ALLOW_WAIT

    log.debug("Waiting for message...")
    while not len(ON_MESSAGE_BUFFER):
        await asyncio.sleep(0.5)
        if not ALLOW_WAIT:
            log.debug("Waiting for message aborted.")
            return None
    message = ON_MESSAGE_BUFFER[0]
    ON_MESSAGE_BUFFER.pop(0)
    log.debug("Awaited the message!")
    return message


@tasks.loop(seconds=1.1)
async def update_game():
    global bot_started
    global SEND_INFO
    global LAST_SEND_AT
    if not bot_started:
        loop_log.debug("Bot isn't connected, cannot update game.")
        return
    global LAST_UPDATE_AT
    if LAST_UPDATE_AT:
        if time.time() - LAST_UPDATE_AT > 10:
            log.warning(f"Connection problems, no updates for {time.time() - LAST_UPDATE_AT}s.")
            if time.time() - LAST_UPDATE_AT > 20:
                log.error("Pausing connection for 5 seconds...")
                await asyncio.sleep(5)
                log.warning("Resuming...")
    if LAST_SEND_AT:
        if time.time() - LAST_SEND_AT < 1 and SEND_INFO:
            loop_log.debug(f"Update attempted too soon: {time.time() - LAST_SEND_AT}")
            await asyncio.sleep(1 - (time.time() - LAST_SEND_AT))
            loop_log.debug(f"Update allowed. Time: {time.time() - LAST_SEND_AT}")
    """
    Every update that goes to the other player *MUST* be sent through this function to ensure efficiency.
    """
    if LAST_SEND_AT:
        loop_log.debug(f"Running update... {time.time() - LAST_SEND_AT}")
    else:
        loop_log.debug(f"Running initial update...")
    if BOT.is_ws_ratelimited():
        log.error("Rate limited.")
    # print(f'update game running.. {PLAYER}, {SEND_INFO}')
    if SEND_INFO:
        if len(SEND_INFO.split("%!%")) > 1:
            await CHANNEL.send(file=discord.File(SEND_INFO.split("%!%")[-1]))
            log.debug("Sent a file.")
            LAST_SEND_AT = time.time()
            SEND_INFO = None
        else:
            headers = {"authorization": f"Bot {TOKEN}"}
            payload = {"content": {SEND_INFO}}
            d = requests.post(f'https://discord.com/api/v9/channels/{CHANNEL.id}/messages',
                              headers=headers, data=payload, timeout=3)
            loop_log.debug(f"Sent update info. Status: {d.status_code}")
            # d = await CHANNEL.send(SEND_INFO)
            LAST_SEND_AT = time.time()
            # print(f"SENT INFO, {PLAYER}, {d}")
            SEND_INFO = None
    else:
        loop_log.debug(f"No send info provided.")


@tasks.loop(seconds=1)
async def api_listener():
    """
    Listens for any new commands in the execution queue.
    Upon finding new commands it executes them and removes them from the queue.
    """
    # print(f"API LISTENER WORKING...{PLAYER}")
    global LOOP_LOGGING
    if LOOP_LOGGING and loop_log.level != logging.DEBUG:
        loop_log.setLevel(logging.DEBUG)
        log.debug("Loop logging enabled.")
    elif not LOOP_LOGGING and loop_log.level != logging.INFO:
        loop_log.setLevel(logging.INFO)
        log.debug("Loop logging disabled.")
    loop_log.debug("Listening...")
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
                log.error(f"Function does not exist.")
                log.error(f"Error: {e}")


async def start_bot():
    """
    Starts the discord bot.
    """
    await BOT.start(TOKEN)
