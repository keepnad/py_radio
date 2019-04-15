#!/usr/bin/env python3
import requests
import vlc
import time
import signal
import sys

# Run a listener to exit nicely on ctrl+c
def exit_handler(signal, frame):
    print(' SIGINT caught -- Exiting...')
    sys.exit(0)

# return a track name given track id
def name_from_id(track_id):
    url='http://us-qa.api.iheart.com/api/v1/catalog/getTrackByTrackId'
    headers = {'Accept': 'application/json'}
    params = (
        ('trackId', track_id),
    )
    return requests.get(url, headers=headers, params=params).json()['track']['title']

# reutrn an album genre given album id
def genre_from_album(album_id):
    url = 'http://us-qa.api.iheart.com/api/v1/catalog/getAlbumsByAlbumIds'
    headers = {'Accept': 'application/json'}
    params = (
        ('albumId', album_id),
    )
    return requests.get(url, headers=headers, params=params).json()['trackBundles'][0]['genre']

# return all stations in a dictionary
def get_all_stations():
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'true'),
        ('limit', '-1'),
        ('offset', '0'),
    )
    return requests.get(url, headers=headers, params=params).json()

# return stations near a given city
def get_locational_stations(city):
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'false'),
        ('limit', '-1'),
        ('offset', '0'),
        ('city', city),
    )
    return requests.get(url, headers=headers, params=params).json()

# return stations near the requesting IP
def get_local_stations():
    url = 'http://us-qa.api.iheart.com/api/v2/content/liveStations'
    headers = {'Accept': 'application/json'}
    params = (
        ('allMarkets', 'false'),
        ('limit', '-1'),
        ('offset', '0'),
        ('useIP', 'true'),
    )
    return requests.get(url, headers=headers, params=params).json()

# get stream urls, names, and desriptions from a bunch of stations
def load_station_dicts(a):

    station_urls = {}
    station_names = {}
    station_descs = {}

    # read values into dicts
    i = 0
    for x in range (a['total']):
        try:
            hls_url = a['hits'][x]['streams']['hls_stream']
            if hls_url != '':
                station_urls[i] = hls_url
                station_names[i] = a['hits'][i]['name']
                station_descs[i] = a['hits'][i]['description']
                i += 1
        except:
            continue

    return station_urls, station_names, station_descs, i

def main():
    print('----- Terminal Radio -----')
    print('\nAvailable local stations:\n')
    signal.signal(signal.SIGINT, exit_handler)

    # create instance of py-vlc
    instance = vlc.Instance('--input-repeat=-1', '--fullscreen')
    player = instance.media_player_new()

    # read in live stations
    a = get_local_stations()

    # dicts to store station values
    station_urls, station_names, station_descs, max_num = load_station_dicts(a)

    #print(station_urls)
    #return
    # loop to run radio after stopping, until quit
    while True:
        stop = False
        for k, v in station_names.items():
            print('%d:\t%s - %s' % (k + 1, station_names[k], station_descs[k]))

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
            if channel_num >= max_num or channel_num < 0:
                print('Enter a number corresponding to a station')
                continue
            else:
                good_input = True

        #print(requests.get(station_urls[channel_num]))
        #return

        # if it is an hls stream, get metadata
        try:
            b = requests.get(station_urls[channel_num])
            #print('works here')
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
            print('Now Playing:', title,'-', artist)

        except KeyError:
            title = ''
            artist = ''
            img_url = ''
        except IndexError:
            title = ''
            artist = ''
            img_url = ''
        except:
            print('Stream failed to open. Press enter to try another.\n')
            sys.stdin.read(1)
            continue

        # play stream
        print(a['hits'][channel_num]['name'], '-', a['hits'][channel_num]['description'])
        # print('stream URL:', url)
        media = instance.media_new(station_urls[channel_num])
        player.set_media(media)
        player.play()
        print('(q)uit program or (s)top playback')
        while True:
            time.sleep(.5)
            sig = sys.stdin.read(1)
            if sig == 'q':
                print('Exiting...')
                sys.exit(0)
            elif sig == 's':
                print('Stopping playback...')
                player.stop()
                break

if __name__ == "__main__":
    main()
