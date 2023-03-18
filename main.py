import subprocess
subprocess.check_call(["pip", "install", "requests", "-t", "/tmp"])
import sys
sys.path.append("/tmp")

import requests
import base64
import json
import time
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    # Get the Spotify client ID and secret from the Secrets Manager secret
    secrets_manager = boto3.client('secretsmanager')
    secrets_response = secrets_manager.get_secret_value(SecretId='spotify-credentials')
    secrets_json = json.loads(secrets_response['SecretString'])
    client_id = secrets_json['spotify_client_id']
    client_secret = secrets_json['spotify_client_secret']
    
    # Get the access token and its expiry time
    access_token, expires_at = get_access_token(client_id, client_secret)
    
    # Get the tracks in the source playlist
    source_playlist_id = "37i9dQZEVXcCKUxFWSD1WC"
    source_track_uris = get_playlist_tracks(source_playlist_id, access_token)
    
    # Get the tracks in the target playlist
    target_playlist_id = "2mULMNIOjAkmgJvE6J7YhL"
    target_track_uris = get_playlist_tracks(target_playlist_id, access_token)
    
    # Filter out the tracks that already exist in the target playlist
    new_track_uris = list(set(source_track_uris) - set(target_track_uris))
    # Add the new tracks to the target playlist
    if len(new_track_uris) > 0:
        add_tracks_to_playlist(target_playlist_id, new_track_uris, access_token)
        return {'statusCode': 200, 'body': '{} new tracks added to target playlist'.format(len(new_track_uris))}
    else:
        return {'statusCode': 200, 'body': 'No new tracks to add to target playlist'}

def get_access_token(client_id, client_secret):
    token_url = 'https://accounts.spotify.com/api/token'
    headers = {'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode()).decode()}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(token_url, headers=headers, data=data)
    response_data = json.loads(response.text)
    access_token = response_data['access_token']
    expires_in = response_data['expires_in']
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    return access_token, expires_at

def get_playlist_tracks(playlist_id, access_token):
    playlist_url = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id)
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(playlist_url, headers=headers)
    response_data = json.loads(response.text)
    return [item['track']['uri'] for item in response_data['items']]

def add_tracks_to_playlist(playlist_id, track_uris, access_token):
    playlist_url = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id)
    headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    data = json.dumps({'uris': track_uris})
    response = requests.post(playlist_url, headers=headers, data=data)
    response.raise_for_status()

def get_new_access_token(client_id, client_secret, current_access_token, current_expiry):
    # Check if the current access token has expired
    if datetime.now() < current_expiry:
        return current_access_token, current_expiry

    # Get a new access token and its expiry time
    access_token, expires_at = get_access_token(client_id, client_secret)
    return access_token, expires_at
