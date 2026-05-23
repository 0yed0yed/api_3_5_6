#! PACKET MANAGER MODULE
#`````ＩＭＰＯＲＴＳ`````

import ujson as json
import binascii
import base64
import time
import socket
import random
import asyncio
import datetime

#ＰＲＯＴＯ－ＩＭＰＯＲＴＳ

from protobuf_decoder.protobuf_decoder import Parser
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime


Key , Iv = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56]) , bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])


async def EnC_AEs(HeX):
    cipher = AES.new(Key , AES.MODE_CBC , Iv)
    return cipher.encrypt(pad(bytes.fromhex(HeX), AES.block_size)).hex()
    

async def DEc_AEs(HeX):
    cipher = AES.new(Key , AES.MODE_CBC , Iv)
    return unpad(cipher.decrypt(bytes.fromhex(HeX)), AES.block_size).hex()
    

async def EnC_PacKeT(HeX , K , V): 
    return AES.new(K , AES.MODE_CBC , V).encrypt(pad(bytes.fromhex(HeX) ,16)).hex()
    

async def DEc_PacKeT(HeX , K , V):
    return unpad(AES.new(K , AES.MODE_CBC , V).decrypt(bytes.fromhex(HeX)) , 16).hex()  


async def EnC_Uid(H , Tp):
    e , H = [] , int(H)
    while H:
        e.append((H & 0x7F) | (0x80 if H > 0x7F else 0)) ; H >>= 7
    return bytes(e).hex() if Tp == 'Uid' else None


async def EnC_Vr(N):
    if N < 0: ''
    H = []
    while True:
        Xrohit = N & 0x7F ; N >>= 7
        if N: Xrohit |= 0x80
        H.append(Xrohit)
        if not N: break
    return bytes(H)
 
       
def DEc_Uid(H):
    n = s = 0
    for b in bytes.fromhex(H):
        n |= (b & 0x7F) << s
        if not b & 0x80: break
        s += 7
    return n

    
async def CrEaTe_VarianT(field_number, value):
    field_header = (field_number << 3) | 0
    return await EnC_Vr(field_header) + await EnC_Vr(value)


async def CrEaTe_LenGTh(field_number, value):
    field_header = (field_number << 3) | 2
    encoded_value = value.encode() if isinstance(value, str) else value
    return await EnC_Vr(field_header) + await EnC_Vr(len(encoded_value)) + encoded_value


async def CrEaTe_ProTo(fields):
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested_packet = await CrEaTe_ProTo(value)
            packet.extend(await CrEaTe_LenGTh(field, nested_packet))
        elif isinstance(value, int):
            packet.extend(await CrEaTe_VarianT(field, value))
        elif isinstance(value, str) or isinstance(value, bytes):
            packet.extend(await CrEaTe_LenGTh(field, value))
    return packet

    
async def DecodE_HeX(H):
    R = hex(H) 
    F = str(R)[2:]
    if len(F) == 1: F = "0" + F ; return F
    else: return F


async def Fix_PackEt(parsed_results):
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data['wire_type'] = result.wire_type
        if result.wire_type == "varint":
            field_data['data'] = result.data
        if result.wire_type == "string":
            field_data['data'] = result.data
        if result.wire_type == "bytes":
            field_data['data'] = result.data
        elif result.wire_type == 'length_delimited':
            field_data["data"] = await Fix_PackEt(result.data.results)
        result_dict[result.field] = field_data
    return result_dict


async def DeCode_PackEt(input_text):
    try:
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = await Fix_PackEt(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}")
        return None


async def GeneRaTePk(Pk, N, K, V):
    PkEnc = await EnC_PacKeT(Pk, K, V)
    length_hex = await DecodE_HeX(int(len(PkEnc) // 2))

    if len(length_hex) == 2:
        HeadEr = N + "000000"
    elif len(length_hex) == 3:
        HeadEr = N + "00000"
    elif len(length_hex) == 4:
        HeadEr = N + "0000"
    elif len(length_hex) == 5:
        HeadEr = N + "000"
    else:
        print('ErroR => FuCk GeneRatinG PacKeT !! ')

    return bytes.fromhex(HeadEr + length_hex + PkEnc)


async def AuthClan(CLan_Uid, AuTh, K, V):

    fields = {
        1: 3,
        2: {
            1: int(CLan_Uid),
            2: 1,
            4: str(AuTh)
        }
    }

    proto_packet = await CrEaTe_ProTo(fields)

    proto_hex = proto_packet.hex()

    final_packet = await GeneRaTePk(
        proto_hex,
        '1201',
        K,
        V
    )

    return final_packet


async def AutH_Chat(T , uid, code , K, V):
    fields = {
  1: T,
  2: {
    1: uid,
    3: "en",
    4: str(code)
  }
}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1215' , K , V)       


def xMsGFixinG(n):
    return '🗿'.join(str(n)[i:i + 3] for i in range(0, len(str(n)), 3))


async def ArA_CoLor():

    Tp = [
        "32CD32",
        "00BFFF",
        "00FA9A",
        "90EE90",
        "FF4500",
        "FF6347",
        "FF69B4",
        "FF8C00",
        "FF6347",
        "FFD700",
        "FFDAB9",
        "F0F0F0",
        "F0E68C",
        "D3D3D3",
        "A9A9A9",
        "D2691E",
        "CD853F",
        "BC8F8F",
        "6A5ACD",
        "483D8B",
        "4682B4",
        "9370DB",
        "C71585",
        "FF8C00",
        "FFA07A"
    ]

    selected_color = random.choice(Tp)

    return selected_color


def xAvATar():

    avatar_list = [
        902048004,
        902047018,
        902048021,
        902036021,
        902042011,
        902000074,
        902044014
    ]

    selected_avatar = random.choice(avatar_list)

    return selected_avatar


def xBaNnEr():

    banner_list = [
        901032009,
        901026021,
        901049014,
        901049003,
        901048020,
        901048010,
        901042013,
        901042014,
        901036035,
        901040006,
        901047013,
        901028017
    ]

    selected_banner = random.choice(banner_list)

    return selected_banner


async def xSEndMsg(Msg, Tp, Tp2, id, K, V):
    feilds = {
        1: id,
        2: Tp2,
        3: Tp,
        4: Msg,
        5: 1756580149,
        7: 2,
        9: {
            1: "[FFFFFF]ROHIT",
            2: int(xAvATar()),
            3: int(xBaNnEr()),
            4: 330,
            5: 827001007,
            8: "ROHIT",
            10: 1,
            11: 1,
            13: {
                1: 2
            },
            14: {
                1: 1158053040,
                2: 8,
                3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
            },
            12: 0
        },
        10: "en",
        13: {3: 1}
    }

    Pk = (await CrEaTe_ProTo(feilds)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)



async def xSEndMsgsQQ(Msg, id, K, V):

    fields = {
        1: id,
        2: id,
        4: Msg,
        5: 1756580149,
        8: 904990072,
        9: {
            1: "ROHIT - X1",
            2: int(xAvATar()),
            4: 330,
            5: 827001007,
            8: "ROHIT - X1",
            10: 1,
            11: 1,
            13: {1: 2},
            14: {
                1: 1158053040,
                2: 8,
                3: "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
            }
        },
        10: "en",
        13: {
            2: 2,
            3: 1
        }
    }

    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk

    return await GeneRaTePk(Pk, '1201', K, V)


    
async def xSEndMsgsQ(Msg , id , K , V, region="IND"):
    """Send message with region 1 title included"""
    
    fields = {
        1: id, 
        2: id, 
        4: Msg, 
        5: 1756580149, 
        8: 904990072, 
        9: {
            1: "ROHIT", 
            2: int(xAvATar()),
            4: 330, 
            5: 827001007, 
            8: "ROHIT", 
            10: 1,
            11: 1,
            13: {
                1: 2
            },
            14: {
                1: 1158053040, 
                2: 8, 
                3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
            }
        }, 
        10: "en", 
        13: {2: 2, 3: 1},
        14: {
            1: {
                1: random.choice([1, 4]),
                2: 1,
                3: random.randint(1, 180),
                4: 1,
                5: int(datetime.now().timestamp()),
                6: region
            }
        }
    }
    
    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)


async def GeT_Status(PLayer_Uid, K, V):

    PLayer_Uid = await EnC_Uid(PLayer_Uid, Tp='Uid')

    if len(PLayer_Uid) == 8:

        Pk = f'080112080a04{PLayer_Uid}1005'

    elif len(PLayer_Uid) == 10:

        Pk = f"080112090a05{PLayer_Uid}1005"

    return await GeneRaTePk(Pk, '0f15', K, V)


async def GenJoinSquadsPacket(code, K, V):
    fields = {
        1: 4,
        2: {
            4: bytes.fromhex("01090a0b121920"),
            5: str(code),
            6: 6,
            8: 1,
            9: {
                2: 800,
                6: 11,
                8: "1.122.1",
                9: 5,
                10: 1
            }
        }
    }
    proto = await CrEaTe_ProTo(fields)
    return await GeneRaTePk(proto.hex(), '0515', K, V)


async def GeTSQDaTa(D):
    try:
        data5 = D.get('5', {}).get('data', {})
        uid = data5.get('1', {}).get('data')
        chat_code = data5.get('17', {}).get('data')
        squad_code = data5.get('31', {}).get('data')
        return uid, chat_code, squad_code
    except Exception:
        return None, None, None


async def OpEnSq(K, V, region):
    fields = {
        1: 1,
        2: {
            2: "\u0001",
            3: 1,
            4: 1,
            5: "en",
            9: 1,
            11: 1,
            13: 1,
            14: {
                2: 5756,
                6: 11,
                8: "1.122.1",
                9: 2,
                10: 4
            }
        }
    }

    if region.lower() == "ind":
        packet = '0514'
    else:
        packet = "0515"

    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet, K, V)


async def cHSq(Nu, Uid, K, V, region):
    fields = {
        1: 17,
        2: {
            1: int(Uid),
            2: 1,
            3: int(Nu - 1),
            4: 62,
            5: "\u001a",
            8: 5,
            13: 329
        }
    }

    if region.lower() == "ind":
        packet = '0514'
    else:
        packet = "0515"

    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet, K, V)


async def SEnd_InV(Nu, Uid, K, V, region):
    fields = {
        1: 2,
        2: {
            1: int(Uid),
            2: region,
            4: int(Nu)
        }
    }

    if region.lower() == "ind":
        packet = '0514'
    else:
        packet = "0515"

    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet, K, V)


async def ExiT(idT, K, V):
    fields = {
        1: 7,
        2: {
            1: idT
        }
    }

    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', K, V)