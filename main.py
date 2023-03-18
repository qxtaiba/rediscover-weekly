import os
import time
import boto3
import base64
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Get the Spotify client ID and secret from the Secrets Manager secret
secrets_manager = boto3.client('secretsmanager')
secrets_response = secrets_manager.get_secret_value(SecretId='spotify-credentials')
secrets_json = json.loads(secrets_response['SecretString'])
client_id = secrets_json['spotify_client_id']
client_secret = secrets_json['spotify_client_secret']

# Create the Spotify auth manager
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri='http://localhost:8888/callback',
                                               scope=["user-library-read", "playlist-modify-public", "playlist-modify-private"]))
print("Auth manager created")
access_token = sp.auth_manager.get_access_token(as_dict=False)
print("Access token retrieved")

# Get the tracks in the source playlist
source_playlist_id = "37i9dQZEVXcCKUxFWSD1WC"
source_results = sp.playlist_tracks(source_playlist_id)
source_track_uris = [item['track']['uri'] for item in source_results['items']]

# Get the tracks in the target playlist
target_playlist_id = "2mULMNIOjAkmgJvE6J7YhL"
target_results = sp.playlist_tracks(target_playlist_id)
target_track_uris = [item['track']['uri'] for item in target_results['items']]

# Filter out the tracks that already exist in the target playlist
new_track_uris = list(set(source_track_uris) - set(target_track_uris))

# Add the new tracks to the target playlist
if len(new_track_uris) > 0:
    sp.playlist_add_items(target_playlist_id, new_track_uris)
    print('{} new tracks added to target playlist'.format(len(new_track_uris)))
else:
    print('No new tracks to add to target playlist')
