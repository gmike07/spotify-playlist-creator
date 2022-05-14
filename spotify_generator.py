try:
    from six.moves.BaseHTTPServer import HTTPServer
    from Requesthandler import RequestHandler
    import requests
    import webbrowser
    import six.moves.urllib.parse as urllibparse
    import json
    import random
except ModuleNotFoundError as e:  # to install packages and restart if needed
    import os
    import sys
    os.system('pip install six')
    os.system('pip install requests')
    os.system('pip install webbrowser')
    os.startfile(sys.argv[0])
    sys.exit()


def start_local_http_server(port, handler=RequestHandler):
    server = HTTPServer(("127.0.0.1", port), handler)
    server.allow_reuse_address = True
    server.auth_code = None
    server.auth_token_form = None
    server.error = None
    return server


class spotifyClient:

    def __init__(self, clientID, clientSecret, port=7777):
        self.port = port
        self.redirect_uri = f'http://localhost:{self.port}'
        self.clientID = clientID
        self.clientSecret = clientSecret
        print('waiting to authenticate...')
        code = self.get_code_token()
        self.api_key = self.get_api_token(code)
        self.userID = self.get_user_id()

    def get_code_token(self):
        scopes = 'user-top-read user-read-recently-played ' \
                 'playlist-read-private playlist-read-collaborative ' \
                 'playlist-modify-public playlist-modify-private ' \
                 'user-library-modify user-library-read user-read-email ' \
                 'user-read-private app-remote-control streaming ugc-' \
                 'image-upload user-read-playback-position ' \
                 'user-read-playback-state user-modify-playback-state ' \
                 'user-read-currently-playing'
        server = start_local_http_server(self.port)
        webbrowser.open(self.get_authorize_url(scopes))
        server.handle_request()
        return server.auth_code

    def get_api_token(self, code):
        url = "https://accounts.spotify.com/api/token"
        payload = {
            "client_id": self.clientID,
            "client_secret": self.clientSecret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, data=payload, verify=True, headers=headers)
        response_json = response.json()
        token = response_json['access_token']
        return token

    def get_authorize_url(self, scopes):
        payload = {
            "client_id": self.clientID,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            'scope': scopes,
            'show_dialog': True
        }
        urlparams = urllibparse.urlencode(payload)

        return "%s?%s" % ('https://accounts.spotify.com/authorize', urlparams)

    def get_top_tracks(self, offset=0, time_range='medium_term', limit=50):
        url = f'https://api.spotify.com/v1/me/top/tracks?limit={limit}&offset={offset}&time_range={time_range}'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response_json = response.json()
        return response_json

    def get_top_artists(self, offset=0, time_range='medium_term', limit=50):
        url = f'https://api.spotify.com/v1/me/top/artists?limit={limit}&offset={offset}&time_range={time_range}'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response_json = response.json()
        return response_json

    def get_recently_played(self, limit=50):
        url = f'https://api.spotify.com/v1/me/player/recently-played?limit={limit}'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response_json = response.json()
        return response_json

    def get_top_recommendations(self, offset, term):
        uris = get_top_tracks(self, offset, term)
        url = f'https://api.spotify.com/v1/recommendations'

        # can only have 5 seeds
        uris = random.choices(list(uris), k=5)
        uris = [uri[len("spotify:track:"):] for uri in uris]

        payload = dict()
        payload['seed_tracks'] = ','.join(uris)
        urlparams = urllibparse.urlencode(payload)
        response = requests.get(
            "%s?%s" % (url, urlparams),
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response_json = response.json()
        return response_json['tracks']

    def get_songs_in_playlist(self, playlist_id):
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response_json = response.json()
        return response_json['tracks']

    def create_playlist(self, playlist_name, public=False):
        url = f'https://api.spotify.com/v1/users/{self.userID}/playlists'
        data = json.dumps({
            'public': public,
            'name': playlist_name,
            'description': 'Recommended songs'
        })
        response = requests.post(
            url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            },
            data=data
        )
        response_json = response.json()
        return response_json['id']

    def get_playlists_name(self):
        url = f'https://api.spotify.com/v1/me/playlists'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response_json = response.json()
        return response_json['items']

    def get_user_id(self):
        url = f'https://api.spotify.com/v1/me'
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response_json = response.json()
        return response_json['id']

    def add_song_to_playlist(self, playlist_id, uris):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        # can only add 100 each time
        request_body = json.dumps({"uris": uris[:100]})
        response = requests.post(url, data=request_body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f'Bearer {self.api_key}'})
        return response.ok


def get_recently_played_uris(spotify_client):
    return {song['track']['uri'] for song in spotify_client.get_recently_played()['items']}


def get_in_playlist(spotify_client, playlist_id):
    return {song['track']['uri'] for song in spotify_client.get_songs_in_playlist(playlist_id)['items']}


def get_top_tracks(spotify_client, offset, time_range):
    return {song['uri'] for song in spotify_client.get_top_tracks(offset, time_range)['items']}


def get_top_artists(spotify_client, offset, time_range):
    return {song['id'] for song in spotify_client.get_top_artists(offset, time_range)['items']}


def get_top_recommendations(spotify_client, offset, time_range):
    uris = spotify_client.get_top_recommendations(offset, time_range)
    return {song['uri'] for song in uris}


def find_good_uris(spotify_client, playlist_id, n=30):
    uris = set()
    terms = ['long_term', 'medium_term', 'short_term']
    offset = 0
    while len(uris) < n:
        helper = set()
        for term in terms:
            helper |= get_top_tracks(spotify_client, offset, term)
        uris |= helper
        uris -= get_recently_played_uris(spotify_client)
        uris -= get_in_playlist(spotify_client, playlist_id)
        if len(uris) > n:
            break

        for term in terms:
            helper |= get_top_recommendations(spotify_client, 0, term)
        uris |= helper
        uris -= get_recently_played_uris(spotify_client)
        uris -= get_in_playlist(spotify_client, playlist_id)
        offset += 50
    return list(uris)[:n]


def find_playlist_id(playlists, playlist_name, playlist_id):
    for playlist in playlists:
        if playlist['name'] == playlist_name:
            return playlist['id']
    return playlist_id


def create_playlist(spotify_client, playlist_name):
    print('getting existing playlists...')
    playlists = spotify_client.get_playlists_name()
    print('searching playlist...')
    playlist_id = find_playlist_id(playlists, playlist_name, '')
    if playlist_id == '':
        print("playlist doesn't exists, creating now...")
        playlist_id = spotify_client.create_playlist(playlist_name)
    else:
        print('found playlist...')
    print('finding good songs to add to playlist...')
    uris = find_good_uris(spotify_client, playlist_id)
    print('adding songs to playlist...')
    spotify_client.add_song_to_playlist(playlist_id, uris)
    print('Done!')


if __name__ == '__main__':
    # secret to use the api
    _clientID = 'aaa'
    _clientSecret = 'aaa'

    sc = spotifyClient(_clientID, _clientSecret)
    create_playlist(sc, 'nostalgic_recommendation_new')
