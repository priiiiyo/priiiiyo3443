from random import SystemRandom
from string import ascii_letters, digits
from telegram.ext import CommandHandler
from telegram import InlineKeyboardMarkup,  
from threading import Thread
from time import sleep

from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import auto_delete_message, auto_delete_upload_message, sendMessage, sendMarkup, deleteMessage, delete_all_messages, update_all_messages, sendStatusMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.status_utils.clone_status import CloneStatus
from bot import dispatcher, LOGGER, STOP_DUPLICATE, AUTO_DELETE_UPLOAD_MESSAGE_DURATION, BOT_PM, CLONE_LIMIT, CHANNEL_USERNAME, MIRROR_LOGS, \
     download_dict, download_dict_lock, LINK_LOGS, FSUB, FSUB_CHANNEL_ID, Interval
from bot.helper.ext_utils.bot_utils import is_appdrive_link, is_gdrive_link, get_readable_file_size, new_thread


def _clone(message, bot, multi=0):
    if AUTO_DELETE_UPLOAD_MESSAGE_DURATION != -1:
        reply_to = message.reply_to_message
        if reply_to is not None:
            try:
                reply_to.delete()
            except Exception as error:
                LOGGER.warning(error)
    uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
    if FSUB:
        try:
            user = bot.get_chat_member(f"{FSUB_CHANNEL_ID}", message.from_user.id)
            LOGGER.info(user.status)
            if user.status not in ("member", "creator", "administrator", "supergroup"):
                buttons = ButtonMaker()
                chat_u = CHANNEL_USERNAME.replace("@", "")
                buttons.buildbutton("👉🏻 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗜𝗡𝗞 👈🏻", f"https://t.me/{chat_u}")
                help_msg = f"𝗗𝗘𝗔𝗥 {uname},\n𝗬𝗢𝗨 𝗡𝗘𝗘𝗗 𝗧𝗢 𝗝𝗢𝗜𝗡 𝗠𝗬 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗧𝗢 𝗨𝗦𝗘 𝗕𝗢𝗧. \n\n𝗖𝗟𝗜𝗖𝗞 𝗢𝗡 𝗧𝗛𝗘 𝗕𝗘𝗟𝗢𝗪 𝗕𝗨𝗧𝗧𝗢𝗡 𝗧𝗢 𝗝𝗢𝗜𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟"
                msg = sendMarkup(help_msg, bot, message, InlineKeyboardMarkup(buttons.build_menu(2)))
                Thread(target=auto_delete_upload_message, args=(bot, message, msg)).start()
                return
        except Exception:
            pass
    if BOT_PM and message.chat.type != "private":
        try:
            msg1 = f"𝗔𝗱𝗱𝗲𝗱 𝘆𝗼𝘂𝗿 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗹𝗶𝗻𝗸 𝘁𝗼 𝗰𝗹𝗼𝗻𝗲\n"
            send = bot.sendMessage(message.from_user.id,text=msg1)
            send.delete()
        except Exception as e:
            LOGGER.warning(e)
            buttons = ButtonMaker()
            buttons.buildbutton('👉🏻 𝗦𝗧𝗔𝗥𝗧 𝗕𝗢𝗧 👈🏻', f'https://t.me/{bot.get_me().username}?start=start')
            help_msg = f'𝗗𝗘𝗔𝗥 {uname},\n𝗬𝗢𝗨 𝗡𝗘𝗘𝗗 𝗧𝗢 𝗦𝗧𝗔𝗥𝗧 𝗧𝗛𝗘 𝗕𝗢𝗧 𝗨𝗦𝗜𝗡𝗚 𝗧𝗢 𝗕𝗘𝗟𝗢𝗪 𝗕𝗨𝗧𝗧𝗢𝗡. \n\n𝗜𝗧𝗦 𝗡𝗘𝗘𝗗𝗘𝗗 𝗦𝗢 𝗕𝗢𝗧 𝗖𝗔𝗡 𝗦𝗘𝗡𝗗 𝗬𝗢𝗨𝗥 𝗠𝗜𝗥𝗥𝗢𝗥/𝗖𝗟𝗢𝗡𝗘/𝗟𝗘𝗘𝗖𝗛𝗘𝗗 𝗙𝗜𝗟𝗘𝗦 𝗜𝗡 𝗣𝗠. \n\n𝗖𝗟𝗜𝗖𝗞 𝗢𝗡 𝗧𝗛𝗘 𝗕𝗘𝗟𝗢𝗪 𝗕𝗨𝗧𝗧𝗢𝗡 𝗧𝗢 𝗦𝗧𝗔𝗥𝗧 𝗧𝗛𝗘 𝗕𝗢𝗧'
            reply_message = sendMarkup(help_msg, bot, message, InlineKeyboardMarkup(buttons.build_menu(2)))
            Thread(target=auto_delete_message, args=(bot, message, reply_message)).start()
            return
    args = message.text.split()
    reply_to = message.reply_to_message
    link = ''
    if len(args) > 1:
        link = args[1].strip()
        if link.strip().isdigit():
            multi = int(link)
            link = ''
        elif message.from_user.username:
            tag = f"@{message.from_user.username}"
        else:
            tag = message.from_user.mention_html(message.from_user.first_name)
    if reply_to:
        if len(link) == 0:
            link = reply_to.text.split(maxsplit=1)[0].strip()
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    if LINK_LOGS:
        if link != "":
            uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
            slmsg = f'╭─🪧 𝗔𝗱𝗱𝗲𝗱 𝗯𝘆 ⇢ {uname}'
            slmsg += f'\n╰─🪪 𝗨𝘀𝗲𝗿 𝗜𝗗 ⇢ <code>{message.from_user.id}</code>\n\n'
            try:
                source_link = link
                for link_log in LINK_LOGS:
                    bot.sendMessage(link_log, text=slmsg + source_link, parse_mode=ParseMode.HTML)
            except IndexError:
                pass
            if reply_to is not None:
                try:
                    reply_text = reply_to.text
                    if is_url(reply_text):
                        source_link = reply_text.strip()
                        for link_log in LINK_LOGS:
                            bot.sendMessage(chat_id=link_log, text=slmsg + source_link, parse_mode=ParseMode.HTML)
                except TypeError:
                    pass
    is_appdrive = is_appdrive_link(link)
    if is_appdrive:
        try:
            msg = sendMessage(f"𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗜𝗡𝗚 𝗔𝗣𝗣𝗗𝗥𝗜𝗩𝗘 𝗟𝗜𝗡𝗞 ⇝ \n<code>{link}</code>", bot, message)
            link = appdrive(link)
            deleteMessage(bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(bot, msg)
            return sendMessage(str(e), bot, message)
    is_gdtot = is_gdtot_link(link)
    if is_gdtot:
        try:
            msg = sendMessage(f"𝐁𝐘𝐏𝐀𝐒𝐒𝐈𝐍𝐆 𝐆𝐃𝐓𝐎𝐓 𝐋𝐈𝐍𝐊 ⇝ <code>{link}</code>", bot, message)
            link = gdtot(link)
            deleteMessage(bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(bot, msg)
            return sendMessage(str(e), bot, message)

    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
        if res != "":
            return sendMessage(res, bot, message)
        if STOP_DUPLICATE:
            LOGGER.info('Checking File/Folder if already in Drive...')
            smsg, button = gd.drive_list(name, True, True)
            if smsg:
                msg3 = "📂 𝐅𝐢𝐥𝐞/𝐅𝐨𝐥𝐝𝐞𝐫 𝐢𝐬 𝐚𝐥𝐫𝐞𝐚𝐝𝐲 𝐚𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐢𝐧 𝐃𝐫𝐢𝐯𝐞.\n 𝐇𝐞𝐫𝐞 𝐚𝐫𝐞 𝐭𝐡𝐞 𝐬𝐞𝐚𝐫𝐜𝐡 𝐫𝐞𝐬𝐮𝐥𝐭𝐬 ↴:"
                return sendMarkup(msg3, bot, message, button)
        if CLONE_LIMIT is not None:
            LOGGER.info("Checking File/Folder Size...")
            if size > CLONE_LIMIT * 1024**3:
                msg2 = f"𝐅𝐚𝐢𝐥𝐞𝐝, 𝐂𝐥𝐨𝐧𝐞 𝐥𝐢𝐦𝐢𝐭 𝐢𝐬 {CLONE_LIMIT}GB.\nYour File/Folder size is {get_readable_file_size(size)}."
                return sendMessage(msg2, bot, message)
        if multi > 1:
            sleep(4)
            nextmsg = type('nextmsg', (object, ), {'chat_id': message.chat_id, 'message_id': message.reply_to_message.message_id + 1})
            nextmsg = sendMessage(args[0], bot, nextmsg)
            nextmsg.from_user.id = message.from_user.id
            multi -= 1
            sleep(4)
            Thread(target=_clone, args=(nextmsg, bot, multi)).start()
        if files <= 20:
            msg = sendMessage(f"Cloning: <code>{link}</code>", bot, message)
            result, button = gd.clone(link)
            deleteMessage(bot, msg)
        else:
            drive = GoogleDriveHelper(name)
            gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=12))
            clone_status = CloneStatus(drive, size, message, gid)
            with download_dict_lock:
                download_dict[message.message_id] = clone_status
            sendStatusMessage(message, bot)
            result, button = drive.clone(link)
            with download_dict_lock:
                del download_dict[message.message_id]
                count = len(download_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
                    delete_all_messages()
                else:
                    update_all_messages()
            except IndexError:
                pass
        cc = f'\n╰─📬 𝐁𝐲 ⇢ {tag}\n\n'
        if button in ["cancelled", ""]:
            sendMessage(f"{tag} {result}", bot, message)
        else:
            if AUTO_DELETE_UPLOAD_MESSAGE_DURATION != -1:
                auto_delete_message = int(AUTO_DELETE_UPLOAD_MESSAGE_DURATION / 60)
                if message.chat.type == "private":
                    warnmsg = ""
                else:
                    autodel = secondsToText()
                    warnmsg = f" \n 𝗧𝗵𝗶𝘀 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝘄𝗶𝗹𝗹 𝗮𝘂𝘁𝗼 𝗱𝗲𝗹𝗲𝘁𝗲𝗱 𝗶𝗻 {autodel}\n\n"
        if BOT_PM and message.chat.type != "private":
            pmwarn = f"𝗜 𝗵𝗮𝘃𝗲 𝘀𝗲𝗻𝘁 𝗹𝗶𝗻𝗸𝘀 𝗶𝗻 𝗣𝗠.\n"
        elif message.chat.type == "private":
            pmwarn = ""
        else:
            pmwarn = ""
        uploadmsg = sendMarkup(result + cc + pmwarn + warnmsg, bot, message, button)
        Thread(target=auto_delete_upload_message, args=(bot, message, uploadmsg).start()
        if MIRROR_LOGS:
            try:
                for i in MIRROR_LOGS:
                    bot.sendMessage(chat_id=i, text=result + cc, reply_markup=button, parse_mode=ParseMode.HTML)
                except Exception as e:
                LOGGER.warning(e)
            if BOT_PM and message.chat.type != "private":
                try:
                    LOGGER.info(message.chat.type)
                    bot.sendMessage(message.from_user.id, text=result + cc, reply_markup=button, parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.warning(e)
                    return
            sendMarkup(result + cc, bot, message, button)
            LOGGER.info(f'Cloning Done: {name}')
    else:
        sendMessage('Send Gdrive or gdtot link along with command or by replying to the link by command', bot, message)

@new_thread
def cloneNode(update, context):
    _clone(update.message, context.bot)

clone_handler = CommandHandler(BotCommands.CloneCommand, cloneNode, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(clone_handler)
