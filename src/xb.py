#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/27 10:33 上午
# @File    : utils.py
import json
import time
from datetime import datetime
from hashlib import md5
import random
from typing import Union, Tuple

import requests
from Crypto.Hash import HMAC, SHA256
from pydantic import BaseModel
import random


def generate_random_str(length:int=16,upper:bool=False,only_num:bool=False):
    """
    生成一个指定长度的随机字符串
    """
    if only_num:
        base_str = "0123456789"
    else:
        base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    random_str = ''
    l = len(base_str) - 1
    for i in range(length):
        random_str += base_str[random.randint(0, l)]
    if upper:
        return random_str.upper()
    return random_str

class SignIn(BaseModel):
    pathname: str = "/"
    params: str = ""  # 例如:Action=CommitUploadInner&SpaceName=aweme&Version=2020-11-19
    accesskey_id: str
    secret_accesskey: str
    service_name: str
    method: str
    x_amz_security_token: str
    body: str = ""


class DouyinUploadHelper():
    def __init__(self, info: SignIn, x_amz_date: str = None, today_str: str = None):
        if not today_str:
            self.today_str = datetime.now().strftime("%Y%m%d")
        else:
            self.today_str = today_str
        if not x_amz_date:
            self.x_amz_date = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        else:
            self.x_amz_date = x_amz_date
        self.info = info

    def _get_canonical_headers(self):
        if self.info.method.upper() == "POST" and self.info.body:
            return f"x-amz-content-sha256:{self._sha256(self.info.body)}\n" \
                   f"x-amz-date:{self.x_amz_date}\nx-amz-security-token:{self.info.x_amz_security_token}\n"
        else:
            return f"x-amz-date:{self.x_amz_date}\n" \
                   f"x-amz-security-token:{self.info.x_amz_security_token}\n"

    def _get_canonical_headers_fields(self):
        if self.info.method.upper() == "POST" and self.info.body:
            return "x-amz-content-sha256;x-amz-date;x-amz-security-token"
        else:
            return "x-amz-date;x-amz-security-token"

    def _get_hash_body(self):
        if self.info.method.upper() == "POST":
            return self._sha256(self.info.body)
        elif self.info.method.upper() == "GET":
            return self._sha256("")

    @classmethod
    def get_service_name_by_request_url(cls, url):
        # 就两种
        if 'image' in url:
            return 'imagex'
        else:
            return 'vod'

    def get_sign(self):
        info = self.info
        today_str = self.today_str
        secretAccessKey = info.secret_accesskey
        key1 = "AWS4" + secretAccessKey
        h1, _ = self._hmacsha256(key1, today_str)
        print("h1:", _)
        h2, _ = self._hmacsha256(h1, "cn-north-1")
        print("h2:", _)
        h3, _ = self._hmacsha256(h2, info.service_name)
        print("h3:", _)
        h4, _ = self._hmacsha256(h3, "aws4_request")
        print("h4:", _)
        sha256_message_list = [
            info.method.upper(),
            info.pathname,
            info.params,
            self._get_canonical_headers(),
            self._get_canonical_headers_fields(),
            self._get_hash_body()
        ]
        sha256_message = "\n".join(sha256_message_list)
        print("sha256_message:", sha256_message)
        # sha256_message = f"""GET\n/\nAction={info.action}&FileSize={info.filesize}&FileType={info.file_type}&IsInner={info.is_inner}&SpaceName={info.space_name}&Version={info.version}&app_id={info.app_id}&s={info.s}&user_id={info.user_id}\nx-amz-date:{info.x_amz_date}\nx-amz-security-token:{info.x_amz_security_token}\n\nx-amz-date;x-amz-security-token\ne3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"""
        # sha256_message = f"""GET\n/\nAction={info.action}&IsInner={info.is_inner}&SpaceName={info.space_name}&Version={info.version}&app_id={info.app_id}&s={info.s}&user_id={info.user_id}\nx-amz-date:{info.x_amz_date}\nx-amz-security-token:{info.x_amz_security_token}\n\nx-amz-date;x-amz-security-token\ne3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"""
        m5_message = f"AWS4-HMAC-SHA256\n{self.x_amz_date}\n{self.today_str}/cn-north-1/{info.service_name}/aws4_request\n{SHA256.new(sha256_message.encode('utf8')).hexdigest()}"
        print("m5_message:", m5_message)
        h5, sign = self._hmacsha256(h4, m5_message)
        print("h5:", sign)
        return sign

    def _sha256(self, message):
        return SHA256.new(message.encode('utf8')).hexdigest()

    def _hmacsha256(self, secret: Union[HMAC.HMAC, str], message: str) -> Tuple[HMAC.HMAC, str]:
        if isinstance(secret, str):
            hmac = HMAC.new(secret.encode('utf8'), digestmod=SHA256)
        else:
            hmac = HMAC.new(secret.digest(), digestmod=SHA256)
        hmac.update(message.encode('utf8'))
        return hmac, hmac.hexdigest()

    @classmethod
    def get_upload_info(cls, cookie):
        """
        获取三个参数
        ak, secret_access_key, session_token
        :return:
        """
        headers = {
            'authority': 'creator.douyin.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'cookie': cookie,
            'dnt': '1',
            'pragma': 'no-cache',
            'referer': 'https://creator.douyin.com/creator-micro/content/publish',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
        url = "https://creator.douyin.com/web/api/media/upload/auth/v5/?cookie_enabled=true&screen_width=1280&screen_height=800&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F109.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&aid=1128"
        response = requests.get(url, headers=headers)
        status_code = response.json().get('status_code')
        if status_code == 0:
            info = json.loads(response.json().get("auth"))
            secret_access_key = info.get('SecretAccessKey')
            session_token = info.get('SessionToken')
            ak = info.get('AccessKeyID')
            return True,"success", ak, secret_access_key, session_token
        else:
            return False,response.json().get('status_msg'),"","",""







def s(aa, bb):
    q = [0, 0, 0]
    q[0] = int(aa / 256) & 255
    q[1] = aa % 256 & 255
    q[2] = bb % 256 & 255
    return ''.join(map(chr, q))


def K(aa, z):
    Q = list(range(256))
    c = 0
    P = ""
    y = 0
    while y < 256:
        c = (c + Q[y] + ord(aa[y % len(aa)])) % 256
        I = Q[y]
        Q[y] = Q[c]
        Q[c] = I
        y += 1
    d = 0
    c = 0
    D = 0
    while D < len(z):
        d = (d + 1) % 256
        c = (c + Q[d]) % 256
        I = Q[d]
        Q[d] = Q[c]
        Q[c] = I
        P += chr(ord(z[D]) ^ Q[(Q[d] + Q[c]) % 256])
        D += 1
    return P


def M(aa=''):
    r = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None, None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, None,
         None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
         None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
         None, None, 10, 11, 12, 13, 14, 15]
    j = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "0a", "0b", "0c", "0d", "0e", "0f", "10", "11",
         "12", "13", "14", "15", "16", "17", "18", "19", "1a", "1b", "1c", "1d", "1e", "1f", "20", "21", "22", "23",
         "24", "25", "26", "27", "28", "29", "2a", "2b", "2c", "2d", "2e", "2f", "30", "31", "32", "33", "34", "35",
         "36", "37", "38", "39", "3a", "3b", "3c", "3d", "3e", "3f", "40", "41", "42", "43", "44", "45", "46", "47",
         "48", "49", "4a", "4b", "4c", "4d", "4e", "4f", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
         "5a", "5b", "5c", "5d", "5e", "5f", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "6a", "6b",
         "6c", "6d", "6e", "6f", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "7a", "7b", "7c", "7d",
         "7e", "7f", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "8a", "8b", "8c", "8d", "8e", "8f",
         "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "9a", "9b", "9c", "9d", "9e", "9f", "a0", "a1",
         "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "aa", "ab", "ac", "ad", "ae", "af", "b0", "b1", "b2", "b3",
         "b4", "b5", "b6", "b7", "b8", "b9", "ba", "bb", "bc", "bd", "be", "bf", "c0", "c1", "c2", "c3", "c4", "c5",
         "c6", "c7", "c8", "c9", "ca", "cb", "cc", "cd", "ce", "cf", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
         "d8", "d9", "da", "db", "dc", "dd", "de", "df", "e0", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "e9",
         "ea", "eb", "ec", "ed", "ee", "ef", "f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "fa", "fb",
         "fc", "fd", "fe", "ff"]
    l = len(aa) >> 1
    H = l << 1
    U = list(range(l))
    C = 0
    B = 0
    while B < H:
        a = r[ord(aa[B])] << 4
        B += 1
        b = r[ord(aa[B])]
        B += 1
        U[C] = (a | b) & 255
        C += 1
    return U


def H(QQ, WW, EE, RR, TT, YY, UU, II, OO, PP,
      AA, SS, DD, FF, GG, HH, JJ, KK, LL):
    K = [0] * 19
    K[0] = QQ
    K[1] = AA
    K[2] = WW
    K[3] = SS
    K[4] = EE
    K[5] = DD
    K[6] = RR
    K[7] = FF
    K[8] = TT
    K[9] = GG
    K[10] = YY
    K[11] = HH
    K[12] = UU
    K[13] = JJ
    K[14] = II
    K[15] = KK
    K[16] = OO
    K[17] = LL
    K[18] = PP
    v = ''
    for i in K:
        v += chr(int(i) & 255)
    return v


def K(aa, z):
    Q = list(range(256))
    c = 0
    P = ""
    y = 0
    while y < 256:
        try:
            p = ord(aa[y % len(aa)])
        except:
            p = 0
        c = (c + Q[y] + p) % 256
        I = Q[y]
        Q[y] = Q[c]
        Q[c] = I
        y += 1
    d = 0
    c = 0
    D = 0
    while D < len(z):
        d = (d + 1) % 256
        c = (c + Q[d]) % 256
        I = Q[d]
        Q[d] = Q[c]
        Q[c] = I
        P += chr(ord(z[D]) ^ Q[(Q[d] + Q[c]) % 256])
        D += 1
    return P;


def u(aa, bb='Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe='):
    w = len(aa)
    v = ''
    for i in range(0, w, 3):
        m = ord(aa[i]) << 16 | ord(aa[i + 1]) << 8 | (ord(aa[i + 2]) & 255)
        v += bb[m >> 18 & 63]
        v += bb[m >> 12 & 63]
        v += bb[m >> 6 & 63]
        v += bb[m & 63]
    return v


def C(r):
    a = r[0] ^ int(r[1])
    for i in range(2, len(r)):
        a = a ^ r[i]
    return a


def f(aa=14, l1=[], l2=[], l3=[]):
    d = 1 / 256
    e = 1 % 256
    t_ = int(time.time())
    f = t_ >> 24 & 255
    g = t_ >> 16 & 255
    h = t_ >> 8 & 255
    i = t_ & 255
    m = random.randint(536919696 - 10000, 536919696 + 10000)
    f1 = m >> 24 & 255
    g1 = m >> 16 & 255
    h1 = m >> 8 & 255
    i1 = m & 255
    r = [64, d, e, aa, l1[14], l1[15], l2[14], l2[15], l3[14], l3[15], f, g, h, i, f1, g1, h1, i1]
    v = C(r)
    r_ = [r[i] for i in range(len(r)) if i % 2 == 0] + [v] + [r[i] for i in range(len(r)) if i % 2 == 1]
    return r_


def get_x_b(url:str, ua:str):
    data = 'd41d8cd98f00b204e9800998ecf8427e'
    Y = M(md5(bytes(M(md5(url.encode()).hexdigest()))).hexdigest())
    L = M(md5(bytes(M(md5(data.encode()).hexdigest()))).hexdigest())
    A = M(md5(u(K(s(1, 12),
                 ua),

                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=').encode()).hexdigest())
    e = f(12, Y, L, A)
    a = H(*e)
    b = K(chr(255), a)
    c = chr(2) + chr(255) + b
    d = u(c)
    return d

def build_request_url_with_xb(url:str, ua:str):
    x_b = get_x_b(url.replace(url.split('?', 1)[0] + "?", ""), ua)
    return url +  "&X-Bogus=" + x_b


def hmac_sha256_helper(key:Union[str, bytes], message:str)->HMAC.HMAC:
    h1 = HMAC.new(key, digestmod=SHA256)
    h1.update(message.encode('utf8'))
    return h1

__all__ = [get_x_b]
