import glob
import json
import os
import io
import re
import time
from pprint import pprint
from apiclient import discovery
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client.file import Storage
from oauth2client import client
from oauth2client import tools
import httplib2
from io import StringIO
from pdf2image import convert_from_path
import PyPDF2

def get_credentials():

    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/drive-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/drive'
    CLIENT_SECRET_FILE = 'client_secret_395744274280-ot1ar85i1306dvbo7ql1a7rqblc3j1bn.apps.googleusercontent.com.json'
    APPLICATION_NAME = 'Drive API Python Quickstart'

    credential_path = os.path.join("./", 'drive-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def ocr(file):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    imgfile = file+'.jpg'  # Image with texts (png, jpg, bmp, gif, pdf)
    txtfile = file+'.txt'  # Text file outputted by OCR

    mime = 'application/vnd.google-apps.document'
    res = service.files().create(
        body={
            'name': imgfile,
            'mimeType': mime
        },
        media_body=MediaFileUpload(imgfile, mimetype=mime, resumable=True)
    ).execute()

    downloader = MediaIoBaseDownload(
        io.FileIO(txtfile, 'wb'),
        service.files().export_media(fileId=res['id'], mimeType="text/plain")
    )
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    service.files().delete(fileId=res['id']).execute()
    print("Done.")


def convertpdf2image(path_to_pdf):
    images = convert_from_path(path_to_pdf)
    for i in range(15,len(images)-10):
        images[i].save("page"+str(i+1)+".jpg","JPEG")

def ocrText(sommaire,pages):
    for i in range(sommaire,pages-9):
        time.sleep(4)
        ocr("page"+str(i))
        time.sleep(4)
        os.remove("page"+str(i) + ".jpg")


def pdfPages(Pdf):
    file = open(Pdf,"rb")
    readpdf =PyPDF2.PdfFileReader(file)
    return readpdf.numPages

def groupTextArabic(sommaire,pages):
    fileText = open("total.txt", "w", encoding="UTF-8")
    for i in range(sommaire,pages-9):
        file = open("page"+str(i) +".txt", "r", encoding="UTF-8")
        fileText.write(file.read())
        file.close()
        os.remove("page"+str(i) +".txt")
    fileText.close()

def correction(Results):
    temp=[]
    for i in range(len(Results)-1):
        if(Results[i]+200<Results[i+1]):
            temp.append(Results[i])
    temp.append(Results[len(Results) - 1])
    return temp

def getsegment():
    file=open("total.txt",'r',encoding="UTF-8")
    Text=file.read()
    Results=[]
    allmatches = re.finditer("ملف رقم", Text, flags=re.IGNORECASE)
    for m in allmatches:
        Results.append(m.start())
    Results=correction(Results)
    return Results

def getSegmentText(Tab):
    file = open("total.txt", 'r', encoding="UTF-8")
    Text = file.read()
    texts=[]
    for i in range(len(Tab)-1):
        texts.append(Text[Tab[i]:Tab[i+1]])
    texts.append(Text[Tab.pop():])
    return texts

def getChambre(text):

    r=None
    e=None
    allmatches = re.finditer("________________", text, flags=re.IGNORECASE)
    for m in allmatches:
        r=m.end()
    allmatches = re.finditer("ملف", text, flags=re.IGNORECASE)
    for m in allmatches:
        e = m.start()
    if(r==None): return ""
    else:
        if(e!=None):
            result=text[r:e]
        else:result=text[r:]
    return result

def getTabofChamber(texts):
    tab = []
    newtab = []
    for t in texts:
        tab.append(getChambre(t))
    newtab.append(tab[0])
    for i in range(len(tab) - 1):
        newtab.append(tab[i])
    return(newtab)

def getItems(text,chambre):
    start=None
    finish=None
    code=""
    date=""
    title=""
    sujet=""
    keywords=""
    reference=""
    principe=""
    content=""
    allmatches = re.finditer("ملف رقم", text, flags=re.IGNORECASE)
    for m in allmatches:
        start=m.end()
        break
    allmatches = re.finditer("قرار", text, flags=re.IGNORECASE)
    for m in allmatches:
        finish = m.start()
        break
    if (start!=None and finish!=None):
        code=text[start:finish]
    start = None
    finish = None
    allmatches = re.finditer("بتاريخ", text, flags=re.IGNORECASE)
    for m in allmatches:
        start = m.end()
        break
    allmatches = re.finditer("قضية", text, flags=re.IGNORECASE)
    for m in allmatches:
        finish = m.start()
        break
    if (start!=None and finish!=None):
        date=text[start:finish].replace("/", "-")
    start = None
    finish = None
    allmatches = re.finditer("قضية", text, flags=re.IGNORECASE)
    for m in allmatches:
        start = m.end()
        break
    allmatches = re.finditer("موضوع", text, flags=re.IGNORECASE)
    for m in allmatches:
        finish = m.start()
        break
    if (start!=None and finish!=None):
        title=text[start:finish]
    start = None
    finish = None
    allmatches = re.finditer("موضوع", text, flags=re.IGNORECASE)
    for m in allmatches:
        start = m.end()
        break
    allmatches = re.finditer("مرجع القانوني", text, flags=re.IGNORECASE)
    for m in allmatches:
        finish = m.start()
        break
    if (start!=None and finish!=None):
        sujet = text[start:finish]
    start = None
    finish = None
    allmatches = re.finditer("كلمات الأساسية", text, flags=re.IGNORECASE)
    for m in allmatches:
        start = m.end()
        break
    allmatches = re.finditer("مرجع القانوني", text, flags=re.IGNORECASE)
    for m in allmatches:
        finish = m.start()
        break
    if (start!=None and finish!=None):
        keywords = text[start:finish]
    start = None
    finish = None
    allmatches = re.finditer("مرجع القانوني", text, flags=re.IGNORECASE)
    for m in allmatches:
        print(m)
        start = m.end()
        break
    allmatches = re.finditer("مبدأ", text, flags=re.IGNORECASE)
    for m in allmatches:
        print(m)
        finish = m.start()
        break
    if (start!=None and finish!=None):
        reference = text[start:finish]
    start = None
    finish = None
    allmatches = re.finditer("مبدأ", text, flags=re.IGNORECASE)
    for m in allmatches:
        start = m.end()
        break
    allmatches = re.finditer("إن المحكمة العليا", text, flags=re.IGNORECASE)
    for m in allmatches:
        finish = m.start()
        break
    if (start!=None and finish!=None):
        principe = text[start:finish]
    start = None
    finish = None
    allmatches = re.finditer("إن المحكمة العليا", text, flags=re.IGNORECASE)
    for m in allmatches:
        start = m.end()
        break
    if (start!=None):
        content = text[start:]
    if (sujet!=""):
        return Jurisprudence(code,date,principe,chambre,title,content,sujet,keywords,reference)


class Jurisprudence:
    def __init__(self,code,date,principle,room_ar,title,content,sujet,keywords,reference):
        self.id=code
        self.date=date
        self.principle=principle
        self.code=code
        self.year=None
        self.room_ar=room_ar
        self.title=title
        self.room=None
        self.decision=content
        self.sujet=sujet
        self.keywords=keywords
        self.reference=reference

def finalisation(texts,chambres,num):
    elements = []
    for i in range(len(chambres)):
        item=getItems(texts[i], chambres[i])
        if (item!=None):
            elements.append(item)
    file = open(f"{num}.json", "w", encoding="UTF-8")
    json_str = json.dumps([ob.__dict__ for ob in elements])
    file.write(json_str)
    file.close()

read_files = glob.glob("PDF/*.pdf")
i=1
for f in read_files:
    print(f)
    convertpdf2image(f)
    ocrText(16,pdfPages(f))
    groupTextArabic(16,pdfPages(f))
    texts = getSegmentText(getsegment())
    chambres = getTabofChamber(texts)
    finalisation(texts, chambres, i)
    i+=1




