import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import boto3
import json
from datetime import datetime, timedelta


def lambda_handler(event, context):
    # Get the Spotify client ID and secret from the Secrets Manager secret
    secrets_manager = boto3.client('secretsmanager')
    secrets_response = secrets_manager.get_secret_value(SecretId='spotify-credentials')
    secrets_json = json.loads(secrets_response['SecretString'])
    client_id = secrets_json['spotify_client_id']
    client_secret = secrets_json['spotify_client_secret']
    
    # Get the access token and its expiry time from Secret Manager
    access_token, expires_at = get_access_token_from_secret(secrets_manager, client_id, client_secret)

    # If access token is expired or about to expire, generate a new access token
    if is_access_token_expired(expires_at):
        access_token = generate_access_token(client_id, client_secret, secrets_manager)
        
    # Create a Spotipy client
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret, access_token=access_token)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

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


def get_access_token_from_secret(secrets_manager, client_id, client_secret):
    secrets_response = secrets_manager.get_secret_value(SecretId='spotify-credentials')
    secrets_json = json.loads(secrets_response['SecretString'])
    access_token = secrets_json['access_token']
    expiry_time = datetime.fromisoformat(secrets_json['expiry_time'])
    return access_token, expiry_time


def is_access_token_expired(expiry_time):
    return expiry_time - timedelta(minutes=5) <= datetime.now()


def generate_access_token(client_id, client_secret, secrets_manager):
    token_url = 'https://accounts.spotify.com/api/token'
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    access_token = sp._auth_manager.get_access_token()
    expires_at = datetime.now() + timedelta(seconds=access_token['expires_in'])
    # Store the new access token and expiry time in Secret Manager
    secrets_manager.put_secret_value(SecretId='spotify-access-token', SecretString=json.dumps({
        'access_token': access_token['access_token'],
        'expiry_at': expires_at.isoformat()
    }))
    return access_token['access_token']



def get_playlist_tracks(sp, playlist_id):
    results = sp.playlist_items(playlist_id, fields='items.track.uri,total', additional_types=['track'])
    tracks = results['items']
    while results.get('next'):
        results = sp.next(results)
        tracks.extend(results['items'])
    return [track['track']['uri'] for track in tracks]

def add_tracks_to_playlist(sp, playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)
