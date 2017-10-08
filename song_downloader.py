from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from PIL import Image
import easygui as eg
from easygui import EgStore
import unidecode
import requests
import imghdr
import shutil
import urllib
import pyttsx
import eyed3
import time
import wget
import json
import sys
import os


def cal_Duration(seconds):   #Formats the length of the video into human readable form
    minutes = (seconds-seconds%60)/60
    leftSeconds = seconds%60
    if len(str(leftSeconds))<2:
        left = '0'+str(leftSeconds)
    else:
        left = str(leftSeconds)
    duration = str(minutes)+':'+left
    return duration

def youtube_Results(info):
    queryString = 'https://www.youtube.com/results?search_query='
    mainUrl = queryString+info+' audio'

    source_code = requests.get(mainUrl)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text,'lxml')
    results = soup.select('a[href^="/watch?v="]')

    cleanResults = []
    for item in results:
        cleanResults.append(item.get('href'))

    cleanestResults = []
    for item in cleanResults:
        if item in cleanestResults:
            continue
        else:
            cleanestResults.append(item)

    return cleanestResults

def xml_Results(youtubeUrl):
    xmlUrl = 'https://www.youtube.com/oembed?url='+youtubeUrl+'&format=xml'

    source_code = requests.get(xmlUrl)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text,'xml')

    for thumb in soup.findAll('thumbnail_url'):
        thumbUrl = thumb.text

    for title in soup.findAll('title'):
        videoTitle = title.text
        videoTitle = unidecode.unidecode(videoTitle)

    for author in soup.findAll('author_name'):
        authorName = author.text

    xmlDetails = {}
    xmlDetails['title'] = videoTitle
    xmlDetails['author'] = authorName
    xmlDetails['thumb'] = thumbUrl

    #xmlDetails = {'title': videoTitle,'thumb': thumbUrl}

    return xmlDetails

def call_Provider(youtubeUrl):
    infoUrl = 'https://www.youtubeinmp3.com/fetch/?format=JSON&video='+youtubeUrl

    source_code = requests.get(infoUrl)
    plain_text = source_code.text
    jsonData = json.loads(plain_text)
    duration = cal_Duration(int(jsonData['length'])) #Formats the length of the video into human readable form /Calling the cal_duration function
    downloadLink = jsonData['link']

    apiResults = {}
    apiResults['duration'] = duration
    apiResults['download'] = downloadLink
    #apiResults = {'duration':duration,'download':downloadLink}

    return apiResults

def find_Cover(searchCover):
    headers = {'user-agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17'}

    googleUrl = 'https://google.co.in/search?q='+searchCover+' artwork lastfm'+'&source=lnms&tbm=isch&sa=X'
    source_code = requests.get(googleUrl,headers=headers)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text,'lxml')
    print('Fetching artwork for your music file...')
    for div in soup.findAll('div',attrs={'class':'rg_meta'}):
        image = div.text
        jsonGoogle = json.loads(image)
        #print(jsonGoogle)
        break

    imageUrl = jsonGoogle['ou']

    #extension = jsonGoogle['ou'][-4:]

    #print(coverImageFile)
    #save cover image to disk
    print('Downloading the the best artwork we found for your music file...')
    urllib.urlretrieve(imageUrl,'cover')
    extension = imghdr.what('cover')
    newFilename = 'cover.'+extension
    os.rename('cover',newFilename)
    #print('Cover Image downloaded...')

    return newFilename

def set_Tags(trackName,artistName,movieName,fileName):

    if artistName.strip() == '':
        artistName = 'Unknown'

    audio = eyed3.load(fileName)
    imageData = open('cover.jpeg','rb').read()
    print('Settings ID3 Tags of your music file...')
    audio.tag.images.set(2,imageData,'image/jpeg')

    audio.tag.title = unicode(trackName.title(),'utf-8')

    if movieName.strip() == '':
        pass
    else:
        audio.tag.album = unicode(movieName.title(),'utf-8')
        # print(movieName)

    audio.tag.album_artist = unicode(artistName.title(),'utf-8')

    audio.tag.save()

def standardize_Cover(coverName):
    img = Image.open(coverName)
    print('Optimizing the artwork we downloaded for your music file...')
    width , height = img.size
    if width > 600:
        bg = img.resize((600,600),Image.ANTIALIAS)
        bg.save('cover.jpeg',quality=100)
    else:
        img.save('cover.jpeg',quality = 100)

def remove_Special(string):
    quotes = ['\'','\"','\\','/',':','*','?','<','>','|']
    clean = ''
    for i in range(len(string)):
        if string[i] in quotes:
            continue
        else:
            clean += string[i]

    return clean

def config_Settings():

    fileName = 'config.txt'
    path = os.path.join(os.getcwd(),fileName)

    if os.path.isfile(path):
        configFile = open(path,'r')
        string = configFile.read()
        jsonData = json.loads(string)
        test = jsonData['time']
        if test < time.time():
            musicDir = jsonData['dir']
        configFile.close()

    else:
        #define what happens when the file doesn't exist
        configFile = open(path,'w')
        config = {}
        config['time']=time.time()
        musicDir = eg.diropenbox(title='Select your music directory : ')
        config['dir']=musicDir
        string = json.dumps(config)
        configFile.write(string)
        configFile.close()


    return musicDir

#Functions defintions finishes here
music = config_Settings()
speak = pyttsx.init()
answers = eg.multenterbox(msg='Enter Details to Proceed: ',title='Song Downloader',fields=['Track Name','Artist Name','Movie Name'],callback=None,run=True)

#Checking for validity of answers
if answers!=None:
    check = 1
    while check:
        if answers[0].strip()=='':
            errmsg = '\"Track Name\" is a required field.'
            answers = eg.multenterbox(msg=errmsg, title='Song Downloader',fields=['Track Name','Artist Name','Movie Name'],values=[answers[0],answers[1],answers[2]],callback=None,run=True)
        elif answers[1].strip() == '' and answers[2].strip() == '':
            errmsg = 'You need to enter either \"Artist Name\" or \"Movie Name\".'
            answers = eg.multenterbox(msg=errmsg, title='Song Downloader',fields=['Track Name','Artist Name','Movie Name'],values=[answers[0],answers[1],answers[2]],callback=None,run=True)
        else:
            check = 0
            #for exiting the loop if the validity of the fields are met
else:
    print('The user didn\'t enter the required details.')
    sys.exit()

searchInput = answers[0]+' '+answers[1]+' '+answers[2]

results = youtube_Results(searchInput)

no = 0
Next = 1
while Next:
    # href = results[no]
    if no < len(results):

        youtubeUrl = 'https://www.youtube.com'+results[no]
        details = xml_Results(youtubeUrl)
        apiData = call_Provider(youtubeUrl)

        urllib.urlretrieve(details['thumb'],'thumb.jpg')
        img = Image.open('thumb.jpg')
        img = img.resize((200,188),Image.ANTIALIAS)
        img.save('thumb.jpg')

        msg = 'Does this look like the song you were trying to download? \n\n Title : '+details['title']+'\n Author : '+details['author']+'\n Duration : '+apiData['duration']
        choices = ['<Prev','Yes','No','Next>']
        reply = eg.buttonbox(msg,title='Song Downloader',image='thumb.jpg',choices=choices,default_choice='Yes',cancel_choice='No')

        if reply == 'Yes':
            #Put fileName here
            # print(details['title'])
            details['title'] = remove_Special(details['title'])
            fileName = eg.filesavebox(default=music+'\\'+details['title']+'.mp3')

            if fileName == None:
                print('The download was cancelled by the user.')
                speak.say('The download was cancelled by the user.')
                speak.runAndWait()
                break

            else:
                speak.say('The song is being downloaded right now')
                speak.runAndWait()
                startTime = time.time()

                wget.download(apiData['download'],out='temp.mp3')
                # urllib.urlretrieve(apiData['download'],'temp.mp3')

                endTime = time.time()
                timeElapsed = endTime - startTime
                timeElapsed = round(timeElapsed,2)
                speak.say('The song has been downloaded on your computer.')
                speak.runAndWait()
                print('The song was downloaded to your computer in '+str(timeElapsed)+'s')

                #Deletes the ID3 Tag of the dowloaded file
                mp3 = MP3('temp.mp3')
                mp3.delete()
                mp3.save()

                searchCover = answers[0]+' '+answers[1]+' '+answers[2]
                cover = find_Cover(searchCover)
                standardize_Cover(cover)
                set_Tags(answers[0],answers[1],answers[2],'temp.mp3')

                shutil.move('temp.mp3',fileName)

                os.remove('thumb.jpg')
                if 'jpeg' in cover:
                    os.remove(cover)
                else:
                    os.remove(cover)
                    os.remove('cover.jpeg')
                break

        elif reply == 'Next>':
            no +=1

        elif reply == '<Prev':
            no -=1

        elif reply == 'No':
            print('The application was closed by the user.')
            break

        else:
            Next = 0
    else:
        eg.msgbox('Sorry, no more results are available.')
