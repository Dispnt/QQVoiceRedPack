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
# tkinter/sqlite 部分
import tkinter
import tkinter.messagebox
import sqlite3


# 都是百度的
APPID = '?'
APIKey = '?'
SecretKey = '?'


def get_request_url():
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + APIKey + '&client_secret=' + SecretKey
    at_content = requests.get(host)  # 请求一个含有access_token的json
    at = json.loads(at_content.text)["access_token"]  # 解析json内access_token属性的值
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=" + at  # 拼接api请求的网页
    return request_url


def get_screenshot():
    os.system('adb shell screencap -p /sdcard/pictures/Screenshots/Screenshot_Redpack.png')  # adb命令截图
    os.system('adb pull /sdcard/pictures/Screenshots/Screenshot_Redpack.png Screenshot.png')  # adb命令发到电脑


def screenshot_process():
    global simClickPosX
    global simClickPosY
    global simHoldPosX
    global simHoldPosY  # 函数内定义全局变量
    img = Image.open('Screenshot.png')
    if img.size == (1440, 2880):  # 如果是2k屏
        cutsize = (191, 1575, 1252, 2312)  # 剪剩的坐标
        simClickPosX = '300' # 自己领自己红包的x坐标是1000
        simClickPosY = '2000'  # 点击红包的X,Y坐标
        simHoldPosX = '750'
        simHoldPosY = '1700'  # 长按讲话按钮的X,Y坐标
    elif img.size == (1080, 1920):  # 如果是1080p，同上
        cutsize = (130, 1150, 950, 1480)
        simClickPosX = '300'
        simClickPosY = '1330'
        simHoldPosX = '550'
        simHoldPosY = '1150'

    after_cut = img.crop(cutsize)  # 剪掉图片
    after_cut.save('Screenshot_Redpack.png')  # 然后保存

    textStatus.insert(1.0, '截图大小' + str(img.size) + '\n剪贴大小:' + str(cutsize))  # tkinter的文本框插入文字


def ocr_result():
    request_url = get_request_url()  # 带Access Token的api请求url

    f = open('Screenshot_Redpack.png', 'rb')  # 打开图片
    img_encode = base64.b64encode(f.read())  # base64 编码
    params = urllib.parse.urlencode({"image": img_encode})  # 进行 urlencode
    r_json = requests.post(request_url, params).json()  # post
    print(r_json)
    word_list = r_json.get('words_result')  # word_list变量里是json数组
    result_list = list()  # 一个叫result_list的列表
    for i in word_list:  # 对word_list里的每个键值对要...
        result_list.append(i.get('words'))  # 要在ocrlist内插入words属性的值
    result_str = ' '.join(result_list)  # stackoverflow上找到的把列表转换为字符串的方法
    print(result_str)
    textStatus.insert(1.0, '识别内容:' + result_str + '\n')  # tkinter的文本框插入文字
    return result_str


def gen_audio(ocrResult):
    aipSpeech = AipSpeech(APPID, APIKey, SecretKey)
    result = aipSpeech.synthesis(ocrResult, 'zh', '1', {
        'vol': 8,
        'per': 1,
        'spd': 3
    })
    if not isinstance(result, dict):
        with open('ocr.mp3', 'wb') as f:  # 结果写进mp3文件里
            f.write(result)


def simclick():
    audioForMutagen = MP3('ocr.mp3')  # ocr.mp3现在是一个Mutagen的mp3文件
    audiolenth = str(math.ceil(audioForMutagen.info.length) * 1000)  # 向上取整ocr.mp3的时长用来当作模拟按住说话的时间
    os.system('adb shell input tap ' + simClickPosX + " " + simClickPosY)  # adb命令模拟点击红包部分
    os.popen(
        'adb shell input swipe ' + simHoldPosX + " " + simHoldPosY + " " + simHoldPosX + " " + simHoldPosY + " " + audiolenth)
    # adb命令模拟按住说话 os.popen函数能够不等待shell命令完成继续下面的操作
    time.sleep(0.5)  # 等0.5秒，长按可能会有延迟
    playsound.playsound('ocr.mp3')  # 播放声音，不用教过的pygame放的原因是因为那东西太洋气了调不来音调... 

    # os.system('adb push '+ 'ocr.mp3 ' + '/sdcard/Android/media')
    # os.system('adb shell am start -a "android.intent.action.VIEW" -t "audio/mp3" -d '+ 'file://storage/emulated/0/Android/media/ocr.mp3')

    textStatus.insert(1.0, '音频时长(s)' + str(
        audioForMutagen.info.length) + '\n' + '按住时间(ms):' + audiolenth + '\n')  # tkinter的文本框插入文字


def mainAction():  # 劈里啪啦全部倒出来
    get_screenshot()
    screenshot_process()
    WordsInRedPack = ocr_result()
    gen_audio(WordsInRedPack)
    simclick()


# ---------------tkinter部分

def validate():
    id = varStuID.get()  # id变量是varStuID这个StringVar里来的，下同
    pwd = varPwd.get()
    conn = sqlite3.connect('RedPack.sqlite')  # 连接数据库文件
    crsr = conn.cursor()  # 建立游标
    crsr.execute("select * from UserInfo where StuID='" + id + "'")  # 在UserInfo表中找到StuID
    rs = crsr.fetchone()  # 返回找到的第一条记录
    if rs != None:  # 如果找到StuID的话
        if pwd == rs[1]:  # 如果密码对的话
            top.destroy()  # 登录框没有了
            tkinter.messagebox.showinfo('欢迎', '欢迎,' + rs[2])  # 当然是欢迎的提示
            # bgImage(root, 'bglogined.png') # 换背景图片
        else:  # 如果密码不对
            tkinter.messagebox.showerror('不对', '密码错辣')  # 跳密码错的提示，下同
            entryName.focus_set()  # 焦点在varStuID的那个框，下同
    else:  # 
        tkinter.messagebox.showerror('不对', '用户名错辣')
        entryName.focus_set()
    varStuID.set('')  # 清空varStuID框框
    varPwd.set('')  # 清空varPwd的框框


def login():
    global top, entryName, varStuID, varPwd
    top = tkinter.Toplevel()
    top.title('用DB Browser填的数据库里找密码。。。')
    top.geometry('400x150+' + str(root.winfo_width() // 3) + '+' + str(root.winfo_height() // 3))
    top.resizable(0, 0)
    labelName = tkinter.Label(top, text='Username：')
    labelName.place(x=10, y=10)
    labelNameIs = tkinter.Label(top, text='用户名是:username')
    labelNameIs.place(x=230, y=10)
    labelPwd = tkinter.Label(top, text='Password：')
    labelPwd.place(x=10, y=40)
    labelPwdIs = tkinter.Label(top, text='密码是:pwd')
    labelPwdIs.place(x=10, y=120)
    varStuID = tkinter.StringVar(top, value='')
    varPwd = tkinter.StringVar(top, value='')
    entryName = tkinter.Entry(top, textvariable=varStuID, width=18)
    entryName.place(x=80, y=10)
    entryPwd = tkinter.Entry(top, textvariable=varPwd, width=18, show='*')
    entryPwd.place(x=80, y=40)
    buttonLogin = tkinter.Button(top, text='登录', command=validate)
    buttonLogin.place(x=50, y=80)
    buttonCancel = tkinter.Button(top, text='取消', command=top.destroy)
    buttonCancel.place(x=120, y=80)
    entryName.focus_set()
    top.focus_set()
    top.grab_set()
    top.wait_window()


def putWidget():
    submenu1 = tkinter.Menu(mainMenu, tearoff=0)
    submenu1.add_command(label='登录(L)', underline=3, command=login)
    submenu1.add_command(label='注册(R)', underline=3)
    submenu1.add_command(label='注销(O)', underline=3)
    submenu1.add_separator()
    submenu1.add_command(label='退出(E)', underline=3, command=quit)

    submenu2 = tkinter.Menu(mainMenu, tearoff=0)

    manualMenu = tkinter.Menu(submenu2, tearoff=0)
    manualMenu.add_command(label='最一开始不带tkinter时候用的(A)', underline=18, command=mainAction)
    manualMenu.add_command(label='这个是因为说要带tkinter分高才草草加了两句的tkinter版本(B)', underline=35, command=mainActionGUI)

    submenu2.add_cascade(label='完整程序(C)', underline=5, menu=manualMenu)
    submenu2.add_separator()
    submenu2.add_command(label='get_screenshot()')
    submenu2.add_command(label='ocr_result()')
    submenu2.add_command(label='gen_audio()')
    submenu2.add_command(label='simclick()')

    submenu4 = tkinter.Menu(mainMenu, tearoff=0)
    submenu4.add_command(label='使用方法', command=howtouse)
    submenu4.add_command(label='关于')

    mainMenu.add_cascade(label='账号(A)', underline=3, menu=submenu1)
    mainMenu.add_cascade(label='这里才是主要的(M)', underline=8, menu=submenu2)
    mainMenu.add_cascade(label='帮助', menu=submenu4)
    root['menu'] = mainMenu


def bgImage(window, fileName):
    background_image = tkinter.PhotoImage(file=fileName)
    background_label = tkinter.Label(window, image=background_image)
    background_label.image = background_image
    background_label.place(x=0, y=0, relwidth=1, relheight=1)


def mainActionGUI():
    textStatus.place(x=0, y=0)
    mainAction()


def howtouse():
    howtouse = tkinter.Toplevel()
    howtouse.title('How to Use')
    howtouse.geometry('800x600')
    howtouse.resizable(0, 0)
    bgImage(howtouse, 'howtouse.png')


root = tkinter.Tk()  # 新建root窗口
root.title('QQ，语音红包ocr')  # root窗口标题
root.geometry('800x600')  # root窗口大小
root.resizable(0, 0)  # root窗口不能拖动

bgImage(root, 'bglogin.png')  # root窗口背景
textStatus = tkinter.Text(root, width=800, height=600)  # root窗口里的文本框
mainMenu = tkinter.Menu(root)  # 菜单栏
putWidget()  # 放控件
login()  # 登陆函数

root.mainloop()