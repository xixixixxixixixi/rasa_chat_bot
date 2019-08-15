# -*- coding: utf-8 -*-
"""
用于将语音消息转化为TEXT
"""
from aip import AipSpeech

""" 你的 APPID AK SK """
APP_ID = '16604772'
API_KEY = 'D0UkKHRU8oTGxmqm8AzFAZN3'
SECRET_KEY = 'IM6p0oKQf3igtsWQ7E7OcI15isj1blQF'

client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
# 读取文件
def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()


def get_voice_text():
    # 识别本地文件
    x=client.asr(get_file_content('result.pcm'), 'pcm', 16000, {'dev_pid': 1737,})
    print(x)
    x=x["result"][0]
    return x
