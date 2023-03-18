import base64
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import boto3
import json
import time

def lambda_handler(event, context):
    # Get the Spotify client ID and secret from the Secrets Manager secret
    secrets_manager = boto3.client('secretsmanager')
    secrets_response = secrets_manager.get_secret_value(SecretId='spotify-credentials')
    secrets_json = json.loads(secrets_response['SecretString'])

    client_id = secrets_json['spotify_client_id']
    client_secret = secrets_json['spotify_client_secret']
    refresh_token = secrets_json['refresh_token']

    # Get the cached access token and its expiry time from the Secrets Manager secret
    access_token = secrets_json['access_token']
    expires_at = secrets_json['expires_at']

    # Refresh the access token if it has expired
    if time.time() > float(expires_at):
        access_token, expires_at = refresh_token_method(refresh_token, client_id, client_secret)
        
        # Update the Secrets Manager secret with the new access token and expiry time
        secrets_manager.update_secret(SecretId='spotify-credentials', SecretString=json.dumps({'access_token': access_token, 'expires_at': expires_at}))

    # Initialize the Spotify object with the refreshed access token
    sp = spotipy.Spotify(auth=access_token)

    # Get the tracks in the source playlist
    source_playlist_id = "37i9dQZEVXcCKUxFWSD1WC"
    source_track_uris = get_playlist_tracks(sp, source_playlist_id)

    # Get the tracks in the target playlist
    target_playlist_id = "2mULMNIOjAkmgJvE6J7YhL"
    target_track_uris = get_playlist_tracks(sp, target_playlist_id)

    # Filter out the tracks that already exist in the target playlist
    new_track_uris = list(set(source_track_uris) - set(target_track_uris))

    # Add the new tracks to the target playlist
    if len(new_track_uris) > 0:
        add_tracks_to_playlist(sp, target_playlist_id, new_track_uris)
        return {'statusCode': 200, 'body': '{} new tracks added to target playlist'.format(len(new_track_uris))}
    else:
        return {'statusCode': 200, 'body': 'No new tracks to add to target playlist'}

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