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

track_list = []
data = {"Autor" : "Unknown", "Album": "Unknown"}
i_tracks = 0
command = 0 # 0-nothing 1-play 2-pause 3-stop 4-next 5-prev

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
    global track_list
    global data
    global i_tracks
    #ogarnianie cd
    try:
        d = cdio.Device(driver_id=pycdio.DRIVER_UNKNOWN)
        drive_name = d.get_device()
        i_tracks = d.get_num_tracks()#ilosc trackow
    except IOError:
        print("Problem finding a CD-ROM")
        sys.exit(1) #if no drive exit

    musicbrainzngs.set_useragent("Small_diy_cd_player", "0.1", "miki.klopsiki@o2.pl")
    disc = discid.read()#id read
    try:
        result = musicbrainzngs.get_releases_by_discid(disc.id,includes=["artists", "recordings"]) #get data from Musicbrainz
    except musicbrainzngs.ResponseError:
        print("disc not found or bad response, using cdtxt instead") #if not available search for cdtext
        cdt = d.get_cdtext()
        i_first_track = pycdio.get_first_track_num(d.cd)
        for t in range(i_first_track, i_tracks + i_first_track):
            value = cdt.get(0, t)
            if value is not None:
                track_list.append(value)
                pass
            else: #if there isnt anything just type Unknowsn
                track_list.append("Unknown-%s" % t)
                pass
        pass
    else: #Artist and album info
        a, b=search_exact_tracklist(result)
        if result.get("disc"):
            data["Autor"] = result["disc"]["release-list"][a]["artist-credit-phrase"]
            data["Album"] = result["disc"]["release-list"][a]["title"]
        elif result.get("cdstub"):
            data["Autor"] = result["cdstub"]["artist"]
            data["Album"] = result["cdstub"]["title"]
        #print(result["disc"]["release-list"][a]["medium-list"][b]["track-list"])
        for i in range(0,i_tracks):
            track_list.append(result["disc"]["release-list"][a]["medium-list"][b]["track-list"][i]["recording"]["title"]) #uzupelnij tracklist
def playcd(conn):
    fetchdata()

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

    while True:
        dump = conn.recv()
        index = medialist.index_of_item(listplayer.get_media_player().get_media())
        Timer= str(floor((player.get_time()/1000)/60)) + ":" + str(floor((player.get_time()/1000)%60)) + " - " + str(floor((player.get_length()/1000)/60)) + ":" + str(floor((player.get_length()/1000)%60))
        conn.send([index+1, i_tracks, track_list[index], data["Autor"], data["Album"], Timer, player.get_state()])
        match dump:
            case 0:
                pass
            case 1:
                listplayer.play()
            case 2:
                listplayer.pause()
            case 3:
                listplayer.stop()
            case 4:
                listplayer.next()
            case 5:
                listplayer.previous()
def PlayerGlobalSync():
    global songnumber, track_list, data, i_tracks, command, cdplayer
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
        print(dump)
        
        lcd.clear()
        lcd.message=dump[2]
        lcd.cursor_position(0,1)
        lcd.message=dump[5]
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


while True:
    dump = input()
    if dump == '-1':
        cdplayer.kill()
        cdplayer.join()
    elif (dump == '-2') and not cdplayer.is_alive():
        cdplayer = Process(target=playcd, args=(child_conn,))
        cdplayer.start()
    else:
        command=int(dump)

