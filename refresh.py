from spotipy.oauth2 import SpotifyOAuth

# Set up the Spotify OAuth2 client
scope = 'playlist-modify-public'
client_id = '8ccf8e72abe2405a82520079efb3a627'
client_secret = 'bbc9f00b70fd458c9580818093801b43'
redirect_uri = 'http://127.0.0.1:8888/callback'
auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)

# Get the authorization URL to retrieve the authorization code
auth_url = auth_manager.get_authorize_url()
print("Please visit this URL to authorize the application:", auth_url)

# After the user authorizes the application, get the authorization code from the redirect URL
redirect_response = input("Paste the full redirect URL here:")
auth_manager.get_access_token(redirect_response)

# Print the refresh token to the console
print("Refresh token:", auth_manager.refresh_token)
