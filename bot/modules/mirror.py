from base64 import b64encode
from requests import utils as rutils, get as rget
from re import match as re_match, search as re_search, split as re_split
from time import sleep, time
from pytz import timezone
from os import path as ospath, remove as osremove, listdir, walk
from shutil import rmtree
from threading import Thread
from subprocess import run as srun
from pathlib import PurePath
from html import escape
from telegram.ext import CommandHandler
from telegram import InlineKeyboardMarkup

from bot import Interval, INDEX_URL, VIEW_LINK, aria2, QB_SEED, dispatcher, DOWNLOAD_DIR, BOT_PM, MIRROR_LOGS, LINK_LOGS, SOURCE_LINK, INDEX_BUTTON, VIEW_BUTTON, TIMEZONE, AUTO_DELETE_UPLOAD_MESSAGE_DURATION, \
                download_dict, download_dict_lock, TG_SPLIT_SIZE, LOGGER, DB_URI, CHANNEL_USERNAME, LEECH_LOG, LEECH_LOG_ALT, LEECH_ENABLED, INCOMPLETE_TASK_NOTIFIER
from bot.helper.ext_utils.bot_utils import is_url, is_magnet, is_mega_link, is_gdrive_link, is_appdrive_link, is_gdtot_link, get_content_type
from bot.helper.ext_utils.fs_utils import get_base_name, get_path_size, split_file, clean_download
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException, NotSupportedExtractionArchive
from bot.helper.mirror_utils.download_utils.aria2_download import add_aria2c_download
from bot.helper.mirror_utils.download_utils.gd_downloader import add_gd_download
from bot.helper.mirror_utils.download_utils.qbit_downloader import QbDownloader
from bot.helper.mirror_utils.download_utils.mega_downloader import add_mega_download
from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator, appdrive, gdtot
from bot.helper.mirror_utils.download_utils.telegram_downloader import TelegramDownloadHelper
from bot.helper.mirror_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from bot.helper.mirror_utils.status_utils.tg_upload_status import TgUploadStatus
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.mirror_utils.upload_utils.pyrogramEngine import TgUploader
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import auto_delete_message, auto_delete_upload_message, sendMessage, sendMarkup, delete_all_messages, update_all_messages
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import DbManger


class MirrorListener:
    def __init__(self, bot, message, isZip=False, extract=False, isQbit=False, isLeech=False, pswd=None, tag=None, seed=False):
        self.bot = bot
        self.message = message
        self.uid = self.message.message_id
        self.extract = extract
        self.isZip = isZip
        self.isQbit = isQbit
        self.isLeech = isLeech
        self.pswd = pswd
        self.tag = tag
        self.seed = any([seed, QB_SEED])
        self.isPrivate = self.message.chat.type in ['private', 'group']

    def clean(self):
        try:
            Interval[0].cancel()
            Interval.clear()
            aria2.purge()
            delete_all_messages()
        except:
            pass

    def onDownloadStart(self):
        if not self.isPrivate and INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
            DbManger().add_incomplete_task(self.message.chat.id, self.message.link, self.tag)

    def onDownloadComplete(self):
        with download_dict_lock:
            LOGGER.info(f"Download completed: {download_dict[self.uid].name()}")
            download = download_dict[self.uid]
            name = str(download.name()).replace('/', '')
            gid = download.gid()
            size = download.size_raw()
            if name == "None" or self.isQbit or not ospath.exists(f'{DOWNLOAD_DIR}{self.uid}/{name}'):
                name = listdir(f'{DOWNLOAD_DIR}{self.uid}')[-1]
            m_path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        if self.isZip:
            try:
                with download_dict_lock:
                    download_dict[self.uid] = ZipStatus(name, m_path, size)
                path = m_path + ".zip"
                LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
                if self.pswd is not None:
                    if self.isLeech and int(size) > TG_SPLIT_SIZE:
                        srun(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", f"-p{self.pswd}", path, m_path])
                    else:
                        srun(["7z", "a", "-mx=0", f"-p{self.pswd}", path, m_path])
                elif self.isLeech and int(size) > TG_SPLIT_SIZE:
                    srun(["7z", f"-v{TG_SPLIT_SIZE}b", "a", "-mx=0", path, m_path])
                else:
                    srun(["7z", "a", "-mx=0", path, m_path])
            except FileNotFoundError:
                LOGGER.info('File to archive not found!')
                self.onUploadError('Internal error occurred!!')
                return
            if not self.isQbit or not self.seed or self.isLeech:
                try:
                    rmtree(m_path)
                except:
                    osremove(m_path)
        elif self.extract:
            try:
                if ospath.isfile(m_path):
                    path = get_base_name(m_path)
                LOGGER.info(f"Extracting: {name}")
                with download_dict_lock:
                    download_dict[self.uid] = ExtractStatus(name, m_path, size)
                if ospath.isdir(m_path):
                    for dirpath, subdir, files in walk(m_path, topdown=False):
                        for file_ in files:
                            if file_.endswith((".zip", ".7z")) or re_search(r'\.part0*1\.rar$|\.7z\.0*1$|\.zip\.0*1$', file_) \
                               or (file_.endswith(".rar") and not re_search(r'\.part\d+\.rar$', file_)):
                                m_path = ospath.join(dirpath, file_)
                                if self.pswd is not None:
                                    result = srun(["7z", "x", f"-p{self.pswd}", m_path, f"-o{dirpath}", "-aot"])
                                else:
                                    result = srun(["7z", "x", m_path, f"-o{dirpath}", "-aot"])
                                if result.returncode != 0:
                                    LOGGER.error('Unable to extract archive!')
                        for file_ in files:
                            if file_.endswith((".rar", ".zip", ".7z")) or re_search(r'\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$', file_):
                                del_path = ospath.join(dirpath, file_)
                                osremove(del_path)
                    path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
                else:
                    if self.pswd is not None:
                        result = srun(["bash", "pextract", m_path, self.pswd])
                    else:
                        result = srun(["bash", "extract", m_path])
                    if result.returncode == 0:
                        LOGGER.info(f"Extracted Path: {path}")
                        osremove(m_path)
                    else:
                        LOGGER.error('Unable to extract archive! Uploading anyway')
                        path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        else:
            path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        up_name = PurePath(path).name
        up_path = f'{DOWNLOAD_DIR}{self.uid}/{up_name}'
        if self.isLeech and not self.isZip:
            checked = False
            for dirpath, subdir, files in walk(f'{DOWNLOAD_DIR}{self.uid}', topdown=False):
                for file_ in files:
                    f_path = ospath.join(dirpath, file_)
                    f_size = ospath.getsize(f_path)
                    if int(f_size) > TG_SPLIT_SIZE:
                        if not checked:
                            checked = True
                            with download_dict_lock:
                                download_dict[self.uid] = SplitStatus(up_name, up_path, size)
                            LOGGER.info(f"Splitting: {up_name}")
                        split_file(f_path, f_size, file_, dirpath, TG_SPLIT_SIZE)
                        osremove(f_path)
        if self.isLeech:
            size = get_path_size(f'{DOWNLOAD_DIR}{self.uid}')
            LOGGER.info(f"Leech Name: {up_name}")
            tg = TgUploader(up_name, self)
            tg_upload_status = TgUploadStatus(tg, size, gid, self)
            with download_dict_lock:
                download_dict[self.uid] = tg_upload_status
            update_all_messages()
            tg.upload()
        else:
            size = get_path_size(up_path)
            LOGGER.info(f"Upload Name: {up_name}")
            drive = GoogleDriveHelper(up_name, self)
            upload_status = UploadStatus(drive, size, gid, self)
            with download_dict_lock:
                download_dict[self.uid] = upload_status
            update_all_messages()
            drive.upload(up_name)

    def onDownloadError(self, error):
        error = error.replace('<', ' ').replace('>', ' ')
        clean_download(f'{DOWNLOAD_DIR}{self.uid}')
        with download_dict_lock:
            try:
                del download_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(download_dict)
        msg = f"{self.tag} your download has been stopped due to: {error}"
        sendMessage(msg, self.bot, self.message)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

        if not self.isPrivate and INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
            DbManger().rm_complete_task(self.message.link)

    def onUploadComplete(self, link: str, size, files, folders, typ, name: str):
        kie = datetime.now(timezone(f"{TIMEZONE}"))
        jam = kie.strftime("\n 𝗗𝗮𝘁𝗲 : %d/%m/%Y\n 𝗧𝗶𝗺𝗲: %I:%M:%S %P")
        msg = f"{jam}"
        uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
        chat_id = str(LEECH_LOG)[5:][:-1]
        buttons = ButtonMaker()
        # this is inspired by def mirror to get the link from message
        mesg = self.message.text.split("\n")
        message_args = mesg[0].split(" ", maxsplit=1)
        reply_to = self.message.reply_to_message
        slmsg = f"\n╭─📂 𝐅𝐢𝐥𝐞𝐧𝐚𝐦𝐞 ⇢ <code>{escape(name)}</code>"
        slmsg += f"\n├─🕹️ 𝗦𝗶𝘇𝗲 ⇢ {size}"
        slmsg += f"\n├─🪧 𝗔𝗱𝗱𝗲𝗱 𝗯𝘆 ⇢ {uname}"
        if LINK_LOGS:
            try:
                source_link = message_args[1]
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
        if not self.isPrivate and INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
            DbManger().rm_complete_task(self.message.link)
        if AUTO_DELETE_UPLOAD_MESSAGE_DURATION != -1:
            reply_to = self.message.reply_to_message
            if reply_to is not None:
                try:
                    reply_to.delete()
                except Exception as error:
                    LOGGER.warning(error)
            if self.message.chat.type == "private":
                warnmsg = ""
            else:
                autodel = secondsToText()
                warnmsg = f" \n 𝗧𝗵𝗶𝘀 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝘄𝗶𝗹𝗹 𝗮𝘂𝘁𝗼 𝗱𝗲𝗹𝗲𝘁𝗲𝗱 𝗶𝗻 {autodel}\n\n"
        else:
            warnmsg = ""
        if BOT_PM and self.message.chat.type != "private":
            pmwarn = f"𝗜 𝗵𝗮𝘃𝗲 𝘀𝗲𝗻𝘁 𝗳𝗶𝗹𝗲𝘀 𝗶𝗻 𝗣𝗠.\n"
            pmwarn_mirror = f"𝗜 𝗵𝗮𝘃𝗲 𝘀𝗲𝗻𝘁 𝗹𝗶𝗻𝗸𝘀 𝗶𝗻 𝗣𝗠.\n"
        elif self.message.chat.type == "private":
            pmwarn = ""
            pmwarn_mirror = ""
        else:
            pmwarn = ""
            pmwarn_mirror = ""
        logwarn = f"𝗜 𝗵𝗮𝘃𝗲 𝘀𝗲𝗻𝘁 𝗳𝗶𝗹𝗲𝘀 𝗶𝗻 𝗟𝗼𝗴 𝗖𝗵𝗮𝗻𝗻𝗲𝗹.\n"
        msg += f"\n╭─📂 𝐅𝐢𝐥𝐞𝐧𝐚𝐦𝐞 ⇢ <code>{escape(name)}</code>"
        msg += f"\n├─🕹️ 𝗦𝗶𝘇𝗲 ⇢ {size}"
        if self.isLeech:
            msg += f'\n├─📚 𝐓𝐨𝐭𝐚𝐥 𝐅𝐢𝐥𝐞𝐬 ⇢ {folders}'
            if typ != 0:
                msg += f'\n├─💻 𝗖𝗼𝗿𝗿𝘂𝗽𝘁𝗲𝗱 𝗙𝗶𝗹𝗲𝘀 ⇢ {typ}'
            msg += f'\n╰─📬 𝗟𝗲𝗲𝗰𝗵𝗲𝗱 𝐁𝐲 ⇢ {self.tag}\n\n'
            if not files:
                sendMessage(msg, self.bot, self.message)
            if BOT_PM and self.message.chat.type != "private":
                try:
                    LOGGER.info(self.message.chat.type)
                    reply_markup = sendMessage(msg + pmwarn + warnmsg, self.bot, self.message)
                    Thread(target=auto_delete_upload_message, args=(bot, self.message, reply_markup)).start()
                except Exception as e:
                    LOGGER.warning(e)
                    return
            if MIRROR_LOGS:
                for i in MIRROR_LOGS:
                    indexmsg = ""
                    for index, item in enumerate(list(files), start=1):
                        msg_id = files[item]
                        link = f"https://t.me/c/{chat_id}/{msg_id}"
                        indexmsg += f"{index}. <a href='{link}'>{item}</a>\n"
                        if len(indexmsg.encode("utf-8") + msg.encode("utf-8")) > 4000:
                            sleep(1.5)
                            bot.sendMessage(chat_id=i, text=msg + indexmsg, reply_markup=InlineKeyboardMarkup(buttons.build_menu(2)), parse_mode=ParseMode.HTML)
                            indexmsg = ""
                     if indexmsg != "":
                        sleep(1.5)
                        bot.sendMessage(chat_id=i, text=msg + indexmsg, reply_markup=InlineKeyboardMarkup(buttons.build_menu(2)), parse_mode=ParseMode.HTML)
            else:
                fmsg = 'n\n'
                for index, (link, name) in enumerate(files.items(), start=1):
                    fmsg += f"{index}. <a href='{link}'>{name}</a>\n"
                    if len(fmsg.encode() + msg.encode()) > 4000:
                        sendMessage(msg + fmsg, self.bot, self.message)
                        sleep(1)
                        fmsg = ''
                if fmsg != '':
                    sendMessage(msg + fmsg, self.bot, self.message)
        else:
            msg += f'\n\n<b>Type: </b>{typ}'
            if ospath.isdir(f'{DOWNLOAD_DIR}{self.uid}/{name}'):
                msg += f'\n├─📂 𝐒𝐮𝐛-𝐅𝐨𝐥𝐝𝐞𝐫𝐬 ⇢ {folders}'
                msg += f'\n├─📚 𝐅𝐢𝐥𝐞𝐬 ⇢ {files}'
            msg += f'\n╰─📬 𝐁𝐲 ⇢ {self.tag}\n\n'
            buttons = ButtonMaker()
            buttons.buildbutton("☁️ Drive Link", link)
            LOGGER.info(f'Done Uploading {name}')
            if INDEX_URL is not None:
                url_path = rutils.quote(f'{name}')
                share_url = f'{INDEX_URL}/{url_path}'
                if ospath.isdir(f'{DOWNLOAD_DIR}/{self.uid}/{name}'):
                    share_url += '/'
                    buttons.buildbutton(f"{INDEX_BUTTON}", share_url)
                else:
                    buttons.buildbutton(f"{INDEX_BUTTON}", share_url)
                    if VIEW_LINK:
                        share_urls = f'{INDEX_URL}/{url_path}?a=view'
                        buttons.buildbutton(f"{VIEW_BUTTON}", share_urls)
                if SOURCE_LINK is not None:
                    buttons.buildbutton(f"{SOURCE_LINK}", link)
                if MIRROR_LOGS:
                try:
                    for i in MIRROR_LOGS:
                        bot.sendMessage(chat_id=i, text=msg, reply_markup=InlineKeyboardMarkup(buttons.build_menu(2)), parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.warning(e)
                if BOT_PM and self.message.chat.type != "private":
                    try:
                        bot.sendMessage(chat_id=self.user_id, text=msg, reply_markup=InlineKeyboardMarkup(buttons.build_menu(2)), parse_mode=ParseMode.HTML)
                    except Exception as e:
                        LOGGER.warning(e)
                        return
            if self.isQbit and self.seed and not self.extract:
                if self.isZip:
                    try:
                        osremove(f'{DOWNLOAD_DIR}{self.uid}/{name}')
                    except:
                        pass
                reply_markup = sendMarkup(msg + pmwarn_mirror + warnmsg, self.bot, self.message, InlineKeyboardMarkup(buttons.build_menu(2)))
                Thread(target=auto_delete_upload_message, args=(self.bot, self.message, reply_markup)).start()
                return
            else:
                reply_markup = sendMarkup(msg + pmwarn_mirror + warnmsg, self.bot, self.message, InlineKeyboardMarkup(buttons.build_menu(2)))
                Thread(target=auto_delete_upload_message, args=(self.bot, self.message, reply_markup)).start()
        clean_download(f'{DOWNLOAD_DIR}{self.uid}')
        with download_dict_lock:
            try:
                del download_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(download_dict)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadError(self, error):
        reply_to = self.message.reply_to_message
        if reply_to is not None:
            try:
                reply_to.delete()
            except BaseException:
                pass
        e_str = error.replace('<', '').replace('>', '')
        clean_download(f'{DOWNLOAD_DIR}{self.uid}')
        with download_dict_lock:
            try:
                del download_dict[self.uid]
            except Exception as e:
                LOGGER.error(str(e))
            count = len(download_dict)
        sendMessage(f"{self.tag} {e_str}", self.bot, self.message)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

        if not self.isPrivate and INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
            DbManger().rm_complete_task(self.message.link)

def _mirror(bot, message, isZip=False, extract=False, isQbit=False, isLeech=False, pswd=None, multi=0, qbsd=False):
    mesg = message.text.split('\n')
    length_of_leechlog = len(LEECH_LOG)
    message_args = mesg[0].split(maxsplit=1)
    name_args = mesg[0].split('|', maxsplit=1)
    is_gdtot = False
    qbsel = False
    index = 1
    if FSUB:
        try:
            user = bot.get_chat_member(f"{FSUB_CHANNEL_ID}", message.from_user.id)
            LOGGER.info(user.status)
            if user.status not in ('member', 'creator', 'administrator', 'supergroup'):
                uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
                buttons = ButtonMaker()
                chat_u = CHANNEL_USERNAME.replace('@', '')
                buttons.buildbutton('👉🏻 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗜𝗡𝗞 👈🏻', f'https://t.me/{chat_u}')
                help_msg = f'𝗗𝗘𝗔𝗥 {uname},\n𝗬𝗢𝗨 𝗡𝗘𝗘𝗗 𝗧𝗢 𝗝𝗢𝗜𝗡 𝗠𝗬 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗧𝗢 𝗨𝗦𝗘 𝗕𝗢𝗧. \n\n𝗖𝗟𝗜𝗖𝗞 𝗢𝗡 𝗧𝗛𝗘 𝗕𝗘𝗟𝗢𝗪 𝗕𝗨𝗧𝗧𝗢𝗡 𝗧𝗢 𝗝𝗢𝗜𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟'
                reply_message = sendMarkup(help_msg, bot, message, InlineKeyboardMarkup(buttons.build_menu(2)))
                Thread(target=auto_delete_message, args=(bot, message, reply_message)).start()
                return
        except Exception:
            pass
    if isLeech and length_of_leechlog == 0:
        try:
            text = 'Error: Leech Functionality will not work\nReason: Your Leech Log var is empty.\n\nRead the README file it's there for a reason.'
            msg = sendMessage(text, bot, message)
            LOGGER.error('Leech Log var is Empty\nKindly add Chat id in Leech log to use Leech Functionality\nRead the README file it's there for a reason\n')  
            Thread(target=auto_delete_message, args=(bot, message, msg)).start()
            return
        except Exception as err:
            LOGGER.error(f'Uff We got Some Error:\n{err}')
    if BOT_PM and message.chat.type != "private":
        try:
            msg1 = f"𝗔𝗱𝗱𝗲𝗱 𝘆𝗼𝘂𝗿 𝗥𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝗹𝗶𝗻𝗸 𝘁𝗼 𝗰𝗹𝗼𝗻𝗲\n"
            send = bot.sendMessage(message.from_user.id, text=msg1)
            send.delete()
        except Exception as e:
            LOGGER.warning(e)
            uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
            buttons = ButtonMaker()
            buttons.buildbutton('👉🏻 𝗦𝗧𝗔𝗥𝗧 𝗕𝗢𝗧 👈🏻', f'https://t.me/{bot.get_me().username}?start=start')
            help_msg = f'𝗗𝗘𝗔𝗥 {uname},\n𝗬𝗢𝗨 𝗡𝗘𝗘𝗗 𝗧𝗢 𝗦𝗧𝗔𝗥𝗧 𝗧𝗛𝗘 𝗕𝗢𝗧 𝗨𝗦𝗜𝗡𝗚 𝗧𝗢 𝗕𝗘𝗟𝗢𝗪 𝗕𝗨𝗧𝗧𝗢𝗡. \n\n𝗜𝗧𝗦 𝗡𝗘𝗘𝗗𝗘𝗗 𝗦𝗢 𝗕𝗢𝗧 𝗖𝗔𝗡 𝗦𝗘𝗡𝗗 𝗬𝗢𝗨𝗥 𝗠𝗜𝗥𝗥𝗢𝗥/𝗖𝗟𝗢𝗡𝗘/𝗟𝗘𝗘𝗖𝗛𝗘𝗗 𝗙𝗜𝗟𝗘𝗦 𝗜𝗡 𝗣𝗠. \n\n𝗖𝗟𝗜𝗖𝗞 𝗢𝗡 𝗧𝗛𝗘 𝗕𝗘𝗟𝗢𝗪 𝗕𝗨𝗧𝗧𝗢𝗡 𝗧𝗢 𝗦𝗧𝗔𝗥𝗧 𝗧𝗛𝗘 𝗕𝗢𝗧'
            reply_message = sendMarkup(help_msg, bot, message, InlineKeyboardMarkup(buttons.build_menu(2)))
            Thread(target=auto_delete_message, args=(bot, message, reply_message)).start()
            return
    if len(message_args) > 1:
        args = mesg[0].split(maxsplit=3)
        if "s" in [x.strip() for x in args]:
            qbsel = True
            index += 1
        if "d" in [x.strip() for x in args]:
            qbsd = True
            index += 1
        message_args = mesg[0].split(maxsplit=index)
        if len(message_args) > index:
            link = message_args[index].strip()
            if link.isdigit():
                multi = int(link)
                link = ''
            elif link.startswith(("|", "pswd:")):
                link = ''
        else:
            link = ''
    else:
        link = ''

    if len(name_args) > 1:
        name = name_args[1]
        name = name.split(' pswd:')[0]
        name = name.strip()
    else:
        name = ''

    link = re_split(r"pswd:|\|", link)[0]
    link = link.strip()

    pswd_arg = mesg[0].split(' pswd: ')
    if len(pswd_arg) > 1:
        pswd = pswd_arg[1]

    if message.from_user.username:
        tag = f"@{message.from_user.username}"
    else:
        tag = message.from_user.mention_html(message.from_user.first_name)

    reply_to = message.reply_to_message
    if reply_to is not None:
        file = None
        media_array = [reply_to.document, reply_to.video, reply_to.audio]
        for i in media_array:
            if i is not None:
                file = i
                break

        if not reply_to.from_user.is_bot:
            if reply_to.from_user.username:
                tag = f"@{reply_to.from_user.username}"
            else:
                tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)

        if not is_url(link) and not is_magnet(link) or len(link) == 0:
            if file is None:
                reply_text = reply_to.text.split(maxsplit=1)[0].strip()
                if is_url(reply_text) or is_magnet(reply_text):
                    link = reply_text
            elif file.mime_type != "application/x-bittorrent" and not isQbit:
                listener = MirrorListener(bot, message, isZip, extract, isQbit, isLeech, pswd, tag)
                Thread(target=TelegramDownloadHelper(listener).add_download, args=(message, f'{DOWNLOAD_DIR}{listener.uid}/', name)).start()
                if multi > 1:
                    sleep(4)
                    nextmsg = type('nextmsg', (object, ), {'chat_id': message.chat_id, 'message_id': message.reply_to_message.message_id + 1})
                    nextmsg = sendMessage(message_args[0], bot, nextmsg)
                    nextmsg.from_user.id = message.from_user.id
                    multi -= 1
                    sleep(4)
                    Thread(target=_mirror, args=(bot, nextmsg, isZip, extract, isQbit, isLeech, pswd, multi)).start()
                return
            else:
                link = file.get_file().file_path

    if not is_url(link) and not is_magnet(link) and not ospath.exists(link):
        help_msg = "<b>Send link along with command line:</b>"
        help_msg += "\n<code>/command</code> {link} |newname pswd: xx [zip/unzip]"
        help_msg += "\n\n<b>By replying to link or file:</b>"
        help_msg += "\n<code>/command</code> |newname pswd: xx [zip/unzip]"
        help_msg += "\n\n<b>Direct link authorization:</b>"
        help_msg += "\n<code>/command</code> {link} |newname pswd: xx\nusername\npassword"
        help_msg += "\n\n<b>Qbittorrent selection and seed:</b>"
        help_msg += "\n<code>/qbcommand</code> <b>s</b>(for selection) <b>d</b>(for seeding) {link} or by replying to {file/link}"
        help_msg += "\n\n<b>Multi links only by replying to first link or file:</b>"
        help_msg += "\n<code>/command</code> 10(number of links/files)"
        return sendMessage(help_msg, bot, message)

    LOGGER.info(link)

    if not is_mega_link(link) and not isQbit and not is_magnet(link) \
        and not is_gdrive_link(link) and not link.endswith('.torrent'):
        content_type = get_content_type(link)
        if content_type is None or re_match(r'text/html|text/plain', content_type):
            try:
                link = direct_link_generator(link)
                is_gdtot = is_gdtot_link(link)
                is_appdrive = is_appdrive_link(link)
                if is_gdtot:
                    link = gdtot(link)
                elif is_appdrive:
                    link = appdrive(link)
                LOGGER.info(f"Generated link: {link}")
            except DirectDownloadLinkException as e:
                LOGGER.info(str(e))
                if str(e).startswith('ERROR:'):
                    return sendMessage(str(e), bot, message)
    elif isQbit and not is_magnet(link):
        if link.endswith('.torrent') or "https://api.telegram.org/file/" in link:
            content_type = None
        else:
            content_type = get_content_type(link)
        if content_type is None or re_match(r'application/x-bittorrent|application/octet-stream', content_type):
            try:
                resp = rget(link, timeout=10, headers = {'user-agent': 'Wget/1.12'})
                if resp.status_code == 200:
                    file_name = str(time()).replace(".", "") + ".torrent"
                    with open(file_name, "wb") as t:
                        t.write(resp.content)
                    link = str(file_name)
                else:
                    return sendMessage(f"{tag} ERROR: link got HTTP response: {resp.status_code}", bot, message)
            except Exception as e:
                error = str(e).replace('<', ' ').replace('>', ' ')
                if error.startswith('No connection adapters were found for'):
                    link = error.split("'")[1]
                else:
                    LOGGER.error(str(e))
                    return sendMessage(tag + " " + error, bot, message)
        else:
            msg = "Qb commands for torrents only. if you are trying to dowload torrent then report."
            return sendMessage(msg, bot, message)


    listener = MirrorListener(bot, message, isZip, extract, isQbit, isLeech, pswd, tag, qbsd)

    if is_gdrive_link(link):
        if not isZip and not extract and not isLeech:
            gmsg = f"Use /{BotCommands.CloneCommand} to clone Google Drive file/folder\n\n"
            gmsg += f"Use /{BotCommands.ZipMirrorCommand} to make zip of Google Drive folder\n\n"
            gmsg += f"Use /{BotCommands.UnzipMirrorCommand} to extracts Google Drive archive file"
            sendMessage(gmsg, bot, message)
        else:
            Thread(target=add_gd_download, args=(link, listener)).start()
    elif is_mega_link(link):
        Thread(target=add_mega_download, args=(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener)).start()
    elif isQbit and (is_magnet(link) or ospath.exists(link)):
        Thread(target=QbDownloader(listener).add_qb_torrent, args=(link, f'{DOWNLOAD_DIR}{listener.uid}', qbsel)).start()
    else:
        if len(mesg) > 1:
            try:
                ussr = mesg[1]
            except:
                ussr = ''
            try:
                pssw = mesg[2]
            except:
                pssw = ''
            auth = f"{ussr}:{pssw}"
            auth = "Basic " + b64encode(auth.encode()).decode('ascii')
        else:
            auth = ''
        Thread(target=add_aria2c_download, args=(link, f'{DOWNLOAD_DIR}{listener.uid}', listener, name, auth)).start()

    if multi > 1:
        sleep(4)
        nextmsg = type('nextmsg', (object, ), {'chat_id': message.chat_id, 'message_id': message.reply_to_message.message_id + 1})
        msg = message_args[0]
        if len(mesg) > 2:
            msg += '\n' + mesg[1] + '\n' + mesg[2]
        nextmsg = sendMessage(msg, bot, nextmsg)
        nextmsg.from_user.id = message.from_user.id
        multi -= 1
        sleep(4)
        Thread(target=_mirror, args=(bot, nextmsg, isZip, extract, isQbit, isLeech, pswd, multi)).start()


def mirror(update, context):
    _mirror(context.bot, update.message)

def unzip_mirror(update, context):
    _mirror(context.bot, update.message, extract=True)

def zip_mirror(update, context):
    _mirror(context.bot, update.message, True)

def qb_mirror(update, context):
    _mirror(context.bot, update.message, isQbit=True)

def qb_unzip_mirror(update, context):
    _mirror(context.bot, update.message, extract=True, isQbit=True)

def qb_zip_mirror(update, context):
    _mirror(context.bot, update.message, True, isQbit=True)

def leech(update, context):
    _mirror(context.bot, update.message, isLeech=True)

def unzip_leech(update, context):
    _mirror(context.bot, update.message, extract=True, isLeech=True)

def zip_leech(update, context):
    _mirror(context.bot, update.message, True, isLeech=True)

def qb_leech(update, context):
    _mirror(context.bot, update.message, isQbit=True, isLeech=True)

def qb_unzip_leech(update, context):
    _mirror(context.bot, update.message, extract=True, isQbit=True, isLeech=True)

def qb_zip_leech(update, context):
    _mirror(context.bot, update.message, True, isQbit=True, isLeech=True)

mirror_handler = CommandHandler(BotCommands.MirrorCommand, mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
unzip_mirror_handler = CommandHandler(BotCommands.UnzipMirrorCommand, unzip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
zip_mirror_handler = CommandHandler(BotCommands.ZipMirrorCommand, zip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_mirror_handler = CommandHandler(BotCommands.QbMirrorCommand, qb_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_unzip_mirror_handler = CommandHandler(BotCommands.QbUnzipMirrorCommand, qb_unzip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_zip_mirror_handler = CommandHandler(BotCommands.QbZipMirrorCommand, qb_zip_mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
leech_handler = CommandHandler(BotCommands.LeechCommand, leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
unzip_leech_handler = CommandHandler(BotCommands.UnzipLeechCommand, unzip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
zip_leech_handler = CommandHandler(BotCommands.ZipLeechCommand, zip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_leech_handler = CommandHandler(BotCommands.QbLeechCommand, qb_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_unzip_leech_handler = CommandHandler(BotCommands.QbUnzipLeechCommand, qb_unzip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
qb_zip_leech_handler = CommandHandler(BotCommands.QbZipLeechCommand, qb_zip_leech,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)

dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(unzip_mirror_handler)
dispatcher.add_handler(zip_mirror_handler)
dispatcher.add_handler(qb_mirror_handler)
dispatcher.add_handler(qb_unzip_mirror_handler)
dispatcher.add_handler(qb_zip_mirror_handler)
dispatcher.add_handler(leech_handler)
dispatcher.add_handler(unzip_leech_handler)
dispatcher.add_handler(zip_leech_handler)
dispatcher.add_handler(qb_leech_handler)
dispatcher.add_handler(qb_unzip_leech_handler)
dispatcher.add_handler(qb_zip_leech_handler)
