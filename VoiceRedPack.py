import os
from PIL import Image
import requests
import json
import base64
import urllib
from aip import AipSpeech
from mutagen.mp3 import MP3
import math
import playsound
import time


# 都是百度的
APPID = '?'
APIKey = '?'
SecretKey = '?'


def get_request_url():
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + APIKey + '&client_secret=' + SecretKey
    at_content = requests.get(host)
    at = json.loads(at_content.text)["access_token"]
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=" + at
    return request_url


def get_screenshot():
    os.system('adb shell screencap -p /sdcard/pictures/Screenshots/Screenshot_Redpack.png')
    os.system('adb pull /sdcard/pictures/Screenshots/Screenshot_Redpack.png Screenshot.png')


def screenshot_process():
    global simClickPosX
    global simClickPosY
    global simHoldPosX
    global simHoldPosY
    img = Image.open('Screenshot.png')
    if img.size == (1440, 2880):
        cutsize = (191, 1575, 1252, 2312)
        simClickPosX = '1000' # your own red pack --> X=300
        simClickPosY = '2000'
        simHoldPosX = '750'
        simHoldPosY = '1700'
    elif img.size == (1080, 1920):
        cutsize = (130, 1150, 950, 1480)
        simClickPosX = '300'
        simClickPosY = '1330'

        simHoldPosX = '550'
        simHoldPosY = '1150'

    after_cut = img.crop(cutsize)
    after_cut.save('Screenshot_Redpack.png')


def ocr_result():
    request_url = get_request_url()
    f = open('Screenshot_Redpack.png', 'rb')
    img_encode = base64.b64encode(f.read())
    params = urllib.parse.urlencode({"image": img_encode})
    r_json = requests.post(request_url, params).json()
    word_list = r_json.get('words_result')
    result_list = list()
    for i in word_list:
        result_list.append(i.get('words'))
    result_str = ' '.join(result_list)
    print(result_str)
    return result_str


def gen_audio(ocrResult):
    aipSpeech = AipSpeech(APPID, APIKey, SecretKey)
    result = aipSpeech.synthesis(ocrResult, 'zh', '1', {
        'vol': 8,
        'per': 1,
        'spd': 3
    })
    if not isinstance(result, dict):
        with open('ocr.mp3', 'wb') as f:
            f.write(result)


def simClick():
    audioForMutagen = MP3('ocr.mp3')
    audiolenth = str(math.ceil(audioForMutagen.info.length) * 1000)
    os.system('adb shell input tap ' + simClickPosX + " " + simClickPosY)
    os.popen(
        'adb shell input swipe ' + simHoldPosX + " " + simHoldPosY + " " + simHoldPosX + " " + simHoldPosY + " " + audiolenth)
    time.sleep(0.5)
    playsound.playsound('ocr.mp3')


get_screenshot()
screenshot_process()
WordsInRedPack = ocr_result()
gen_audio(WordsInRedPack)
simClick()