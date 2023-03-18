# (re)Discover Weekly

This AWS Lambda function synchronizes tracks from a source playlist to a target playlist using the Spotify API. The function is triggered by a scheduled event in AWS CloudWatch Events, which executes the function at a specified time interval.

## Architecture 

The Lambda function is written in Python and utilizes the following AWS services:

- **AWS Lambda**: the function is hosted on the Lambda service.
- **AWS Secrets Manager**: stores the client ID, client secret, and refresh token for the Spotify API.
- **AWS CloudWatch Events**: the function is triggered by a scheduled event created using CloudWatch Events.

```
        +-------------------------+
        |    CloudWatch Events    |
        +-------------------------+
                    |
                    v
            +-----------------+
            |   AWS Lambda    |
            +-----------------+
                    |
                    v
            +-----------------+
            | Secrets Manager |
            +-----------------+
                    |
                    v
            +-----------------+
            |   Spotify API   |
            +-----------------+
```

The function flow is as follows:

1. The Lambda function is triggered by the scheduled event from CloudWatch Events.
2. The function retrieves the client ID, client secret, and refresh token from AWS Secrets Manager.
3. The function then retrieves the access token and its expiry time from AWS Secrets Manager, refreshing if needed. 
4. The function initializes the Spotify object with the access token.
5. The function retrieves the tracks in the source playlist and the target playlist.
6. The function filters out the tracks that already exist in the target playlist.
7. The function adds the new tracks to the target playlist.
8. The function returns the number of new tracks added to the target playlist.

## Requirements 

In order to use this implementation, you need:

- AWS Account
- Spotify Premimum Account
- The following AWS services:


    - AWS Lambda
    - AWS Secrets Manager
    - AWS CloudWatch Events

## Installation and Configuration

### Create a Spotify App

1. Log in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Click the "Create an App" button and follow the prompts to create a new Spotify app.
3. Add http://localhost:8080/callback/ to the Redirect URIs in the Spotify app settings.
4. Once your app is created, make note of the Client ID and Client Secret values.
5. In order to generate your initial refresh token, follow [this](https://benwiz.com/blog/create-spotify-refresh-token/) guide 

### Store Spotify Credentials in AWS Secrets Manager

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/).
2. Navigate to the AWS Secrets Manager service.
3. Create a new secret with the following key-value pairs:

    ```
    {
      "spotify_client_id": "<YOUR_SPOTIFY_CLIENT_ID>",
      "spotify_client_secret": "<YOUR_SPOTIFY_CLIENT_SECRET>",
      "refresh_token": "<YOUR_SPOTIFY_REFRESH_TOKEN>"
    }
    ```
    

### Create and Configure the Lambda Function

1. Log in to the AWS Management Console.
2. Navigate to the AWS Lambda service.
3. Create a new Lambda function with the following settings:

    - Runtime: Python 3.8
    - Execution Role: New role with basic permissions to access Secrets Manager and CloudWatch Logs.

4. Copy and paste the code from the provided `lambda_function.py` script into the Lambda function editor.
5. Set the `source_playlist_id` and `target_playlist_id` variables in the code to the Spotify IDs of the source and target playlists.
6. Save the Lambda function.
7. Create a new scheduled event in AWS CloudWatch Events to trigger the Lambda function at a specified time interval.

## Usage

The Lambda function will automatically run at the specified time interval and add any new tracks from the source playlist to the target playlist. You can monitor the execution of the Lambda function in the CloudWatch Logs.
