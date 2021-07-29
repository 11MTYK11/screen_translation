from pathlib import WindowsPath
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font
from tkinter import simpledialog
from typing import Mapping
from PIL import Image,ImageTk,ImageDraw,ImageFont
import easyocr
import json
import os,sys
import shutil
import cv2
import numpy as np
import threading
import time,mss
import uuid
from tkinter import colorchooser
from tkinter import scrolledtext
import webview

def cv2pil(image):
    ''' OpenCV型 -> PIL型 '''
    new_image = image.copy()
    if new_image.ndim == 2:  # モノクロ
        pass
    elif new_image.shape[2] == 3:  # カラー
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
    elif new_image.shape[2] == 4:  # 透過
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGRA2RGBA)
    new_image = Image.fromarray(new_image)
    return new_image

def pil2cv(image):
    ''' PIL型 -> OpenCV型 '''
    new_image = np.array(image, dtype=np.uint8)
    if new_image.ndim == 2:  # モノクロ
        pass
    elif new_image.shape[2] == 3:  # カラー
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
    elif new_image.shape[2] == 4:  # 透過
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGBA2BGRA)
    return new_image
def cv2_putText_jp(img, text, org, color):
    x, y = org
    r,g,b = color
    colorRGB = (r, g, b)
    imgPIL = cv2pil(img)
    draw = ImageDraw.Draw(imgPIL)
    fnt = ImageFont.truetype(r'adddata\アプリ明朝UD.otf',30)
    w, h = draw.textsize(text,font=fnt)
    draw.text(xy = (x-w,y), text=str(text), fill = colorRGB,font=fnt)
    imgCV = pil2cv(imgPIL)
    return imgCV

class textDialog(simpledialog.Dialog):
    def body(self, master):
        self.attributes("-topmost",True)
        box = tk.Frame(self)
        self.showtext = scrolledtext.ScrolledText(box,font=("",20))
        self.showtext.pack(fill=tk.BOTH,expand=True)
        self.showtext.delete("1.0","end")
        self.showtext.insert("1.0",showtextdata.get())
        box.pack(fill=tk.BOTH,expand=True)
    def buttonbox(self):
        self.btn = tk.Button(self,text="翻訳する(google翻訳が開きます)",command=self.opengoogle)
        self.btn.pack(fill=tk.X,side=tk.LEFT,expand=True)
        self.btn = tk.Button(self,text="閉じる",command=self.closewin)
        self.btn.pack(fill=tk.X,side=tk.LEFT,expand=True)
        self.sizer = ttk.Sizegrip(self)
        self.sizer.pack(anchor="se",side=tk.LEFT)
    def opengoogle(self):
        if len(showtextdata.get()) >= 5000:
            messagebox.showerror("エラー","文字数が5000文字を超えているため翻訳できません")
        else:
            root.withdraw()
            self.withdraw()
            webview.create_window('翻訳画面', f'https://translate.google.com/?hl=ja&sl=auto&tl=en&text={self.showtext.get("1.0","end")}&op=translate',on_top=True)
            webview.start()
            root.deiconify()
            self.deiconify()
    def closewin(self):
        self.destroy()
global langjson,imgdata,langlist,beforelist,reader,resultjson,mojijson,afterfoto,ocrfoto
afterfoto = None
ocrfoto = None
resultjson = {}
beforelist = []
langlist = []
mojijson = {}
imgdata = None
reader = None
root = tk.Tk()
root.wm_attributes("-transparentcolor", "snow")
root.attributes("-topmost",True)
root.title("画面翻訳君")
root.geometry(f"930x{260+200}")
menuframe = tk.LabelFrame(root)
menuframe.pack(fill=tk.X)
firstx = tk.IntVar(root)
firsty = tk.IntVar(root)
secondx = tk.IntVar(root)
secondy = tk.IntVar(root)
dragset = tk.BooleanVar(root)
dragset.set(False)
hideset = tk.BooleanVar(root)
hideset.set(False)
resultset = tk.BooleanVar(root)
resultset.set(False)
langvalue = tk.StringVar(root)
langvalue.set(value=langlist)
showtextdata = tk.StringVar(root)
mainframe = tk.Frame(root)
mainframe.pack(fill=tk.BOTH,expand=True)

with open('adddata\\langs.json', mode='rt', encoding='utf-8') as file:
    langjson = json.load(file)
def doneocr():
    scanth = threading.Thread(target=doneocrth)
    scanth.setDaemon(True)
    scanth.start()
def doneocrth():
    global imgdata,langlist,langjson,beforelist,reader,resultjson,afterfoto,ocrfoto
    resultjson.clear()
    root.title("画像をスキャンしています...")
    ocrbtn.config(state="disabled")
    screenbtn.config(state="disabled")
    colorbtn.config(state="disabled")
    popupbtn.config(state="disabled")
    resultlist = []
    count = 0
    try:
        langid = []
        for data in langlist:
            langid.append(langjson[data])
        if langid == beforelist:
            print("一緒です")
        else:
            try:
                reader = easyocr.Reader(langid,gpu = False,download_enabled=True)
            except:
                import traceback
                messagebox.showerror("エラー",f"エラー\nエラー内容:{traceback.format_exc()}")
                ocrbtn.config(state="normal")
                screenbtn.config(state="normal")
                colorbtn.config(state="normal")
                popupbtn.config(state="normal")
                return None
        beforelist = langid.copy()
        sizedataw = float(sizeintw.get()/100)
        sizedatah = float(sizeinth.get()/100)
        ocrimg = imgdata.resize((int(imgdata.width*sizedataw),int(imgdata.height*sizedatah))) 
        scanimg = ocrimg.crop((firstx.get(),firsty.get(),secondx.get(),secondy.get()))
        cv2img = pil2cv(scanimg)
        img_gray = cv2.cvtColor(cv2img, cv2.COLOR_BGR2GRAY)
        result = reader.readtext(img_gray)
        for data in result:
            try:
                count += 1
                writetext = str(count)
                resultlist.append(f"{count}\n{data[1]}\n")
                datajson = {"text":str(writetext),"place":data[0][0],"rectdatax":data[0][0],"rectdatay":data[0][2]}
                resultjson.setdefault(str(uuid.uuid4()),datajson)
                cv2img = cv2_putText_jp(cv2img,str(writetext),data[0][0],(0,0,0))
            except:
                import traceback
                traceback.print_exc()
            try:
                cv2.rectangle(cv2img,data[0][0],data[0][2],(255,0,0))
            except:
                pass
        resultjson.setdefault("pasteplace",(firstx.get(),firsty.get()))
        pilimg = cv2pil(cv2img)
        copyimg = ocrimg.copy()
        copyimg.paste(pilimg,(firstx.get(),firsty.get()))
        ocrfoto = pil2cv(copyimg)
        showtextdata.set("\n".join(resultlist))
        resulttext.delete("1.0","end")
        resulttext.insert("1.0",showtextdata.get())
        sizechange("a")
        canvaschange(copyimg)
        afterfoto = scanimg
    except:
        import traceback
        traceback.print_exc()
    ocrbtn.config(state="normal")
    screenbtn.config(state="normal")
    colorbtn.config(state="normal")
    popupbtn.config(state="normal")
    root.title("画面翻訳君")
def resetocr():
    global imgdata,ocrfoto
    ocrfoto = pil2cv(imgdata)
    fotocanvas.delete("all")
    sizechange("a")
    canvaschange(imgdata)
def getscreen():
    global imgdata,resultjson,ocrfoto
    resultjson.clear()
    root.overrideredirect(1)
    root.attributes("-alpha",0)
    with mss.mss() as sct:
        moniter = sct.monitors[0]
        sct_img = sct.grab(moniter)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        imgdata = img.copy()
        canvaschange(img)
        ocrfoto = pil2cv(imgdata)
        sizechange("a")
    root.overrideredirect(0)
    root.attributes("-alpha",1.0)
def langadd():
    global langlist,langjson
    if selectlang.get() in langlist:
        pass
    else:
        try:
            langlist.append(selectlang.get())
        except:
            import traceback
            traceback.print_exc()
        langvalue.set(value=langlist)
def langdel():
    global langlist,langjson
    selected_indices = langslist.curselection()
    selected_list = [langslist.get(i) for i in selected_indices]
    for data in selected_list:
        try:
            langlist.remove(data)
        except:
            import traceback
            traceback.print_exc()
    langvalue.set(value=langlist)
def changecolor():
    global imgdata,resultjson,afterfoto
    color = colorchooser.askcolor()
    fotocanvas.delete("all")
    cv2img = pil2cv(afterfoto)
    for key in resultjson.keys():
        datajson = resultjson[key]
        try:
            try:
                cv2img = cv2_putText_jp(cv2img,str(datajson["text"]),tuple(datajson["place"]),color[0])
                cv2.rectangle(cv2img,datajson["rectdatax"],datajson["rectdatay"],color[0])
            except:
                pass
        except:
            import traceback
            traceback.print_exc()
    pilimg = cv2pil(cv2img)
    copyimg = imgdata.copy()
    copyimg.paste(pilimg,resultjson["pasteplace"])
    canvaschange(copyimg)
def sizechange(a):
    global ocrfoto
    try:
        hsize, wsize, channel = ocrfoto.shape
        sizedataw = float(sizeintw.get()/100)
        sizedatah = float(sizeinth.get()/100)
        showimg = cv2.resize(ocrfoto,dsize=(int(wsize*sizedataw),int(hsize*sizedatah)))
        pildata = cv2pil(showimg)
        canvaschange(pildata)
    except:
        pass
def changetext():
    if resultset.get():
        resultbtn["text"] = "結果を隠す"
        resultframe.pack(fill=tk.Y,side=tk.LEFT)
        resultset.set(False)
    else:
        resultbtn["text"] = "結果を表示する"
        resultframe.pack_forget()
        resultset.set(True)

def changelist():
    if hideset.get():
        langbtn["text"] = "言語リストを隠す"
        langframe.pack(fill=tk.Y,side=tk.LEFT)
        hideset.set(False)
    else:
        langbtn["text"] = "言語リストを表示する"
        langframe.pack_forget()
        hideset.set(True)
def trancelate():
    if len(showtextdata.get()) >= 5000:
        messagebox.showerror("エラー","文字数が5000文字を超えているため翻訳できません")
    else:
        root.withdraw()
        webview.create_window('翻訳画面', f'https://translate.google.com/?hl=ja&sl=auto&tl=en&text={resulttext.get("1.0","end")}&op=translate',on_top=True)
        webview.start()
        root.deiconify()
def doit(root=root):
    d = textDialog(root)
uselbl = tk.Frame(mainframe)
uselbl.pack(fill=tk.X)
screenbtn = tk.Button(uselbl,text="スクショを撮る",command=getscreen)
screenbtn.pack(fill=tk.BOTH,expand=True,side=tk.LEFT)
ocrbtn = tk.Button(uselbl,text="選択した範囲をOCRする",command=doneocr)
ocrbtn.pack(fill=tk.BOTH,expand=True,side=tk.LEFT)
colorbtn = tk.Button(uselbl,text="色を変更する",command=changecolor)
colorbtn.pack(fill=tk.BOTH,expand=True,side=tk.LEFT)
popupbtn = tk.Button(uselbl,text="結果をポップアップで表示する",command=doit)
popupbtn.pack(fill=tk.BOTH,expand=True,side=tk.LEFT)
langbtn = tk.Button(uselbl,text="言語リストを隠す",command=changelist)
langbtn.pack(fill=tk.BOTH,expand=True,side=tk.LEFT)
resultbtn = tk.Button(uselbl,text="結果を隠す",command=changetext)
resultbtn.pack(fill=tk.BOTH,expand=True,side=tk.LEFT)

canvasframe = tk.Frame(mainframe)
canvasframe.pack(fill=tk.BOTH,expand=True)

openimg = Image.open("adddata\\firstshow.png")
fotocanvas = tk.Canvas(canvasframe)
fotocanvas.pack(fill=tk.BOTH,expand=True,side=tk.LEFT)
sizeintw = tk.IntVar(root)
sizeintw.set(100)
sizeinth = tk.IntVar(root)
sizeinth.set(100)
scaleframe = tk.LabelFrame(root,text="画像表示倍率(%)  上:横の倍率  下:縦の倍率")
scaleframe.pack(fill=tk.X)
sizescale = ttk.Scale(scaleframe,variable=sizeintw,orient=tk.HORIZONTAL,from_=0,to=100,command=sizechange)
sizescale.pack(fill=tk.X)
sizescale = ttk.Scale(scaleframe,variable=sizeinth,orient=tk.HORIZONTAL,from_=0,to=100,command=sizechange)
sizescale.pack(fill=tk.X)
langframe = tk.Frame(canvasframe,bd=1,relief="solid")
langframe.pack(fill=tk.Y,side=tk.LEFT)
selectlang = tk.StringVar(root)
ocrcb = ttk.Combobox(
    langframe, textvariable=selectlang, 
    values=list(langjson.keys()),state="readonly",font=("",15))
ocrcb.set("日本語")
ocrcb.pack(fill=tk.X)
btnlbl = tk.Frame(langframe)
btnlbl.pack(fill=tk.X)
btn = tk.Button(btnlbl,text="言語を追加する",command=langadd)
btn.pack(fill=tk.X,side=tk.LEFT,expand=True)
btn = tk.Button(btnlbl,text="リストから削除する",command=langdel)
btn.pack(fill=tk.X,side=tk.LEFT,expand=True)
langslist = tk.Listbox(langframe,font=("",20),listvariable=langvalue)
langslist.pack(fill=tk.BOTH,expand=True)
resultframe = tk.Frame(canvasframe)
resultframe.pack(fill=tk.Y,side=tk.LEFT)
resulttext = scrolledtext.ScrolledText(resultframe,font=("",15),bd=1,relief="solid",height=2,width=30)
resulttext.pack(fill=tk.Y,expand=True)
trancelatebtn = tk.Button(resultframe,text="翻訳する(google翻訳が開きます)",font=("",15),command=trancelate)
trancelatebtn.pack(fill=tk.X)
bar_y = tk.Scrollbar(fotocanvas, orient=tk.VERTICAL)
bar_y.pack(side=tk.RIGHT, fill=tk.Y)
bar_y.config(command=fotocanvas.yview)
bar_x = tk.Scrollbar(fotocanvas, orient=tk.HORIZONTAL)
bar_x.pack(side=tk.BOTTOM, fill=tk.X)
bar_x.config(command=fotocanvas.xview)
fotocanvas.config(yscrollcommand=bar_y.set, xscrollcommand=bar_x.set)
def dragstart(event):
    if dragset.get():
        pass
    else:
        firstx.set(fotocanvas.canvasx(event.x))
        firsty.set(fotocanvas.canvasy(event.y))
        dragset.set(True)
fotocanvas.bind("<1>",dragstart)
def draging(event):
    secondx.set(fotocanvas.canvasx(event.x))
    secondy.set(fotocanvas.canvasy(event.y))
    fotocanvas.delete("sikaku")
    fotocanvas.create_rectangle(firstx.get(),firsty.get(),secondx.get(),secondy.get(),width=3,tag="sikaku",outline="blue")
fotocanvas.bind("<B1-Motion>",draging)
def dragend(event):
    dragset.set(False)
fotocanvas.bind("<ButtonRelease>",dragend)
def canvaschange(pilimg):
    tkimg = ImageTk.PhotoImage(pilimg,master=root)
    fotocanvas.create_image(0,0,image=tkimg,anchor="nw")
    fotocanvas.img = tkimg
    fotocanvas.config(scrollregion=(0,0,pilimg.width,pilimg.height))
canvaschange(openimg)
root.mainloop()