#! BEST ON PYTHON VERSION 3.10

import asyncio
import os
import random
import re
import shutil
import ssl
import time
from datetime import datetime
import aiohttp
import ujson as json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from cfonts import render
from ProTo import DecodeWhisper_pb2
from ProTo import MajorLoginRes_pb2
from ProTo import LoginData_pb2
from ProTo import MajorLoginReq_pb2
from ProTo import received_chat_pb2

from flask import Flask, request, jsonify
import threading
from queue import Queue

from R1 import *

# ======================== GLOBALS ========================
online_writer = None
whisper_writer = None
insquad = None
joining_team = False
spammer_uid = None
spam_chat_id = None
spam_uid = None
chat_id = None
uid = None
XX = None
packet_json = None
region = "me"
TOKEN_EXPIRY = 6 * 60 * 60

# Multi-account variables
current_account_index = 0
accounts_list = []
total_accounts_loaded = 0
account_lock = asyncio.Lock()
current_session_account = None  # الحساب المستخدم حالياً

app = Flask(__name__)
command_queue = Queue()
bot_ready = True

# ======================== FLASK API ========================
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "service": "Multi-Account Free Fire Squad API - Auto Switch Per Command",
        "total_accounts": len(accounts_list),
        "current_account": current_account_index + 1 if accounts_list else 0,
        "current_uid": accounts_list[current_account_index]["uid"] if accounts_list else None,
        "auto_switch": "ON - كل أمر يغير الحساب",
        "commands": ["/3", "/5", "/6", "/switch_account", "/accounts"]
    })

@app.route("/3")
def squad3():
    global current_account_index, current_session_account
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid required"}), 400
    
    # تسجيل الحساب المستخدم قبل التبديل
    old_account = current_account_index + 1 if accounts_list else 0
    old_uid = accounts_list[current_account_index]["uid"] if accounts_list else None
    
    # تبديل الحساب قبل تنفيذ الأمر
    switch_to_next_account()
    
    new_uid = accounts_list[current_account_index]["uid"] if accounts_list else None
    
    command_queue.put({"type": 3, "uid": uid})
    
    return jsonify({
        "status": "queued",
        "players": 3,
        "target_uid": uid,
        "previous_account": old_account,
        "previous_uid": old_uid,
        "current_account": current_account_index + 1,
        "current_uid": new_uid,
        "message": f"تم التبديل من حساب {old_uid} إلى {new_uid} لهذا الأمر"
    })

@app.route("/5")
def squad5():
    global current_account_index, current_session_account
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid required"}), 400
    
    old_account = current_account_index + 1 if accounts_list else 0
    old_uid = accounts_list[current_account_index]["uid"] if accounts_list else None
    
    switch_to_next_account()
    
    new_uid = accounts_list[current_account_index]["uid"] if accounts_list else None
    
    command_queue.put({"type": 5, "uid": uid})
    
    return jsonify({
        "status": "queued",
        "players": 5,
        "target_uid": uid,
        "previous_account": old_account,
        "previous_uid": old_uid,
        "current_account": current_account_index + 1,
        "current_uid": new_uid,
        "message": f"تم التبديل من حساب {old_uid} إلى {new_uid} لهذا الأمر"
    })

@app.route("/6")
def squad6():
    global current_account_index, current_session_account
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid required"}), 400
    
    old_account = current_account_index + 1 if accounts_list else 0
    old_uid = accounts_list[current_account_index]["uid"] if accounts_list else None
    
    switch_to_next_account()
    
    new_uid = accounts_list[current_account_index]["uid"] if accounts_list else None
    
    command_queue.put({"type": 6, "uid": uid})
    
    return jsonify({
        "status": "queued",
        "players": 6,
        "target_uid": uid,
        "previous_account": old_account,
        "previous_uid": old_uid,
        "current_account": current_account_index + 1,
        "current_uid": new_uid,
        "message": f"تم التبديل من حساب {old_uid} إلى {new_uid} لهذا الأمر"
    })

@app.route("/status")
def status():
    return jsonify({
        "bot_ready": bot_ready,
        "queue_size": command_queue.qsize(),
        "total_accounts": len(accounts_list),
        "current_account_index": current_account_index + 1 if accounts_list else 0,
        "current_account_uid": accounts_list[current_account_index]["uid"] if accounts_list else None,
        "auto_switch_per_command": True
    })

@app.route("/switch_account")
def switch_account():
    global current_account_index
    old_index = current_account_index + 1 if accounts_list else 0
    old_uid = accounts_list[current_account_index]["uid"] if accounts_list else None
    
    account_id = request.args.get("account_id")
    
    if account_id:
        try:
            new_index = int(account_id) - 1
            if 0 <= new_index < len(accounts_list):
                current_account_index = new_index
                return jsonify({
                    "status": "switched",
                    "previous_account": old_index,
                    "previous_uid": old_uid,
                    "current_account": current_account_index + 1,
                    "uid": accounts_list[current_account_index]["uid"]
                })
        except:
            pass
    
    # Switch to next account
    current_account_index = (current_account_index + 1) % len(accounts_list) if accounts_list else 0
    return jsonify({
        "status": "switched_to_next",
        "previous_account": old_index,
        "previous_uid": old_uid,
        "current_account": current_account_index + 1,
        "uid": accounts_list[current_account_index]["uid"] if accounts_list else None
    })

@app.route("/accounts")
def list_accounts():
    accounts_info = []
    for idx, acc in enumerate(accounts_list):
        accounts_info.append({
            "number": idx + 1,
            "uid": acc["uid"],
            "is_current": idx == current_account_index
        })
    return jsonify({
        "accounts": accounts_info,
        "total": len(accounts_list),
        "current": current_account_index + 1 if accounts_list else 0,
        "auto_switch_mode": "كل أمر يغير الحساب"
    })

def switch_to_next_account():
    """تبديل الحساب إلى التالي"""
    global current_account_index
    if accounts_list:
        old_index = current_account_index
        current_account_index = (current_account_index + 1) % len(accounts_list)
        print(f"🔄 تم التبديل من حساب {old_index + 1} إلى حساب {current_account_index + 1}")
        print(f"🔑 UID القديم: {accounts_list[old_index]['uid']}")
        print(f"🔑 UID الجديد: {accounts_list[current_account_index]['uid']}")

# ======================== FILE MANAGEMENT ========================
def clear_pycache(root_dir):
    """Automatic Delete the __pycache__"""
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        if os.path.basename(dirpath) == "__pycache__":
            try:
                shutil.rmtree(dirpath)
            except Exception:
                pass

clear_pycache(os.getcwd())

def create_credentials_template(filename="bot.txt"):
    template = """
# ============================================
# FREE FIRE MULTI-ACCOUNT CONFIGURATION FILE
# ============================================
# Add your accounts here, one per line
# Format: uid=YOUR_UID,password=YOUR_PASSWORD
# ============================================

# Example accounts (replace with yours):
uid=1234567890,password=your_password_here
uid=0987654321,password=another_password_here
uid=1122334455,password=third_password_here

# ============================================
# ملاحظة: كل أمر من API يغير الحساب تلقائياً
# ============================================
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"📝 Created template {filename}")

def load_accounts_from_file(filename="bot.txt"):
    if not os.path.exists(filename):
        print(f"❌ {filename} not found!")
        create_credentials_template(filename)
        return []

    accounts = []

    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Extract uid and password
                uid_match = re.search(r"uid\s*[:=]\s*(\d+)", line, re.IGNORECASE)
                pass_match = re.search(r"password\s*[:=]\s*(\S+)", line, re.IGNORECASE)

                if uid_match and pass_match:
                    accounts.append({
                        "uid": uid_match.group(1),
                        "password": pass_match.group(1),
                        "line": line_num
                    })
                    print(f"✅ Loaded account {len(accounts)}: UID {uid_match.group(1)}")
                else:
                    print(f"⚠️ Skipping invalid line {line_num}: {line}")

        if not accounts:
            print("❌ No valid accounts found in bot.txt")
            print("📝 Format should be: uid=YOUR_UID,password=YOUR_PASSWORD")
            return []

        print(f"\n📊 Total accounts loaded: {len(accounts)}")
        print(f"🔄 Auto-switch mode: كل أمر يغير الحساب")
        return accounts

    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return []

# ======================== NETWORK FUNCTIONS ========================
async def encrypt_packet(packet_hex, key, iv):
    """Encrypt packet using AES CBC"""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    packet_bytes = bytes.fromhex(packet_hex)
    padded_packet = pad(packet_bytes, AES.block_size)
    encrypted = cipher.encrypt(padded_packet)
    return encrypted.hex()

def Encrypt(number):
    """Encrypt function from your first TCP bot"""
    number = int(number)
    encoded_bytes = []
    
    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80
        encoded_bytes.append(byte)
        if not number:
            break
    
    return bytes(encoded_bytes).hex()

# Headers
Hr = {
    'User-Agent': "UnityPlayer/2018.4.11f1",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB53"}

async def encrypted_proto(payload: bytes):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(payload, AES.block_size)
    return cipher.encrypt(padded)

async def GeNeRaTeAccEss(uid , password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "UnityPlayer/2018.4.11f1",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close",
    }
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                return "Failed to get access token"

            data = await response.json()
            open_id = data.get("open_id")
            access_token = data.get("access_token")
            return (open_id, access_token) if open_id and access_token else (None, None)

async def EncRypTMajoRLoGin(open_id, access_token):
    major_login = MajorLoginReq_pb2.MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 1
    major_login.client_version = "1.123.1"
    major_login.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major_login.system_hardware = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_type = "WIFI"
    major_login.screen_width = 1920
    major_login.screen_height = 1080
    major_login.screen_dpi = "320"
    major_login.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno (TM) 640"
    major_login.gpu_version = "OpenGL ES 3.1 v1.46"
    major_login.unique_device_id = f"Google|{random.getrandbits(128):032x}"
    major_login.client_ip = ""
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2019118695"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = 13564
    major_login.release_channel = "android"
    major_login.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 0
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    string = major_login.SerializeToString()
    return await encrypted_proto(string)

async def MajorLogin(payload):
    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    headers = Hr.copy()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers, ssl=ssl_context, timeout=10) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    err = await response.read()
                    print(f"❌ Login failed [{response.status}]: {err}")
                    return None
    except Exception as e:
        print(f"❌ MajorLogin error: {e}")
        return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    headers = Hr.copy()
    headers['Authorization'] = f"Bearer {token}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers, ssl=ssl_context, timeout=10) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    err = await response.read()
                    print(f"❌ GetLoginData failed [{response.status}]: {err}")
                    return None
    except Exception as e:
        print(f"❌ GetLoginData error: {e}")
        return None

async def DecryptMajorLogin(MajoRLoGinResPonsE):
    proto = MajorLoginRes_pb2.MajorLoginRes()
    proto.ParseFromString(MajoRLoGinResPonsE)
    return proto

async def DecryptLoginData(LoGinDaTa):
    proto = LoginData_pb2.GetLoginData()
    proto.ParseFromString(LoGinDaTa)
    return proto

async def DecodeWhisperMessage(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = DecodeWhisper_pb2.DecodeWhisper()
    proto.ParseFromString(packet)
    return proto

async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = received_chat_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto

async def StartUpAuth(TarGeT, token, timestamp, key, iv):
    uid_hex = hex(TarGeT)[2:]
    uid_length = len(uid_hex)

    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await EnC_PacKeT(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]

    if uid_length == 9:
        headers = '0000000'
    elif uid_length == 8:
        headers = '00000000'
    elif uid_length == 10:
        headers = '000000'
    elif uid_length == 7:
        headers = '000000000'
    else:
        print('Unexpected length')
        headers = '0000000'

    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"

async def cHTypE(H):
    """Detect chat type including custom rooms"""
    if not H:
        return 'Squid'
    elif H == 1:
        return 'CLan'
    elif H == 2:
        return 'PrivaTe'
    elif H == 3:
        return 'CustomRoom'
    else:
        return 'Squid'

async def SEndMsG(H, message, Uid, chat_id, key, iv, region):
    """Send message to any chat type including custom rooms"""
    TypE = await cHTypE(H)

    if TypE == 'Squid':
        msg_packet = await xSEndMsgsQ(message, chat_id, key, iv)
    elif TypE == 'CLan':
        msg_packet = await xSEndMsg(message, 1, chat_id, chat_id, key, iv)
    elif TypE == 'PrivaTe':
        msg_packet = await xSEndMsg(message, 2, Uid, Uid, key, iv)
    else:
        msg_packet = await xSEndMsgsQ(message, chat_id, key, iv)

    return msg_packet

async def SEndPacKeT(OnLinE, ChaT, TypE, PacKeT):
    if TypE == 'ChaT' and ChaT:
        whisper_writer.write(PacKeT)
        await whisper_writer.drain()
    elif TypE == 'OnLine':
        online_writer.write(PacKeT)
        await online_writer.drain()
    else:
        return 'UnsoPorTed TypE ! >> ErrrroR (:():)' 

async def process_api_commands(key, iv, region):
    while True:
        try:
            if command_queue.empty():
                await asyncio.sleep(0.2)
                continue

            if online_writer is None:
                print("⚠ Bot not connected yet")
                await asyncio.sleep(1)
                continue

            cmd = command_queue.get()
            players = cmd["type"]
            target_uid = int(cmd["uid"])

            print(f"📢 تنفيذ أمر API -> {players} لاعبين لـ UID {target_uid}")

            P = await OpEnSq(key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', P)

            A = await cHSq(players, target_uid, key, iv, region)
            await asyncio.sleep(0.3)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', A)

            C = await SEnd_InV(players, target_uid, key, iv, region)
            await asyncio.sleep(0.3)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)

            K = await ExiT(None, key, iv)
            await asyncio.sleep(3)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', K)

            print(f"✅ تم تنفيذ الأمر لـ {target_uid}")

        except Exception as e:
            print(f"❌ خطأ في تنفيذ الأمر: {e}")
            await asyncio.sleep(1)

async def safe_send_message(chat_type, message, target_uid, chat_id, key, iv, max_retries=3, region="me"):
    """Enhanced safe send message that works with custom rooms"""
    for attempt in range(max_retries):
        try:
            if online_writer is None and whisper_writer is None:
                await asyncio.sleep(0.2)
                continue

            P = await SEndMsG(chat_type, message, target_uid, chat_id, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
            return True

        except Exception as e:
            print(f"❌ Failed to send message (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)

    return False

async def TcPOnLine(ip, port, key, iv, AutHToKen, reconnect_delay=0.5):  
    global online_writer, last_status_packet, spy
    global insquad, joining_team, whisper_writer, region  

    bot_uid = 100000000000000

    if insquad is not None:  
        insquad = None  

    if joining_team is True:  
        joining_team = False  

    online_writer = None  
    whisper_writer = None  

    while True:  
        try:  
            print(f"🔌 Connecting to {ip}:{port}...")  
            reader, writer = await asyncio.open_connection(ip, int(port))  
            online_writer = writer  

            try:  
                if not AutHToKen or len(AutHToKen) % 2 != 0:  
                    print("❌ Authentication token invalid")  
                    raise ValueError("Invalid token")  

                bytes_payload = bytes.fromhex(AutHToKen)  
                online_writer.write(bytes_payload)  
                await online_writer.drain()  

                try:  
                    first_packet = await asyncio.wait_for(reader.read(1024), timeout=3)  
                    if first_packet:  
                        data_hex = first_packet.hex()  
                except asyncio.TimeoutError:  
                    pass  

                print("✅ Authentication Token Sent")  

            except Exception as e:  
                print(f"❌ Failed to send authentication token: {repr(e)}")  
                raise e

            while True:  
                data2 = await reader.read(9999)  
                if not data2:  
                    print("❌ Connection lost")  
                    break  

                data_hex = data2.hex()

                packet_type = None  

                if 'packet_json' not in locals():
                    packet_json = None

                if data_hex.startswith("0500") and packet_json and isinstance(packet_json, dict):  
                    try:  
                        packet_type = packet_json.get('1')  

                        has_data = (
                            '5' in packet_json and
                            isinstance(packet_json['5'], dict) and
                            'data' in packet_json['5']
                        )  

                        if packet_type in (6, 7, 8, 9, 10, 11, 12):  
                            insquad = None
                            joining_team = False  

                            if has_data:  
                                try:  
                                    OwNer_UiD, CHaT_CoDe, _ = await GeTSQDaTa(packet_json)  

                                    auth_packet = await AutH_Chat(
                                        3,
                                        OwNer_UiD,
                                        CHaT_CoDe,
                                        key,
                                        iv
                                    )  

                                    if whisper_writer and online_writer:
                                        await SEndPacKeT(
                                            whisper_writer,
                                            online_writer,
                                            'ChaT',
                                            auth_packet
                                        )  

                                except Exception as e:
                                    pass  

                            continue  

                        if has_data and insquad is None:  
                            try:  
                                OwNer_UiD, CHaT_CoDe, _ = await GeTSQDaTa(packet_json)  

                                auth_packet = await AutH_Chat(
                                    3,
                                    OwNer_UiD,
                                    CHaT_CoDe,
                                    key,
                                    iv
                                )  

                                if whisper_writer and online_writer:
                                    await SEndPacKeT(
                                        whisper_writer,
                                        online_writer,
                                        'ChaT',
                                        auth_packet
                                    )  

                            except Exception as e:
                                pass  

                    except Exception as e:
                        pass  

                if insquad == True and packet_json and isinstance(packet_json, dict):  
                    try:  
                        OwNer_UiD, CHaT_CoDe, _ = await GeTSQDaTa(packet_json)  

                        auth_packet = await AutH_Chat(
                            3,
                            OwNer_UiD,
                            CHaT_CoDe,
                            key,
                            iv
                        )  

                        if whisper_writer and online_writer:
                            await SEndPacKeT(
                                whisper_writer,
                                online_writer,
                                'ChaT',
                                auth_packet
                            )  

                        joining_team = False
                        insquad = None  

                    except Exception as e:
                        pass

            try:
                if online_writer:
                    try:
                        online_writer.close()
                        await online_writer.wait_closed()
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Error closing online_writer: {e}")
            online_writer = None

            try:
                if whisper_writer:
                    try:
                        whisper_writer.close()
                        await whisper_writer.wait_closed()
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Error closing whisper_writer: {e}")
            whisper_writer = None

            insquad = None
            joining_team = False

            print(f"🔌 Disconnected from {ip}:{port}")

        except ConnectionRefusedError:
            print(f"❌ Connection refused to {ip}:{port}")

        except asyncio.TimeoutError:
            print(f"⏰ Connection timeout to {ip}:{port}")

        except Exception as e:
            print(f"❌ Error with {ip}:{port} - {e}")
            import traceback
            traceback.print_exc()

            try:
                if online_writer:
                    try:
                        online_writer.close()
                        await online_writer.wait_closed()
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Error closing online_writer: {e}")
            online_writer = None

            try:
                if whisper_writer:
                    try:
                        whisper_writer.close()
                        await whisper_writer.wait_closed()
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Error closing whisper_writer: {e}")
            whisper_writer = None

            insquad = None
            joining_team = False

        try:
            jitter = random.uniform(0.8, 1.3)
            await asyncio.sleep(reconnect_delay * jitter)
        except:
            await asyncio.sleep(1)

        reconnect_delay = min(reconnect_delay * 2, 30)
                            
async def TcPChaT(ip, port, AutHToKen, key, iv, LoGinDaTaUncRypTinG, ready_event, region, reconnect_delay=0.5):
    print(f"💬 Chat server: {region} - {ip}:{port}")

    global whisper_writer, online_writer
    global spammer_uid, spam_chat_id, spam_uid
    global chat_id, XX, uid

    while True:
        try:
            reader, writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer

            if AutHToKen:
                if isinstance(AutHToKen, str):
                    bytes_payload = bytes.fromhex(AutHToKen)
                else:
                    bytes_payload = AutHToKen
                whisper_writer.write(bytes_payload)
                await whisper_writer.drain()

            ready_event.set()

            if LoGinDaTaUncRypTinG.Clan_ID:
                clan_id = LoGinDaTaUncRypTinG.Clan_ID
                clan_compiled_data = LoGinDaTaUncRypTinG.Clan_Compiled_Data

                pK = await AuthClan(clan_id, clan_compiled_data, key, iv)
                if whisper_writer:
                    whisper_writer.write(pK)
                    await whisper_writer.drain()

            while True:
                data = await reader.read(9999)
                if not data:
                    break

                if data.hex().startswith("120000"):
                    msg = await DeCode_PackEt(data.hex()[10:])
                    chatdata = json.loads(msg)

                    try:
                        response = await DecodeWhisperMessage(data.hex()[10:])
                        uid = response.Data.uid
                        chat_id = response.Data.Chat_ID
                        XX = response.Data.chat_type
                        MsG = response.Data.msg.lower()
                    except:
                        response = None

                    if response:
                        uid = response.Data.uid
                        chat_id = response.Data.Chat_ID
                        XX = response.Data.chat_type
                        inPuTMsG = response.Data.msg.lower()
                        uid_str = str(uid)                        
                        sender_uid = str(response.Data.uid)

                        if inPuTMsG.startswith(("/3")):  
                            print(f"📩 Received /3 command from {sender_uid}")
                            initial_message = f"🎮 Cʟᴀᴛɪɴɢ 3-Pʟᴀʏᴇʀ Gʀᴏᴜᴘ..."
                            await safe_send_message(
                                response.Data.chat_type,
                                initial_message,
                                uid,
                                chat_id,
                                key,
                                iv)  

                            P = await OpEnSq(key, iv, region)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', P)  

                            A = await cHSq(3, uid, key, iv, region)  
                            await asyncio.sleep(0.3)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', A)  

                            C = await SEnd_InV(3, uid, key, iv, region)  
                            await asyncio.sleep(0.3)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)  

                            K = await ExiT(None, key, iv)  
                            await asyncio.sleep(3.5)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', K)  

                            success_message = f"✅ Gʀᴏᴜᴘ Iɴᴠɪᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!"
                            await safe_send_message(
                                response.Data.chat_type,
                                success_message,
                                uid,
                                chat_id,
                                key,
                                iv
                            )
                            print(f"✅ /3 command completed for {sender_uid}")

                        if inPuTMsG.startswith(("/5")):  
                            print(f"📩 Received /5 command from {sender_uid}")
                            initial_message = f"🎮 Cʟᴀᴛɪɴɢ 5-Pʟᴀʏᴇʀ Gʀᴏᴜᴘ..."
                            await safe_send_message(
                                response.Data.chat_type,
                                initial_message,
                                uid,
                                chat_id,
                                key,
                                iv)  

                            P = await OpEnSq(key, iv, region)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', P)  

                            A = await cHSq(5, uid, key, iv, region)  
                            await asyncio.sleep(0.3)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', A)  

                            C = await SEnd_InV(5, uid, key, iv, region)  
                            await asyncio.sleep(0.3)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)  

                            K = await ExiT(None, key, iv)  
                            await asyncio.sleep(3.5)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', K)  

                            success_message = f"✅ Gʀᴏᴜᴘ Iɴᴠɪᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!"
                            await safe_send_message(
                                response.Data.chat_type,
                                success_message,
                                uid,
                                chat_id,
                                key,
                                iv
                            )
                            print(f"✅ /5 command completed for {sender_uid}")

                        if inPuTMsG.startswith(("/6")):  
                            print(f"📩 Received /6 command from {sender_uid}")
                            initial_message = f"🎮 Cʟᴀᴛɪɴɢ 6-Pʟᴀʏᴇʀ Gʀᴏᴜᴘ..."
                            await safe_send_message(
                                response.Data.chat_type,
                                initial_message,
                                uid,
                                chat_id,
                                key,
                                iv)  

                            P = await OpEnSq(key, iv, region)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', P)  

                            A = await cHSq(6, uid, key, iv, region)  
                            await asyncio.sleep(0.3)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', A)  

                            C = await SEnd_InV(6, uid, key, iv, region)  
                            await asyncio.sleep(0.3)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)  

                            K = await ExiT(None, key, iv)  
                            await asyncio.sleep(3.5)  
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', K)  

                            success_message = f"✅ Gʀᴏᴜᴘ Iɴᴠɪᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!"
                            await safe_send_message(
                                response.Data.chat_type,
                                success_message,
                                uid,
                                chat_id,
                                key,
                                iv
                            )
                            print(f"✅ /6 command completed for {sender_uid}")

                        response = None
                            
            whisper_writer.close()
            await whisper_writer.wait_closed()
            whisper_writer = None
                    	
        except Exception as e:
            print(f"❌ Chat error {ip}:{port} - {e}")
            whisper_writer = None
        await asyncio.sleep(reconnect_delay)

# ======================== MAIN BOT FUNCTION ========================
async def MaiiiinE(account):
    global online_writer, whisper_writer, region, bot_ready, current_session_account
    
    current_session_account = account
    
    print(f"\n{'='*60}")
    print(f"🚀 STARTING BOT FOR ACCOUNT: {account['uid']}")
    print(f"{'='*60}")

    Uid = account['uid']
    Pw = account['password']

    print(f"🔑 UID: {Uid}")

    print("\n🔐 Generating authentication tokens...")

    open_id, access_token = await GeNeRaTeAccEss(Uid, Pw)
    if not open_id or not access_token:
        print(f"❌ Error - Invalid Account {Uid} (Check UID/Password)")
        return False

    print("✅ Access token generated")

    PyL = await EncRypTMajoRLoGin(open_id, access_token)
    MajoRLoGinResPonsE = await MajorLogin(PyL)

    if not MajoRLoGinResPonsE:
        print(f"❌ Account {Uid} => Banned / Not Registered!")
        return False

    MajoRLoGinauTh = await DecryptMajorLogin(MajoRLoGinResPonsE)
    token = MajoRLoGinauTh.token

    if not token:
        print(f"❌ No authentication token received for {Uid}!")
        return False

    UrL = MajoRLoGinauTh.url

    try:
        print(render('RIZER', colors=['white', 'blue'], align='center'))
    except:
        pass

    region = MajoRLoGinauTh.region
    ToKen = token
    TarGeT = MajoRLoGinauTh.account_uid
    key = MajoRLoGinauTh.key
    iv = MajoRLoGinauTh.iv
    timestamp = MajoRLoGinauTh.timestamp

    print("\n📡 Fetching server connection data...")

    LoGinDaTa = await GetLoginData(UrL, PyL, ToKen)
    if not LoGinDaTa:
        print(f"❌ Error - Getting Ports From Login Data for {Uid}!")
        return False

    LoGinDaTaUncRypTinG = await DecryptLoginData(LoGinDaTa)

    OnLinePorTs = LoGinDaTaUncRypTinG.Online_IP_Port
    ChaTPorTs = LoGinDaTaUncRypTinG.AccountIP_Port

    print(f"📡 Online Server : {OnLinePorTs}")
    print(f"💬 Chat Server   : {ChaTPorTs}")

    OnLineiP, OnLineporT = OnLinePorTs.split(":")
    ChaTiP, ChaTporT = ChaTPorTs.split(":")

    acc_name = LoGinDaTaUncRypTinG.AccountName
    print(f"\n👋 Welcome, {acc_name}!")

    AutHToKen = await StartUpAuth(
        int(TarGeT),
        ToKen,
        int(timestamp),
        key,
        iv
    )

    ready_event = asyncio.Event()

    print("\n🚀 Starting bot services...")

    api_task = asyncio.create_task(
        process_api_commands(key, iv, region)
    )

    task1 = asyncio.create_task(
        TcPOnLine(
            OnLineiP,
            OnLineporT,
            key,
            iv,
            AutHToKen
        )
    )

    task2 = asyncio.create_task(
        TcPChaT(
            ChaTiP,
            ChaTporT,
            AutHToKen,
            key,
            iv,
            LoGinDaTaUncRypTinG,
            ready_event,
            region
        )
    )

    print()
    print("═"*60)
    print(f"│➤  UID        = {TarGeT}")
    print(f"│➤  NAME       = {acc_name}")
    print(f"│➤  REGION     = {region}")
    print(f"│➤  CHAT IP    = {ChaTiP}:{ChaTporT}")
    print(f"│➤  ONLINE IP  = {OnLineiP}:{OnLineporT}")
    print("═"*60)
    print()

    bot_ready = True

    try:
        await asyncio.gather(task1, task2, api_task)
    except asyncio.CancelledError:
        print("\n🔄 TOKEN EXPIRED — SWITCHING TO NEXT ACCOUNT...")
    except Exception as e:
        print(f"\n❌ ERROR DURING BOT EXECUTION: {e}")
        import traceback
        traceback.print_exc()
    
    bot_ready = False
    return True

# ======================== MULTI-ACCOUNT MANAGER ========================
async def run_account_with_timeout(account, timeout):
    """Run a single account with timeout, return True if successful"""
    try:
        await asyncio.wait_for(MaiiiinE(account), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        print(f"⏰ Account {account['uid']} timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"⚠️ Account {account['uid']} failed: {e}")
        return False

async def StarTinG():
    global accounts_list, current_account_index, total_accounts_loaded
    
    accounts_list = load_accounts_from_file("bot.txt")
    total_accounts_loaded = len(accounts_list)
    
    if not accounts_list:
        print("❌ No accounts to run. Exiting...")
        return

    print(f"\n{'='*60}")
    print(f"🔄 MULTI-ACCOUNT MODE ENABLED")
    print(f"📊 Total accounts loaded: {len(accounts_list)}")
    print(f"🎯 MODE: كل أمر يغير الحساب تلقائياً")
    print(f"{'='*60}\n")

    rotation_count = 0
    
    while True:
        account = accounts_list[current_account_index]
        rotation_count += 1
        
        print(f"\n{'🟢'*30}")
        print(f"🔄 ROTATION #{rotation_count}")
        print(f"➡️  SWITCHING TO ACCOUNT {current_account_index + 1}/{len(accounts_list)}")
        print(f"🔑 UID: {account['uid']}")
        print(f"{'🟢'*30}\n")
        
        success = await run_account_with_timeout(account, TOKEN_EXPIRY)
        
        if not success:
            print(f"⚠️ Account {account['uid']} had issues, moving to next...")
        else:
            print(f"✅ Account {account['uid']} completed successfully")
        
        # Move to next account
        old_index = current_account_index
        current_account_index = (current_account_index + 1) % len(accounts_list)
        
        print(f"\n🔄 Moving from account {old_index + 1} to account {current_account_index + 1}")
        
        # Wait a bit before switching accounts
        print(f"⏱️ Waiting 5 seconds before switching...")
        await asyncio.sleep(5)

# ======================== FLASK SERVER ========================
def run_flask():
    app.run(
        host="0.0.0.0",
        port=5881,
        debug=False,
        threaded=True
    )

# ======================== MAIN ENTRY POINT ========================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🔫 FREE FIRE MULTI-ACCOUNT SQUAD INVITE BOT 🤖               ║
║                                                                  ║
║  ✨ Features:                                                    ║
║  ✅ Multiple accounts from single bot.txt file                   ║
║  ✅ 🔄 AUTO SWITCH PER COMMAND - كل أمر يغير الحساب              ║
║  ✅ Auto-switch on failure/ban                                   ║
║  ✅ Flask API on port 5881                                       ║
║  ✅ Commands: /3, /5, /6 (in-game)                              ║
║  ✅ API endpoints: /3, /5, /6, /switch_account, /accounts       ║
║                                                                  ║
║  📝 Format bot.txt:                                              ║
║  uid=1234567890,password=your_password                          ║
║  uid=0987654321,password=another_password                       ║
║                                                                  ║
║  🌐 API Base URL: http://localhost:5881                         ║
║                                                                  ║
║  ⚡ كل أمر من API يغير الحساب تلقائياً ⚡                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Create template if bot.txt doesn't exist
    if not os.path.exists("bot.txt"):
        create_credentials_template()
        print("\n⚠️ Please edit bot.txt with your account credentials before running!")
        print("⚠️ Format: uid=YOUR_UID,password=YOUR_PASSWORD")
        input("\nPress Enter to exit...")
        exit()
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask API running on http://localhost:5881")
    print("📋 Available endpoints:")
    print("   GET /                - API info")
    print("   GET /status          - Bot status")
    print("   GET /accounts        - List all accounts")
    print("   GET /switch_account  - Switch to next account")
    print("   GET /3?uid=XXX       - Invite to 3-player squad (يغير الحساب تلقائياً)")
    print("   GET /5?uid=XXX       - Invite to 5-player squad (يغير الحساب تلقائياً)")
    print("   GET /6?uid=XXX       - Invite to 6-player squad (يغير الحساب تلقائياً)")
    print()
    print("⚡ IMPORTANT: كل أمر من API يغير الحساب تلقائياً للحساب التالي ⚡")
    print()
    
    # Run main bot
    try:
        asyncio.run(StarTinG())
    except KeyboardInterrupt:
        print("\n\n⚠️ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")