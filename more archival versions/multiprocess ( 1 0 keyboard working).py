import vlc #play music
import time #control time
import discid #read discid
import musicbrainzngs #fetch data
import sys
import cdio, pycdio #cdtxt & trackcount
from multiprocessing import Process, Pipe
import threading #scheduling
from math import floor#round down
track_list = []
data = {"Autor" : "Unknown", "Album": "Unknown"}
i_tracks = 0
command = 0 # 0-nothing 1-play 2-pause 3-stop 4-next 5-prev
kill = False

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
        conn.send([index+1, i_tracks, track_list[index], data["Autor"], data["Album"], floor(player.get_time()/1000), floor(player.get_length()/1000), dump])
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
    global songnumber, track_list, data, i_tracks, command
    if cdplayer.is_alive():
        parent_conn.send(command)
        time.sleep(0.1)
        command=0
        dump=parent_conn.recv()
        print(dump)
    P=threading.Timer(1, PlayerGlobalSync)
    P.start()



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

