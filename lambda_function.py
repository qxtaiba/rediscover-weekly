import base64
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import boto3
import json
import time
import re

def lambda_handler(event, context):
    # Define URL for source and target playlists
    SOURCE_PLAYLIST_URL = 'https://open.spotify.com/playlist/37i9dQZEVXcCKUxFWSD1WC?si=b67b01499f314f9c'
    TARGET_PLAYLIST_URL = 'https://open.spotify.com/playlist/2mULMNIOjAkmgJvE6J7YhL?si=373ae7ba488d4050'

    # Initialise the Secretes Manager client and get Spotify credentials
    secrets_manager = boto3.client('secretsmanager')
    secrets_response = secrets_manager.get_secret_value(SecretId='spotify-credentials')
    secrets_json = json.loads(secrets_response['SecretString'])

    # Get the Spotify client ID and secret from Secrets Manager
    client_id = secrets_json['spotify_client_id']
    client_secret = secrets_json['spotify_client_secret']

    # Get the refresh token, access token, and its expiry time from Secrets Manager
    refresh_token = secrets_json['refresh_token']
    access_token = secrets_json['access_token']
    expires_at = secrets_json['expires_at']

    # Refresh the access token if it has expired
    if time.time() > float(expires_at):
        access_token, expires_at = refresh_token_method(refresh_token, client_id, client_secret)
        
        # Update the Secrets Manager secret with the new access token and expiry time
        secrets_manager.update_secret(SecretId='spotify-credentials', SecretString=json.dumps({
            'access_token': access_token, 
            'expires_at': expires_at,
            'spotify_client_id': client_id,
            'spotify_client_secret': client_secret,
            'refresh_token': refresh_token
        }))

    # Initialize the Spotify object with the refreshed access token
    sp = spotipy.Spotify(auth=access_token)

    # Get the tracks in the source playlist
    source_playlist_id = extract_playlist_id(SOURCE_PLAYLIST_URL)
    source_track_uris = get_playlist_tracks(sp, source_playlist_id)

    # Get the tracks in the target playlist
    target_playlist_id = extract_playlist_id(TARGET_PLAYLIST_URL)
    target_track_uris = get_playlist_tracks(sp, target_playlist_id)

    # Filter out the tracks that already exist in the target playlist
    new_track_uris = list(set(source_track_uris) - set(target_track_uris))

    # Add the new tracks to the target playlist
    if len(new_track_uris) > 0:
        add_tracks_to_playlist(sp, target_playlist_id, new_track_uris)
        return {'statusCode': 200, 'body': '{} new tracks added to target playlist'.format(len(new_track_uris))}
    else:
        return {'statusCode': 200, 'body': 'No new tracks to add to target playlist'}

def extract_playlist_id_regex(playlist_url):
    regex = r'^https://open.spotify.com/playlist/([a-zA-Z0-9]+)\??.*$'
    match = re.match(regex, playlist_url)
    if match:
        return match.group(1)
    raise ValueError('Invalid Playlist URL')

def extract_playlist_id(playlist_url):
    prefix = 'https://open.spotify.com/playlist/'
    if playlist_url.startswith(prefix):
        return playlist_url.split('/')[-1].split('?')[0]
    raise ValueError('Invalid Playlist URL')

def get_playlist_tracks(sp, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return [track['track']['uri'] for track in tracks]

def add_tracks_to_playlist(sp, playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)

def refresh_token_method(refresh_token, client_id, client_secret):
    # Set the request parameters
    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": "Basic " + base64.b64encode((client_id + ":" + client_secret).encode()).decode()}
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    # Send the POST request to the Spotify Accounts service to retrieve an access token
    response = requests.post(url, data=payload, headers=headers)

    # Handle any errors that occur during the token refresh process
    if response.status_code != 200:
        raise ValueError("Could not refresh access token: {}".format(response.content))

    # Extract the access token and expiry time from the response
    token_info = response.json()
    access_token = token_info.get("access_token")
    expires_at = token_info.get("expires_in") + int(time.time())

    # If the access token is not in the response, raise an error
    if not access_token:
        raise ValueError("Could not extract access token from response: {}".format(response.content))

    return access_token, expires_at