from bot import AUTHORIZED_CHATS, LEECH_LOG, LEECH_LOG_ALT, MOD_USERS, SUDO_USERS, dispatcher, DB_URI
from bot.helper.telegram_helper.message_utils import sendMessage
from telegram.ext import CommandHandler
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger


def authorize(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in AUTHORIZED_CHATS:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐔𝐬𝐞𝐫 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐀𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😲'
        elif DB_URI is not None:
            msg = DbManger().user_auth(user_id)
            AUTHORIZED_CHATS.add(user_id)
        else:
            AUTHORIZED_CHATS.add(user_id)
            msg = '𝐔𝐬𝐞𝐫 𝐀𝐮𝐭𝐡𝐫𝐨𝐫𝐢𝐳𝐞𝐝 ✅'
    elif reply_message:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐔𝐬𝐞𝐫 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐀𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😲'
        elif DB_URI is not None:
            msg = DbManger().user_auth(user_id)
            AUTHORIZED_CHATS.add(user_id)
        else:
            AUTHORIZED_CHATS.add(user_id)
            msg = '𝐔𝐬𝐞𝐫 𝐀𝐮𝐭𝐡𝐫𝐨𝐫𝐢𝐳𝐞𝐝 ✅'
    else:
        # Trying to authorize a chat
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHATS:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐂𝐡𝐚𝐭 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐀𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😲'
        elif DB_URI is not None:
            msg = DbManger().user_auth(chat_id)
            AUTHORIZED_CHATS.add(chat_id)
        else:
            AUTHORIZED_CHATS.add(chat_id)
            msg = '𝐂𝐡𝐚𝐭 𝐀𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 ✅'
    sendMessage(msg, context.bot, update.message)

def unauthorize(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(user_id)
            else:
                msg = '𝐔𝐬𝐞𝐫 𝐔𝐧𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😁'
            AUTHORIZED_CHATS.remove(user_id)
        else:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐔𝐬𝐞𝐫 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐔𝐧𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😲'
    elif reply_message:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(user_id)
            else:
                msg = '𝐔𝐬𝐞𝐫 𝐔𝐧𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😁'
            AUTHORIZED_CHATS.remove(user_id)
        else:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐔𝐬𝐞𝐫 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐔𝐧𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😲'
    else:
        # Trying to unauthorize a chat
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(chat_id)
            else:
                msg = '𝐂𝐡𝐚𝐭 𝐔𝐧𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😁'
            AUTHORIZED_CHATS.remove(chat_id)
        else:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐂𝐡𝐚𝐭 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐔𝐧𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 😲'

    sendMessage(msg, context.bot, update.message)

def addSudo(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in SUDO_USERS:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐔𝐬𝐞𝐫 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝗦𝘂𝗱𝗼 😲'
        elif DB_URI is not None:
            msg = DbManger().user_addsudo(user_id)
            SUDO_USERS.add(user_id)
        else:
            SUDO_USERS.add(user_id)
            msg = '𝗣𝗿𝗼𝗺𝗼𝘁𝗲𝗱 𝗮𝘀 𝗦𝘂𝗱𝗼 ✅'
    elif reply_message:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            msg = '𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐔𝐬𝐞𝐫 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝗦𝘂𝗱𝗼 😲'
        elif DB_URI is not None:
            msg = DbManger().user_addsudo(user_id)
            SUDO_USERS.add(user_id)
        else:
            SUDO_USERS.add(user_id)
            msg = '𝗣𝗿𝗼𝗺𝗼𝘁𝗲𝗱 𝗮𝘀 𝗦𝘂𝗱𝗼 ✅'
    else:
        msg = "𝐆𝐢𝐯𝐞 𝐈𝐃 𝐨𝐫 𝐑𝐞𝐩𝐥𝐲 𝐓𝐨 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐨𝐟 𝐰𝐡𝐨𝐦 𝐲𝐨𝐮 𝐰𝐚𝐧𝐭 𝐭𝐨 𝐏𝐫𝐨𝐦𝐨𝐭𝐞 😲😲"
    sendMessage(msg, context.bot, update.message)

def removeSudo(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in SUDO_USERS:
            if DB_URI is not None:
                msg = DbManger().user_rmsudo(user_id)
            else:
                msg = '𝗨𝘀𝗲𝗿 𝗗𝗲𝗺𝗼𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 😁'
            SUDO_USERS.remove(user_id)
        else:
            msg = '𝗡𝗼𝘁 𝘀𝘂𝗱𝗼 𝘂𝘀𝗲𝗿 𝘁𝗼 𝗱𝗲𝗺𝗼𝘁𝗲! 😲'
    elif reply_message:
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            if DB_URI is not None:
                msg = DbManger().user_rmsudo(user_id)
            else:
                msg = '𝗨𝘀𝗲𝗿 𝗗𝗲𝗺𝗼𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 😁'
            SUDO_USERS.remove(user_id)
        else:
            msg = '𝗡𝗼𝘁 𝘀𝘂𝗱𝗼 𝘂𝘀𝗲𝗿 𝘁𝗼 𝗱𝗲𝗺𝗼𝘁𝗲! 😲'
    else:
        msg = "𝗚𝗶𝘃𝗲 𝗜𝗗 𝗼𝗿 𝗥𝗲𝗽𝗹𝘆 𝗧𝗼 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗼𝗳 𝘄𝗵𝗼𝗺 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁 𝘁𝗼 𝗿𝗲𝗺𝗼𝘃𝗲 𝗳𝗿𝗼𝗺 𝗦𝘂𝗱𝗼 😲😲"
    sendMessage(msg, context.bot, update.message)

def addMod(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in MOD_USERS:
            msg = "Already Moderator!"
        elif DB_URI is not None:
            msg = DbManger().user_addmod(user_id)
            MOD_USERS.add(user_id)
        else:
            MOD_USERS.add(user_id)
            with open("mod_users.txt", "a") as file:
                file.write(f"{user_id}\n")
                msg = "Promoted as Moderator"
    elif reply_message is None:
        msg = "Give ID or Reply To message of whom you want to Promote."
    else:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in MOD_USERS:
            msg = "Already Moderator!"
        elif DB_URI is not None:
            msg = DbManger().user_addmod(user_id)
            MOD_USERS.add(user_id)
        else:
            MOD_USERS.add(user_id)
            with open("mod_users.txt", "a") as file:
                file.write(f"{user_id}\n")
                msg = "Promoted as Moderator"
    sendMessage(msg, context.bot, update.message)

def removeMod(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in MOD_USERS:
            msg = DbManger().user_rmmod(user_id) if DB_URI is not None else "Demoted"
            MOD_USERS.remove(user_id)
        else:
            msg = "Not Moderator to demote!"
    elif reply_message is None:
        msg = "Give ID or Reply To message of whom you want to remove from Moderator"
    else:
        user_id = reply_message.from_user.id
        if user_id in MOD_USERS:
            msg = DbManger().user_rmmod(user_id) if DB_URI is not None else "Demoted"
            MOD_USERS.remove(user_id)
        else:
            msg = "Not Moderator to demote!"
    if DB_URI is None:
        with open("mod_users.txt", "a") as file:
            file.truncate(0)
            for i in MOD_USERS:
                file.write(f"{i}\n")
    sendMessage(msg, context.bot, update.message)

def addleechlog(update, context):
    # Trying to add a user in leech logs
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LEECH_LOG:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗨𝘀𝗲𝗿 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝗔𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 😲"
        elif DB_URI is not None:
            msg = DbManger().addleech_log(user_id)
            LEECH_LOG.add(user_id)
        else:
            LEECH_LOG.add(user_id)
            with open("leech.txt", "a") as file:
                file.write(f"{user_id}\n")
                msg = "𝗨𝘀𝗲𝗿 𝐀𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 ✅"
    elif reply_message is None:
        # Trying to add a chat in leech logs
        chat_id = update.effective_chat.id
        if chat_id in LEECH_LOG:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗖𝗵𝗮𝘁 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝐀𝐝𝐝𝐞𝐝 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 😲"
        elif DB_URI is not None:
            msg = DbManger().addleech_log(chat_id)
            LEECH_LOG.add(chat_id)
        else:
            LEECH_LOG.add(chat_id)
            with open("leech.txt", "a") as file:
                file.write(f"{chat_id}\n")
                msg = "𝗖𝗵𝗮𝘁 𝗔𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 ✅"
    else:
        # Trying to add someone by replying
        user_id = reply_message.from_user.id
        if user_id in LEECH_LOG:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗨𝘀𝗲𝗿 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝐄𝐱𝗶𝘀𝘁 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 😲"
        elif DB_URI is not None:
            msg = DbManger().addleech_log(user_id)
            LEECH_LOG.add(user_id)
        else:
            LEECH_LOG.add(user_id)
            with open("leech.txt", "a") as file:
                file.write(f"{user_id}\n")
                msg = "𝗨𝘀𝗲𝗿 𝗔𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 ✅"
    sendMessage(msg, context.bot, update.message)

def rmleechlog(update, context):
    # Trying to remove a user from leech log
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LEECH_LOG:
            if DB_URI is not None:
                msg = DbManger().rmleech_log(user_id)
            else:
                msg = "𝗨𝘀𝗲𝗿 𝐑𝗲𝗺𝗼𝘃𝗲𝗱 𝐅𝗿𝗼𝗺 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😁"
            LEECH_LOG.remove(user_id)
        else:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗨𝘀𝗲𝗿 𝐃𝗼𝗲𝘀 𝐍𝗼𝘁 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
    elif reply_message is None:
        # Trying to remove a chat from leech log
        chat_id = update.effective_chat.id
        if chat_id in LEECH_LOG:
            if DB_URI is not None:
                msg = DbManger().rmleech_log(chat_id)
            else:
                msg = "𝐂𝐡𝐚𝐭 𝐑𝗲𝗺𝗼𝘃𝗲𝗱 𝐅𝗿𝗼𝗺 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😁"
            LEECH_LOG.remove(chat_id)
        else:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐂𝐡𝐚𝐭 𝐃𝗼𝗲𝘀 𝐍𝗼𝘁 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
    else:
        # Trying to remove someone by replying
        user_id = reply_message.from_user.id
        if user_id in LEECH_LOG:
            if DB_URI is not None:
                msg = DbManger().rmleech_log(user_id)
            else:
                msg = "𝗨𝘀𝗲𝗿 𝐑𝗲𝗺𝗼𝘃𝗲𝗱 𝐅𝗿𝗼𝗺 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😁"
            LEECH_LOG.remove(user_id)
        else:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗨𝘀𝗲𝗿 𝐃𝗼𝗲𝘀 𝐍𝗼𝘁 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
    if DB_URI is None:
        with open("leech.txt", "a") as file:
            file.truncate(0)
            for i in LEECH_LOG:
                file.write(f"{i}\n")
    sendMessage(msg, context.bot, update.message)


def addleechlog_alt(update, context):
    # Trying to add a user in leech logs
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LEECH_LOG_ALT:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗨𝘀𝗲𝗿 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝗔𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 😲"
        elif DB_URI is not None:
            msg = DbManger().addleech_log_alt(user_id)
            LEECH_LOG_ALT.add(user_id)
        else:
            LEECH_LOG_ALT.add(user_id)
            with open("leech_logs.txt", "a") as file:
                file.write(f"{user_id}\n")
                msg = "𝗨𝘀𝗲𝗿 𝐀𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 ✅"
    elif reply_message is None:
        # Trying to add a chat in leech logs
        chat_id = update.effective_chat.id
        if chat_id in LEECH_LOG_ALT:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗖𝗵𝗮𝘁 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
        elif DB_URI is not None:
            msg = DbManger().addleech_log_alt(chat_id)
            LEECH_LOG_ALT.add(chat_id)
        else:
            LEECH_LOG_ALT.add(chat_id)
            with open("leech_logs.txt", "a") as file:
                file.write(f"{chat_id}\n")
                msg = "𝗖𝗵𝗮𝘁 𝗔𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 ✅"
    else:
        # Trying to add someone by replying
        user_id = reply_message.from_user.id
        if user_id in LEECH_LOG_ALT:
            msg = "𝗨𝘀𝗲𝗿 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
        elif DB_URI is not None:
            msg = DbManger().addleech_log_alt(user_id)
            LEECH_LOG_ALT.add(user_id)
        else:
            LEECH_LOG_ALT.add(user_id)
            with open("leech_logs.txt", "a") as file:
                file.write(f"{user_id}\n")
                msg = "𝗨𝘀𝗲𝗿 𝗔𝗱𝗱𝗲𝗱 𝐈𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀 ✅"
    sendMessage(msg, context.bot, update.message)

def rmleechlog_alt(update, context):
    # Trying to remove a user from leech log
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LEECH_LOG_ALT:
            if DB_URI is not None:
                msg = DbManger().rmleech_log_alt(user_id)
            else:
                msg = "𝗨𝘀𝗲𝗿 𝐑𝐞𝗺𝗼𝘃𝗲𝗱 𝐅𝗿𝗼𝗺 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😁"
            LEECH_LOG_ALT.remove(user_id)
        else:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗨𝘀𝗲𝗿 𝐃𝗼𝗲𝘀 𝐍𝗼𝘁 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
    elif reply_message is None:
        # Trying to remove a chat from leech log
        chat_id = update.effective_chat.id
        if chat_id in LEECH_LOG_ALT:
            if DB_URI is not None:
                msg = DbManger().rmleech_log_alt(chat_id)
            else:
                msg = "𝗖𝗵𝗮𝘁 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝗳𝗿𝗼𝗺 𝗹𝗲𝗲𝗰𝗵 𝗹𝗼𝗴𝘀 😁"
            LEECH_LOG_ALT.remove(chat_id)
        else:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝗖𝗵𝗮𝘁 𝐃𝗼𝗲𝘀 𝐍𝗼𝘁 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
    else:
        # Trying to remove someone by replying
        user_id = reply_message.from_user.id
        if user_id in LEECH_LOG_ALT:
            if DB_URI is not None:
                msg = DbManger().rmleech_log_alt(user_id)
            else:
                msg = "𝗨𝘀𝗲𝗿 𝐑𝗲𝗺𝗼𝘃𝗲𝗱 𝐅𝗿𝗼𝗺 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😁"
            LEECH_LOG_ALT.remove(user_id)
        else:
            msg = "𝐍𝐨 𝐍𝐞𝐞𝐝!! 𝐔𝐬𝐞𝐫 𝐃𝗼𝗲𝘀 𝐍𝗼𝘁 𝐄𝘅𝗶𝘀𝘁 𝐈𝗻 𝐋𝗲𝗲𝗰𝗵 𝐋𝗼𝗴𝘀 😲"
    if DB_URI is None:
        with open("leech_logs.txt", "a") as file:
            file.truncate(0)
            for i in LEECH_LOG_ALT:
                file.write(f"{i}\n")
    sendMessage(msg, context.bot, update.message)

def sendAuthChats(update, context):
    user = sudo = ''
    user += '\n'.join(f"<code>{uid}</code>" for uid in AUTHORIZED_CHATS)
    sudo += '\n'.join(f"<code>{uid}</code>" for uid in SUDO_USERS)
    sudo += '\n'.join(f"<code>{uid}</code>" for uid in MOD_USERS)
    leechlog += "\n".join(f"<code>{uid}</code>" for uid in LEECH_LOG)
    leechlog_alt += "\n".join(f"<code>{uid}</code>" for uid in LEECH_LOG_ALT)
    sendMessage(f'<b><u>𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗖𝗵𝗮𝘁𝘀:</u></b>{user}\n<b><u>𝗦𝘂𝗱𝗼 𝗨𝘀𝗲𝗿𝘀:</u></b>\n{sudo}\n<b><u>𝗠𝗮𝗶𝗻 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴:</u></b>\n{leechlog}\n<b><u>𝗔𝗹𝘁 𝗟𝗲𝗲𝗰𝗵 𝗟𝗼𝗴𝘀:</u></b>\n{leechlog_alt}', context.bot, update.message)
    sendMessage(f'<b><u>𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗖𝗵𝗮𝘁𝘀:</u></b>{user}\n<b><u>𝗦𝘂𝗱𝗼 𝗨𝘀𝗲𝗿𝘀:</u></b>\n{sudo}', context.bot, update.message)


addleechlog_handler = CommandHandler(command=BotCommands.AddLeechLogCommand, callback=addleechlog,
                       filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
rmleechlog_handler = CommandHandler(command=BotCommands.RmLeechLogCommand, callback=rmleechlog,
                      filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
addleechlog_alt_handler = CommandHandler(command=BotCommands.AddLeechLogAltCommand, callback=addleechlog_alt,
                           filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
rmleechlog_alt_handler = CommandHandler(command=BotCommands.RmLeechLogAltCommand, callback=rmleechlog_alt,
                          filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
send_auth_handler = CommandHandler(command=BotCommands.AuthorizedUsersCommand, callback=sendAuthChats,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
authorize_handler = CommandHandler(command=BotCommands.AuthorizeCommand, callback=authorize,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
unauthorize_handler = CommandHandler(command=BotCommands.UnAuthorizeCommand, callback=unauthorize,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
addsudo_handler = CommandHandler(command=BotCommands.AddSudoCommand, callback=addSudo,
                                    filters=CustomFilters.owner_filter, run_async=True)
removesudo_handler = CommandHandler(command=BotCommands.RmSudoCommand, callback=removeSudo,
                                    filters=CustomFilters.owner_filter, run_async=True)
addmod_handler = CommandHandler(command=BotCommands.AddModCommand, callback=addMod,
                                    filters=CustomFilters.owner_filter, run_async=True)
removemod_handler = CommandHandler(command=BotCommands.RmModCommand, callback=removeMod,
                                    filters=CustomFilters.owner_filter, run_async=True)

dispatcher.add_handler(addleechlog_handler)
dispatcher.add_handler(rmleechlog_handler)
dispatcher.add_handler(addleechlog_alt_handler)
dispatcher.add_handler(rmleechlog_alt_handler)
dispatcher.add_handler(send_auth_handler)
dispatcher.add_handler(authorize_handler)
dispatcher.add_handler(unauthorize_handler)
dispatcher.add_handler(addsudo_handler)
dispatcher.add_handler(removesudo_handler)
dispatcher.add_handler(addmod_handler)
dispatcher.add_handler(removemod_handler)
