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
    
    # Authenticate using SpotifyOAuth and get a new access token if needed
    auth_manager = SpotifyOAuth(client_id=client_id,
                                client_secret=client_secret,
                                redirect_uri="http://127.0.0.1:8888/callback",
                                scope=["playlist-modify-public"],
                                cache_path=".spotifycache")
    
    if auth_manager.get_cached_token() is None or time.time() > auth_manager.get_cached_token()['expires_at'] - 300:
        auth_manager.refresh_access_token(refresh_token)
    access_token = auth_manager.get_cached_token()['access_token']

    # Get the tracks in the source playlist
    sp = spotipy.Spotify(auth_manager=auth_manager)
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
