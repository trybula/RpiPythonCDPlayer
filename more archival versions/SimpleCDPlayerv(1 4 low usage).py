import vlc #play music
import time #control time
import discid #read discid
import musicbrainzngs #fetch data
import sys
import cdio, pycdio #cdtxt & trackcount
import RPi.GPIO as GPIO#buttons
import threading #scheduling
from Adafruit_CharLCD import Adafruit_CharLCD #LCD
import math#round down
import signal

# instantiate lcd and specify pins
lcd = Adafruit_CharLCD(rs=26, en=25,
                       d4=10, d5=9, d6=11, d7=0,
                       cols=16, lines=2)
lcd.clear()
lcd.message("Running\nModule")

playchar = [
    0b01000,
    0b01100,
    0b01110,
    0b01111,
    0b01110,
    0b01100,
    0b01000,
    0b00000
]

pausechar = [
    0b00000,
    0b10010,
    0b10010,
    0b10010,
    0b10010,
    0b10010,
    0b10010,
    0b00000
]

stopchar = [
    0b00000,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b11111,
    0b00000,
    0b00000
]
# Store the custom character in the LCD's memory (in location 0)
lcd.create_char(0, playchar)
lcd.create_char(1, pausechar)
lcd.create_char(2, stopchar)

GPIO.setmode(GPIO.BCM) #przyciski
BUTTONS = [5, 6, 22, 23, 24]
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#ogarnianie cd
try:
    d = cdio.Device(driver_id=pycdio.DRIVER_UNKNOWN)
    drive_name = d.get_device()
    i_tracks = d.get_num_tracks()#ilosc trackow
except IOError:
    print("Problem finding a CD-ROM")
    sys.exit(1) #if no drive exit


songnumber = 0 #zmienne kontrolujace wyswietlanie
track_list = []
data = {"Autor" : "Unknown", "Album": "Unknown"}
statep = 0 #0-play 1-pause 2-stop

def search_exact_tracklist(data): #function to find exalctly wchich cd was inserted (previously multi cd releases didnt work)
    for x in range(0,len(data["disc"]["release-list"])):
        for y in range(0,len(data["disc"]["release-list"][x]["medium-list"])):
            for z in range(0,len(data["disc"]["release-list"][x]["medium-list"][y]["disc-list"])):
                if data["disc"]["release-list"][x]["medium-list"][y]["disc-list"][z]["id"] == data["disc"]["id"]:
                    return x, y

def fetchdata():
    global track_list
    global data
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
        print(track_list)

def next_media_playing(event):
    global songnumber
    songnumber +=1
    if songnumber == i_tracks:
        listplayer.stop()
        songnumber=0
        print("Koniec tej wycieczki")
    else:
        print("Now playing: " , track_list[songnumber])
        time.sleep(0.25)
        print("Duration: ", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))

def next_track(channel):
    listplayer.next()
    next_media_playing(0)
def prev_track(channel):
    global songnumber
    listplayer.previous()
    if songnumber == 0:
        print("bardziej sie nie cofniesz")
    else:
        songnumber-=1
        print("Now playing: " , track_list[songnumber])
        time.sleep(0.25)
        print("Duration: ", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000))) #set_time(1000)
def stop_track(channel):
    global songnumber
    global statep
    listplayer.stop()
    songnumber=0
    statep = 2
def pause_track(channel):
    global statep
    listplayer.pause()
    statep = 1
    print("Paused at: ", time.strftime("%H:%M:%S", time.gmtime(player.get_time()/1000)), "---", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
def play_track(channel):
    global songnumber
    global statep
    listplayer.play()
    statep = 0
    print("Resuming ",track_list[songnumber])
def time_track(channel):
    global songnumber
    global statep
    #print(time.strftime("%H:%M:%S", time.gmtime(player.get_time()/1000)), "---", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
    #wiadomosc=time.strftime("%H:%M:%S", time.gmtime(player.get_time()/1000)) + "-" + time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000))
    wiadomosc= str(math.floor((player.get_time()/1000)/60)) + ":" + str(math.floor((player.get_time()/1000)%60)) + " - " + str(math.floor((player.get_length()/1000)/60)) + ":" + str(math.floor((player.get_length()/1000)%60))
    lcd.clear()
    lcd.message(track_list[songnumber])
    lcd.set_cursor(0,1)
    lcd.message(wiadomosc)
    lcd.set_cursor(15,1)
    match statep:
        case 0:
            lcd.message('\x00')
        case 1:
            lcd.message('\x01')
        case 2:
            lcd.message('\x02')
def auto_time():
    time_track(0)
    threading.Timer(2, auto_time).start()# schedule the function to run every 2 second
def exiting(channel):
    time.sleep(1)
    sys.exit(0) #it wont work in VScodium/code
    print('konczymy')

GPIO.add_event_detect(BUTTONS[0], GPIO.FALLING, callback=next_track, bouncetime=1000) #ustaw eventy
GPIO.add_event_detect(BUTTONS[1], GPIO.FALLING, callback=prev_track, bouncetime=1000)
GPIO.add_event_detect(BUTTONS[3], GPIO.FALLING, callback=stop_track, bouncetime=1000)
GPIO.add_event_detect(BUTTONS[2], GPIO.FALLING, callback=pause_track, bouncetime=1000)
GPIO.add_event_detect(BUTTONS[4], GPIO.FALLING, callback=play_track, bouncetime=1000)
#GPIO.add_event_detect(BUTTONS[2], GPIO.FALLING, callback=exiting, bouncetime=1000)

fetchdata()
print(data["Autor"],'\t',data["Album"])
print('\n')

instance = vlc.Instance() #uruchom vlc
player = instance.media_player_new()
medialist = instance.media_list_new()
listplayer = instance.media_list_player_new()
listplayer.set_media_player(player) 
for i in (range(1,i_tracks+1)):          #second option
    track = instance.media_new("cdda:///dev/cdrom", (":cdda-track=" + str(i)))
    medialist.add_media(track)
listplayer.set_media_list(medialist)


print("Now playing: " , track_list[songnumber]) #startujemy
listplayer.play()
time.sleep(10)#wait to spin
print("Duration: ", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
lcd.show_cursor(False)
#auto jak sie piosenka zmienia sama
event_manager = player.event_manager()# Get the event manager from the player
event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, next_media_playing)# Register the callback

auto_time() #run showing time
signal.pause() #wait for signal, previously it While True: pass, but it consumed 100% of cpu
