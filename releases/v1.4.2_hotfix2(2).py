# A runatboot file
import vlc #play music
import time #control time
import discid #read discid
import musicbrainzngs #fetch data
import sys
import cdio, pycdio #cdtxt & trackcount
from multiprocessing import Process, Pipe
import threading #scheduling
from math import floor#round down
import signal#last 4 is for LCD
import board
from digitalio import DigitalInOut
from adafruit_character_lcd.character_lcd import Character_LCD_Mono
import RPi.GPIO as GPIO#buttons
import os
os.environ['LAST_FM_API_SECRET'] = ''
import pylast
API_KEY = ""#Lastfm login data
API_SECRET = ""
username = ""
password_hash = pylast.md5(b"")

lcd_columns = 16
lcd_rows = 2

lcd_rs = DigitalInOut(board.D26)
lcd_en = DigitalInOut(board.D25)
lcd_d4 = DigitalInOut(board.D10)
lcd_d5 = DigitalInOut(board.D9)
lcd_d6 = DigitalInOut(board.D11)
lcd_d7 = DigitalInOut(board.D0)
# Initialise the LCD class
lcd = Character_LCD_Mono(
    lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
lcd.clear()
lcd.cursor = False
lcd.blink = False

GPIO.setmode(GPIO.BCM) #przyciski
BUTTONS = [5, 6, 22, 23, 24, 12]
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

command = 0 # 0-nothing 1-play 2-pause 3-stop 4-next 5-prev
textb = 15

playchar = [
    0b01000,
    0b01100,
    0b01110,
    0b01111,
    0b01110,
    0b01100,
    0b01000,
    0b00000]
pausechar = [
    0b00000,
    0b10010,
    0b10010,
    0b10010,
    0b10010,
    0b10010,
    0b10010,
    0b00000]
stopchar = [
    0b00000,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b00000,
    0b00000]
lcd.create_char(0, playchar)
lcd.create_char(1, pausechar)
lcd.create_char(2, stopchar)

def search_exact_tracklist(data): #function to find exalctly wchich cd was inserted
    for x in range(0,len(data["disc"]["release-list"])):
        for y in range(0,len(data["disc"]["release-list"][x]["medium-list"])):
            for z in range(0,len(data["disc"]["release-list"][x]["medium-list"][y]["disc-list"])):
                if data["disc"]["release-list"][x]["medium-list"][y]["disc-list"][z]["id"] == data["disc"]["id"]:
                    return x, y
def fetchdata():
    try:
        d = cdio.Device(driver_id=pycdio.DRIVER_UNKNOWN)
        drive_name = d.get_device()
        i_tracks = d.get_num_tracks()#ilosc trackow
        artists = [None] * i_tracks
        track_list = [None] * i_tracks
        album = "Unknown"
    except IOError:
        print("Problem finding a CD-ROM")
        sys.exit(1) #if no drive exit

    musicbrainzngs.set_useragent("Small_diy_cd_player", "0.1")
    disc = discid.read()#id read
    try:
        result = musicbrainzngs.get_releases_by_discid(disc.id,includes=["artists", "recordings"]) #get data from Musicbrainz
    except musicbrainzngs.ResponseError:
        print("disc not found or bad response, using cdtxt instead") #if not available search for cdtext
        cdt = d.get_cdtext()
        i_first_track = pycdio.get_first_track_num(d.cd)

        for t in range(i_first_track, i_tracks + i_first_track):
            for i in range(pycdio.MIN_CDTEXT_FIELD, pycdio.MAX_CDTEXT_FIELDS):
                #print(pycdio.cdtext_field2str(i)) ##0-TITLE 1-PERFORMER 2-SONGWRITER 3-COMPOSER 4-MESSAGE 5-ARRANGER 6-ISRC 7-UPC_EAN  8-GENERE 9-DISC_ID 
                value = cdt.get(i, t)
                if value is not None:
                    if i == 0:
                        track_list[t-1] = value
                        pass
                    elif i == 1:
                        artists[t-1] = value
                        pass
                    pass
                pass
            if(track_list[t-1] == None):
                track_list[t-1] = "Untitled-" + str(t)
                artists[t-1] = "Unknown"
    else: #Artist and album info
        a, b=search_exact_tracklist(result)
        if result.get("disc"):
            artists = [result["disc"]["release-list"][a]["artist-credit-phrase"]] * i_tracks
            album = result["disc"]["release-list"][a]["title"]
        elif result.get("cdstub"):
            artists = [result["cdstub"]["artist"]] * i_tracks
            album = result["cdstub"]["title"]
        for t in range(0,i_tracks):
            track_list[t]=(result["disc"]["release-list"][a]["medium-list"][b]["track-list"][t]["recording"]["title"]) #uzupelnij tracklist
    #print(artists, '\n', track_list, '\n', album, '\n', i_tracks)
    return artists, track_list, album, i_tracks
def playcd(conn):
    artists, track_list, album, i_tracks = fetchdata()

    instance = vlc.Instance() #uruchom vlc
    player = instance.media_player_new()
    medialist = instance.media_list_new()
    listplayer = instance.media_list_player_new()
    listplayer.set_media_player(player) 
    for i in (range(1,i_tracks+1)):          #second option
        track = instance.media_new("cdda:///dev/cdrom", (":cdda-track=" + str(i)))
        medialist.add_media(track)
    listplayer.set_media_list(medialist)

    listplayer.play()
    time.sleep(5)#wait to spin

    last_scrobble=""
    network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=username, password_hash=password_hash)
    while True:
        dump = conn.recv()
        index = medialist.index_of_item(listplayer.get_media_player().get_media())
        now_secs= '0' + str(floor((player.get_time()/1000)%60)) if floor((player.get_time()/1000)%60) < 10 else str(floor((player.get_time()/1000)%60))
        now_min= '0' + str(floor((player.get_time()/1000)/60)) if floor((player.get_time()/1000)/60) < 10 else str(floor((player.get_time()/1000)/60))
        end_secs= '0' + str(floor((player.get_length()/1000)%60)) if floor((player.get_length()/1000)%60) < 10 else str(floor((player.get_length()/1000)%60))
        end_min= '0' + str(floor((player.get_length()/1000)/60)) if floor((player.get_length()/1000)/60) < 10 else str(floor((player.get_length()/1000)/60))
        Timer= now_min + ":" + now_secs + " - " + end_min + ":" + end_secs
        conn.send([index+1, i_tracks, track_list[index], artists[index], album, Timer, player.get_state()])
        match dump:
            case 0:
                pass
            case 1:
                listplayer.play()
            case 2:
                listplayer.pause()
            case 3:
                listplayer.stop()
                last_scrobble=""
            case 4:
                listplayer.next()
                last_scrobble=""
            case 5:
                listplayer.previous()
                last_scrobble=""
        if((player.get_position()*100 > 50) and last_scrobble != track_list[index]):
            last_scrobble= track_list[index]
            if album != "Unknown":
                network.scrobble(artist=artists[index], title=track_list[index], timestamp=int(time.time()), album=album)
            elif track_list[index] != "Unknown" and artists[index] != "Unknown":
                network.scrobble(artist=artists[index], title=track_list[index], timestamp=int(time.time()))

def PlayerGlobalSync():
    global command, cdplayer, textb
    if command == -1:
        if cdplayer.is_alive():
            cdplayer.kill()
            cdplayer.join()
            lcd.clear()
            lcd.message = "Change\nmedium"
        else:
            cdplayer = Process(target=playcd, args=(child_conn,))
            cdplayer.start()
    elif cdplayer.is_alive():
        parent_conn.send(command)
        time.sleep(0.1)
        dump=parent_conn.recv()
        #print(dump)
        lcd.clear()
        if(dump[6] == vlc.State.Ended):
            cdplayer.kill()
            cdplayer.join()
            lcd.clear()
            lcd.message = "CD ended\nChange medium"
        else:
            if(len(dump[2])>16):
                if textb >= len(dump[2])+1:
                    textb = 16
                TrimMessage=dump[2][textb-16:textb]
                textb+=1
            else:
                TrimMessage=dump[2]
            lcd.message=TrimMessage #title
            lcd.cursor_position(0,1)
            lcd.message=dump[5] # time
            lcd.cursor_position(15,1)
            match dump[6]:
                case vlc.State.Playing:
                    lcd.message='\x00'
                case vlc.State.Paused:
                    lcd.message='\x01'
                case vlc.State.Stopped:
                    lcd.message='\x02'
    command=0
    P=threading.Timer(1, PlayerGlobalSync)
    P.start()

GPIO.add_event_detect(BUTTONS[0], GPIO.FALLING, callback=lambda event: globals().update(command = 4), bouncetime=1000)
GPIO.add_event_detect(BUTTONS[1], GPIO.FALLING, callback=lambda event: globals().update(command = 5), bouncetime=1000)
GPIO.add_event_detect(BUTTONS[3], GPIO.FALLING, callback=lambda event: globals().update(command = 3), bouncetime=1000)
GPIO.add_event_detect(BUTTONS[2], GPIO.FALLING, callback=lambda event: globals().update(command = 2), bouncetime=1000)
GPIO.add_event_detect(BUTTONS[4], GPIO.FALLING, callback=lambda event: globals().update(command = 1), bouncetime=1000)
GPIO.add_event_detect(BUTTONS[5], GPIO.FALLING, callback=lambda event: globals().update(command = -1), bouncetime=1000)

parent_conn, child_conn = Pipe()
cdplayer = Process(target=playcd, args=(child_conn,))

cdplayer.start()
PlayerGlobalSync()

