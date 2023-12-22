import vlc #play music
import time #control time
import discid #read discid
import musicbrainzngs #fetch data
import sys
import cdio, pycdio #cdtxt i trackcount
import RPi.GPIO as GPIO#buttons
import threading #scheduling

GPIO.setmode(GPIO.BCM) #przyciski
BUTTONS = [5, 6, 12, 22, 23, 24]
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#ogarnianie cd
try:
    d = cdio.Device(driver_id=pycdio.DRIVER_UNKNOWN)
    drive_name = d.get_device()
    i_tracks = d.get_num_tracks()#ilosc trackow
except IOError:
    print("Problem finding a CD-ROM")
    sys.exit(1)


songnumber = 0 #zmienne kontrolujace wyswietlanie
track_list = []
data = {"Autor" : "Unknown", "Album": "Unknown"}

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
        if result.get("disc"):
            data["Autor"] = result["disc"]["release-list"][0]["artist-credit-phrase"]
            data["Album"] = result["disc"]["release-list"][0]["title"]
        elif result.get("cdstub"):
            data["Autor"] = result["cdstub"]["artist"]
            data["Album"] = result["cdstub"]["title"]
        release = result["disc"]["release-list"][0] #tracklist
        medium = release["medium-list"][0]
        for i in range(0,i_tracks-1):
            track_list.append(medium["track-list"][i]["recording"]["title"]) #uzupelnij tracklist

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
    listplayer.stop()
    songnumber=0
def pause_track(channel):
    listplayer.pause()
    print("Paused at: ", time.strftime("%H:%M:%S", time.gmtime(player.get_time()/1000)), "---", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
def play_track(channel):
    global songnumber
    listplayer.play()
    print("Resuming ",track_list[songnumber])
def time_track(channel):
    print(time.strftime("%H:%M:%S", time.gmtime(player.get_time()/1000)), "---", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
def auto_time():
    time_track(0)
    threading.Timer(1, auto_time).start()# schedule the function to run every second

GPIO.add_event_detect(BUTTONS[0], GPIO.FALLING, callback=next_track, bouncetime=1000) #ustaw eventy
GPIO.add_event_detect(BUTTONS[1], GPIO.FALLING, callback=prev_track, bouncetime=1000)
GPIO.add_event_detect(BUTTONS[2], GPIO.FALLING, callback=stop_track, bouncetime=1000)
GPIO.add_event_detect(BUTTONS[3], GPIO.FALLING, callback=pause_track, bouncetime=1000)
GPIO.add_event_detect(BUTTONS[4], GPIO.FALLING, callback=play_track, bouncetime=1000)
GPIO.add_event_detect(BUTTONS[5], GPIO.FALLING, callback=time_track, bouncetime=1000)

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

#auto jak sie piosenka zmienia sama
event_manager = player.event_manager()# Get the event manager from the player
event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, next_media_playing)# Register the callback

auto_time() #run showing time
while True:
    pass

''' for event which wxecution can be stopped
import threading

stop_event = False

def print_hello():
    global stop_event
    if not stop_event:
        print("Hello!")
        # Call this function again in 1 second
        threading.Timer(1, print_hello).start()

print_hello()

# When you want to stop the event, set stop_event to True
# stop_event = True
'''