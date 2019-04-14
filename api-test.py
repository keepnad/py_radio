#!/usr/bin/env python3
import json
import requests
import vlc
import time
import signal
import sys

# Run a listener to exit nicely on ctrl+c
def exit_handler(signal, frame):
    print(' SIGINT caught -- Exiting...')
    sys.exit(0)

def main():

    print('----- Terminal Radio -----')
    print('----- Ctrl + C exits -----')
    print('\nAvailable local stations:\n')
    signal.signal(signal.SIGINT, exit_handler)

    # create instance of py-vlc
    instance = vlc.Instance('--input-repeat=-1', '--fullscreen')
    player = instance.media_player_new()

    # read in live stations
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'false'),
        ('limit', '-1'),
        ('offset', '0'),
        ('useIP', 'true'),
    )
    response = requests.get(url, headers=headers, params=params)
    a = response.json()
    #print(a['hits'][0]['markets'])
    #return

    # print out and number local stations
    for i in range(0, a['total']):
        if a['hits'][i]['markets'][0]['name'] == 'SANANTONIO-TX':
            name = a['hits'][i]['name']
            desc = a['hits'][i]['description']
            print('%d:\t%s - %s' % (i + 1, name, desc))

    # select a station to listen to
    good_input = False
    print('\nPick a station:')
    while good_input == False:
        try:
            channel_num = int(input())
            channel_num -= 1
        except ValueError:
            print('Enter a number corresponding to a station')
            continue
        if channel_num >= a['total'] or channel_num < 0:
            print('Enter a number corresponding to a station')
            continue
        else:
            good_input = True

    # if it is an hls stream, get metadata
    try:
        b = requests.get(a['hits'][channel_num]['streams']['hls_stream'])
        c = b.text.split('\n')
        d = requests.get(c[2])
        e = d.text.split('\n')

        e[4] = e[4].replace('\\', '')
        #print(e[4])

        title_start = e[4].find('title') + 7
        title_end = e[4].find('"', title_start)
        #print(e[4][title_start])
        #print(e[4][title_end])
        title = e[4][title_start : title_end]

        artist_start = e[4].find('artist') + 8
        artist_end = e[4].find('"', artist_start)
        #print(e[4][artist_start])
        #print(e[4][artist_end])
        artist = e[4][artist_start : artist_end]

        img_url_start = e[4].find('amgArtworkURL') + 15
        img_url_end = e[4].find('"', img_url_start)
        #print(e[4][img_url_start])
        #print(e[4][img_url_end])
        img_url = e[4][img_url_start : img_url_end]
        print('Now Playing:', title,'-', artist, '\n', img_url)

    except KeyError:
        pass

    # play stream
    for stream_type, url in a['hits'][channel_num]['streams'].items():
        if url[0:5] == 'http:':
            print(a['hits'][channel_num]['name'], '-', a['hits'][channel_num]['description'])
            print('stream URL:', url)
            media = instance.media_new(url)
            player.set_media(media)
            player.play()
            while True:
                time.sleep(.5)
        else:
            continue

if __name__ == "__main__":
    main()
