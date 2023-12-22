import vlc #play music
import time #control time
import discid #read discid
import musicbrainzngs #fetch data
import sys
import cdio, pycdio #cdtxt i trackcount

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

fetchdata()
print(data["Autor"],'\t',data["Album"])
print('\n')

instance = vlc.Instance() #uruchom vlc
player = instance.media_player_new()
medialist = instance.media_list_new()
listplayer = instance.media_list_player_new()
listplayer.set_media_player(player) 
#medialist.add_media("cdda:///dev/cdrom") #to laduje jako 1 medoim, wiec nie mozna odpalac np 6 piosenki
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


while True:
    dump = input()
    match dump: #sterowanie
        case "next":
            listplayer.next()
            next_media_playing(0)
        case "prev":
            listplayer.previous()
            if songnumber == 0:
                print("bardziej sie nie cofniesz")
            else:
                songnumber-=1
                print("Now playing: " , track_list[songnumber])
                time.sleep(0.25)
                print("Duration: ", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000))) #set_time(1000)
        case "pause":
            listplayer.pause()
            print("Paused at: ", time.strftime("%H:%M:%S", time.gmtime(player.get_time()/1000)), "---", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
        case "play":
            listplayer.play()
            print("Resuming ",track_list[songnumber])
        case "stop":
            listplayer.stop()
            songnumber=0
        case "exit":
            break
        case "time":
            print(time.strftime("%H:%M:%S", time.gmtime(player.get_time()/1000)), "---", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
        case "procent":
            print(round(player.get_position()*100,2), '%') #idealne do progress bara       set_position(0.2)
        case "media5":
            listplayer.play_item_at_index(4) #numeracja od 0
            songnumber=4
            print("Now playing: " , track_list[songnumber])
            time.sleep(0.25)
            print("Duration: ", time.strftime("%H:%M:%S", time.gmtime(player.get_length()/1000)))
        case _:
            print("zła komenda, spróbuj ponownie")


#player.get_media() gives <vlc.Media object at 0x7f8c3c2750>
#MediaPlayerForward, MediaPlayerBackward, 
#print(medialist.item_at_index(3)) #rozne testy
#print(medialist.item_at_index(5))
#print(medialist.item_at_index(3).get_mrl())
#print(medialist.count())