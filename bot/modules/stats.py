# https://github.com/Appeza/tg-mirror-leech-bot edited by HuzunluArtemis

from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time, Process as psprocess
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from datetime import datetime
from time import time
from subprocess import run as srun, check_output
import requests
from bot import LOGGER, dispatcher, botStartTime, HEROKU_API_KEY, HEROKU_APP_NAME
from telegram.ext import CommandHandler
from telegram import ParseMode, InlineKeyboardMarkup
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage, sendMarkup, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.modules.wayback import getRandomUserAgent

now = datetime.now(pytz.timezone(f'{TIMEZONE}'))

IMAGE_X = "https://telegra.ph/file/28d6c50c499936aed0651.png"

def getHerokuDetails(h_api_key, h_app_name):
    try: import heroku3
    except ModuleNotFoundError: run("pip install heroku3", capture_output=False, shell=True)
    try: import heroku3
    except Exception as f:
        LOGGER.warning("heroku3 cannot imported. add to your deployer requirements.txt file.")
        LOGGER.warning(f)
        return None
    if (not h_api_key) or (not h_app_name): return None
    try:
        heroku_api = "https://api.heroku.com"
        Heroku = heroku3.from_key(h_api_key)
        app = Heroku.app(h_app_name)
        useragent = getRandomUserAgent()
        user_id = Heroku.account().id
        headers = {
            "User-Agent": useragent,
            "Authorization": f"Bearer {h_api_key}",
            "Accept": "application/vnd.heroku+json; version=3.account-quotas",
        }
        path = f"/accounts/{user_id}/actions/get-quota"
        session = requests.Session()
        result = (session.get(heroku_api + path, headers=headers)).json()
        abc = ""
        account_quota = result["account_quota"]
        quota_used = result["quota_used"]
        quota_remain = account_quota - quota_used
        abc += f"Full: {get_readable_time(account_quota)} | "
        abc += f"Used: {get_readable_time(quota_used)} | "
        abc += f"Free: {get_readable_time(quota_remain)}\n"
        # App Quota
        AppQuotaUsed = 0
        OtherAppsUsage = 0
        for apps in result["apps"]:
            if str(apps.get("app_uuid")) == str(app.id):
                try:
                    AppQuotaUsed = apps.get("quota_used")
                except Exception as t:
                    LOGGER.error("error when adding main dyno")
                    LOGGER.error(t)
            else:
                try:
                    OtherAppsUsage += int(apps.get("quota_used"))
                except Exception as t:
                    LOGGER.error("error when adding other dyno")
                    LOGGER.error(t)
        LOGGER.info(f"This App: {str(app.name)}")
        abc += f"App Usage: {get_readable_time(AppQuotaUsed)}"
        abc += f" | Other Apps: {get_readable_time(OtherAppsUsage)}"
        return abc
    except Exception as g:
        LOGGER.error(g)
        return None

def stats(update, context):
    if ospath.exists('.git'):
        last_commit = check_output(["git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'"], shell=True).decode()
        botVersion = check_output(["git log -1 --date=format:v%y.%m%d.%H%M --pretty=format:%cd"], shell=True).decode()
    else:
        last_commit = 'No UPSTREAM_REPO'
        botVersion = 'v1'
    currentTime = get_readable_time(time() - botStartTime)
    osUptime = get_readable_time(time() - boot_time())
    total, used, free, disk= disk_usage('/')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(net_io_counters().bytes_sent)
    recv = get_readable_file_size(net_io_counters().bytes_recv)
    cpuUsage = cpu_percent(interval=0.5)
    p_core = cpu_count(logical=False)
    t_core = cpu_count(logical=True)
    swap = swap_memory()
    swap_p = swap.percent
    swap_t = get_readable_file_size(swap.total)
    memory = virtual_memory()
    mem_p = memory.percent
    mem_t = get_readable_file_size(memory.total)
    mem_a = get_readable_file_size(memory.available)
    mem_u = get_readable_file_size(memory.used)
    stats = f'╭───《🌐 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦 🌐》\n│\n'\
            f'├─🔢 𝗖𝗼𝗺𝗺𝗶𝘁 𝗗𝗮𝘁𝗲 ⇢ {last_commit} \n'\
            f'├─🔢 𝗩𝗲𝗿𝘀𝗶𝗼𝗻 ⇢ {botVersion}\n'\
            f'├─🤖 𝗕𝗼𝘁 𝗨𝗽𝘁𝗶𝗺𝗲 ⇢ {currentTime}\n│\n'\
            f'├─✨ 𝗢𝗦 𝗨𝗽𝘁𝗶𝗺𝗲⇢ {osUptime}\n' \
            f'├─💽 𝗧𝗼𝘁𝗮𝗹 𝗗𝗶𝘀𝗸 𝗦𝗽𝗮𝗰𝗲 ⇢ {total}\n'\
            f'├─💻 𝗨𝘀𝗲𝗱 ⇢ {used} | 💾 𝗙𝗿𝗲𝗲 ⇢ {free}\n│\n'\
            f'├─📤 𝗨𝗽𝗹𝗼𝗮𝗱 ⇢ {sent}\n'\
            f'├─📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 ⇢ {recv}\n│\n'\
            f'├─🖥️ 𝗖𝗣𝗨 ⇢ {cpuUsage}%\n'\
            f'├─📏 𝗥𝗔𝗠 ⇢ {mem_p}%\n'\
            f'├─💿 𝗗𝗜𝗦𝗞 ⇢ {disk}%\n'\
            f'├─🛰️ 𝗣𝗵𝘆𝘀𝗶𝗰𝗮𝗹 𝗖𝗼𝗿𝗲𝘀 ⇢ {p_core}\n'\
            f'├─⚙️ 𝗧𝗼𝘁𝗮𝗹 𝗖𝗼𝗿𝗲𝘀 ⇢ {t_core}\n'\
            f'├─⚡ 𝗦𝗪𝗔𝗣 ⇢ {swap_t} | 𝗨𝘀𝗲𝗱 ⇢ {swap_p}%\n│\n'\
            f'├─💽 𝗠𝗲𝗺𝗼𝗿𝘆 𝗧𝗼𝘁𝗮𝗹 ⇢ {mem_t}\n'\
            f'├─💾 𝗠𝗲𝗺𝗼𝗿𝘆 𝗙𝗿𝗲𝗲 ⇢ {mem_a}\n'\
            f'├─💻 𝗠𝗲𝗺𝗼𝗿𝘆 𝗨𝘀𝗲𝗱 ⇢ {mem_u}\n│\n'\
            f'╰───《☣️ <b>@PriiiiyoS_Mirror</b> ☣️》\n'
    update.effective_message.reply_photo(IMAGE_X, stats, parse_mode=ParseMode.HTML)

stats_handler = CommandHandler(BotCommands.StatsCommand, stats,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(stats_handler)
