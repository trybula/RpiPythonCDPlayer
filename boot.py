import vlc #play music
import time #control time
import discid #read discid
import musicbrainzngs #fetch data
import sys
import cdio, pycdio #cdtxt & trackcount
from multiprocessing import Process, Pipe
import threading #scheduling
from math import floor#round down
import signal
import board
from digitalio import DigitalInOut
from adafruit_character_lcd.character_lcd import Character_LCD_Mono
import os
import pylast
from pydbus import SystemBus
import timeout_decorator
import configparser
from unidecode import unidecode#decoding characters to their english ASCII version
from gpiozero import Button
from subprocess import check_call#for shutdown only
#from fonts.py import *


#------------PARSING CONFIG-------------
config = configparser.ConfigParser()
dir_path = os.path.dirname(os.path.realpath(__file__))
config.read(dir_path + '/config.ini')
is_lastfm = config.getboolean('Last_Fm', 'Enable')
API_SECRET = config.get('Last_Fm', 'Api_secret')
os.environ['LAST_FM_API_SECRET'] = API_SECRET
API_KEY = config.get('Last_Fm', 'Api_key')
username = config.get('Last_Fm', 'Username')
password_hash = pylast.md5(config.get('Last_Fm', 'Password'))

lcd_columns = config.getint('Lcd', 'Columns')
lcd_rows = config.getint('Lcd', 'Rows')

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

Button_up = Button(config.get('Buttons', 'Up'))
Button_right = Button(config.get('Buttons', 'Right'))
Button_left = Button(config.get('Buttons', 'Left'))
Button_middle = Button(config.get('Buttons', 'Middle'))
Button_down = Button(config.get('Buttons', 'Down'))


command = 0 # 0-nothing 1-play 2-pause 3-stop 4-next 5-prev
textb = 15
page = 0
MAX_PAGE = 1
start = 0

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

def MsToTime(start, end):
    now_secs= '0' + str(floor((start/1000)%60)) if floor((start/1000)%60) < 10 else str(floor((start/1000)%60))
    now_min= '0' + str(floor((start/1000)/60)) if floor((start/1000)/60) < 10 else str(floor((start/1000)/60))
    end_secs= '0' + str(floor((end/1000)%60)) if floor((end/1000)%60) < 10 else str(floor((end/1000)%60))
    end_min= '0' + str(floor((end/1000)/60)) if floor((end/1000)/60) < 10 else str(floor((end/1000)/60))
    Timer= now_min + ":" + now_secs + " - " + end_min + ":" + end_secs
    return Timer
def SearchExactTracklist(data): #function to find exalctly wchich cd was inserted
    for x in range(0,len(data["disc"]["release-list"])):
        for y in range(0,len(data["disc"]["release-list"][x]["medium-list"])):
            for z in range(0,len(data["disc"]["release-list"][x]["medium-list"][y]["disc-list"])):
                if data["disc"]["release-list"][x]["medium-list"][y]["disc-list"][z]["id"] == data["disc"]["id"]:
                    return x, y
@timeout_decorator.timeout(5)#handling crash of Musicbrainzg
def FetchDataMB():
    musicbrainzngs.set_useragent("Small_diy_cd_player", "0.1", config.get('MusicBrainz', 'Mail'))
    disc = discid.read()#id read
    try:
    	result = musicbrainzngs.get_releases_by_discid(disc.id,includes=["artists", "recordings"]) #get data from Musicbrainz
    	return result
    except musicbrainzngs.ResponseError: #if not available search for cdtext
    	raise ValueError("Error:can't find on musicbrainzngs")
    
def FetchData():
    try:
        d = cdio.Device(driver_id=pycdio.DRIVER_UNKNOWN)
        drive_name = d.get_device()
        i_tracks = d.get_num_tracks()#ilosc trackow
        artists = ["Unknown"] * i_tracks
        track_list = ["Unknown"] * i_tracks
        album = "Unknown"
    except IOError:
        print("Problem finding a CD-ROM")
        sys.exit(1) #if no drive exit

    try:
        result = FetchDataMB()
    except (ValueError, timeout_decorator.timeout_decorator.TimeoutError): #if not available search for cdtext
        print("disc not found or bad response, using cdtxt instead") 
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
            if(track_list[t-1] == "Unknown"):
                track_list[t-1] = "Untitled-" + str(t)
                artists[t-1] = "Unknown"
    else: #if available pull from Musicbrainz
        a, b=SearchExactTracklist(result)
        if result.get("disc"):
            artists = [result["disc"]["release-list"][a]["artist-credit-phrase"]] * i_tracks
            album = result["disc"]["release-list"][a]["title"]
        elif result.get("cdstub"):
            artists = [result["cdstub"]["artist"]] * i_tracks
            album = result["cdstub"]["title"]
        if(len(result["disc"]["release-list"][a]["medium-list"][b]["track-list"]) < i_tracks): #i have some albums that idk why have 1 more track according to pcdio than it should
            for t in range(0,len(result["disc"]["release-list"][a]["medium-list"][b]["track-list"])):
                track_list[t]=(result["disc"]["release-list"][a]["medium-list"][b]["track-list"][t]["recording"]["title"]) #uzupelnij tracklist
            for t in range(len(result["disc"]["release-list"][a]["medium-list"][b]["track-list"]), i_tracks):
                track_list[t]="Untitled-" + str(t+1)
        else:
            for t in range(0,i_tracks):
                #print(t)
                track_list[t]=(result["disc"]["release-list"][a]["medium-list"][b]["track-list"][t]["recording"]["title"]) #uzupelnij tracklist
        #print(track_list)
        if(artists[0] =="Various Artists"): #if musicbrainz returns Variouus artists check if cdtxt has better info
            cdt = d.get_cdtext()
            i_first_track = pycdio.get_first_track_num(d.cd)
            for t in range(i_first_track, i_tracks + i_first_track):
                value = cdt.get(1, t)
                if value != "Unknown" and value is not None:
                    artists[t-1] = value
                pass
    print(artists, '\n', track_list, '\n', album, '\n', i_tracks)
    return artists, track_list, album, i_tracks
def PlayCd(conn):
    try:
        artists, track_list, album, i_tracks = FetchData()
    except cdio.TrackError:
        print("NO CD DUMBASS")
    else:
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
            match dump:
                case 0:
                    conn.send([index+1, i_tracks, track_list[index], artists[index], album, MsToTime(player.get_time(), player.get_length()), player.get_state()])
                #case 1:
                    #listplayer.play()
                case 2:
                    if(player.get_state() == vlc.State.Stopped):
                        listplayer.play()
                    else:
                        listplayer.pause()
                case 3:
                    listplayer.stop()
                    #last_scrobble=""
                case 4:
                    listplayer.next()
                    #last_scrobble=""
                case 5:
                    if(player.get_position()>0.4):
                        player.set_position(0)
                    else:
                        listplayer.previous()
            if((player.get_position()*100 > 50) and last_scrobble != track_list[index]):
                last_scrobble= track_list[index]
                try:
                    if album != "Unknown":
                        network.scrobble(artist=artists[index], title=track_list[index], timestamp=int(time.time()), album=album)
                    elif track_list[index] != "Unknown" and artists[index] != "Unknown":
                        network.scrobble(artist=artists[index], title=track_list[index], timestamp=int(time.time()))
                    print("Scrobbling success: " + artists[index] + track_list[index] + album + str(time.time()))
                except Exception as e:
                    print("Scrobbling failed: " + artists[index] + track_list[index] + album + str(time.time()))
                    print("Reason? ->")
                    print(e)
def ShowCd(dump):
    global textb
    lcd.clear()
    if(len(dump[2])>16):
        if textb >= len(dump[2])+1:
            textb = 16
        TrimMessage=dump[2][textb-16:textb]
        textb+=1
    else:
        TrimMessage=dump[2]
    lcd.message=unidecode(TrimMessage) #title
    lcd.cursor_position(0,1)
    lcd.message=unidecode(dump[5]) # time
    lcd.cursor_position(15,1)
    match dump[6]:
        case vlc.State.Playing:
            lcd.message='\x00'
        case vlc.State.Paused:
            lcd.message='\x01'
        case vlc.State.Stopped:
            lcd.message='\x02'
        case "playing":
            lcd.message='\x00'
        case "paused":
            lcd.message='\x01'
    
class BtPlayer(object):
    def __new__(self):
        bus = SystemBus()
        manager = bus.get('org.bluez', '/')
        
        for obj in manager.GetManagedObjects():
            if obj.endswith('/player0') or obj.endswith('/player2') or obj.endswith('/player1'):
                return bus.get('org.bluez', obj)
        
        raise BtPlayer.DeviceNotFoundError
    
    class DeviceNotFoundError(Exception):
        def __init__(self):
            super().__init__('No music bluetooth device was found')  

def next():
    global run, command
    match page:
        case 0:
            if(not run):
                command = 4
            else:
                parent_conn.send(4)
        case 1:
            
            command = 4
def back():
    global run, command
    match page:
        case 0:
            if(not run):
                command = 5
            else:
                parent_conn.send(5)
        case 1:
            
            command = 5
def stop():
    global run, command
    match page:
        case 0:
            parent_conn.send(3)
        case 1:
            command = 3
def pause():
    global run, command
    match page:
        case 0:
            parent_conn.send(2)
        case 1:
            command = 2
def middle():
    global command, start
    start = time.time()
    command = -1

def shutdown():
    global start
    end = time.time()
    if(end-start>2):
        lcd.clear()
        lcd.message="Goodbye"
        check_call(['sudo', 'poweroff'])

Button_up.when_pressed = pause
Button_left.when_pressed = back
Button_right.when_pressed = next
Button_down.when_pressed = stop
Button_middle.when_pressed = middle
Button_middle.when_released = shutdown

parent_conn, child_conn = Pipe()
lcd.clear()

while True:
    run = False
    match command:
        case 4:
            page+=1
        case 5:
            page-=1
        case -1:
            run = True
    command = 0
    if page == -1:
        page = MAX_PAGE
    elif page > MAX_PAGE:
        page = 0

    match page:
        case 0:
            lcd.clear()
            lcd.message = "CD Player"
            if(run):
                lcd.clear()
                lcd.message = "Loading..."
                cdplayer = Process(target=PlayCd, args=(child_conn,))
                cdplayer.start()
                time.sleep(5)
                while(run):
                        if command == -1 and cdplayer.is_alive():
                            cdplayer.kill()
                            cdplayer.join()
                            run = False
                        elif cdplayer.is_alive():
                            parent_conn.send(0)#you must send to recive
                            time.sleep(0.1)
                            dump=parent_conn.recv()
                            if(dump[6] == vlc.State.Ended):
                                cdplayer.kill()
                                cdplayer.join()
                                lcd.clear()
                                run = False
                            else:
                                ShowCd(dump)
                        else:
                            run = False
                        command=0
                        time.sleep(1)
        case 1:
            lcd.clear()
            lcd.message = "Bluetooth"
            while(run):
                try:
                    handle = BtPlayer()
                    ShowCd([1,1,handle.Track['Title'], handle.Track['Artist'], 'Untitled', MsToTime(handle.Position, handle.Track['Duration']), handle.Status])
                    match command:
                        case -1:
                            run=False
                        case 1:
                            handle.Play()
                        case 2:
                            handle.Pause()
                        case 4:
                            handle.Next()
                        case 5:
                            handle.Previous()
                        case 3:
                            handle.Stop()   
                except:
                    #print("Something crashed, try again") #dbus-monitor --address "unix:path=/run/dbus/system_bus_socket" "type='signal',sender='org.bluez'"
                    lcd.clear()
                    lcd.message = "Something\nwent wrong"    
                    if(command == -1):
                        run=False             
                command = 0
                time.sleep(1)
    time.sleep(0.5)

