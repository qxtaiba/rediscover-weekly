# [(re)Discover Weekly](https://open.spotify.com/playlist/2mULMNIOjAkmgJvE6J7YhL?si=b167f382262c426c)

This script allows you to synchronizes songs from a source playlist to a target playlist using the Spotify API. The function is triggered by a scheduled event in AWS CloudWatch Events, which executes the function at a specified time interval using a cron schedule. 

## Architecture 

The script is written in Python and is orchestrated the following AWS services:

- **AWS Lambda**: the function is hosted on the Lambda service.
- **AWS Secrets Manager**: stores the client ID, client secret, and refresh token, access token, and expiry time for the Spotify API.
- **AWS CloudWatch Events**: function is triggered by a scheduled event created using CloudWatch Events.
- **AWS CodeBuild**: builds and deploys the Lambda function to AWS.

```
        +-------------------------+
        |    CloudWatch Events    |
        +-------------------------+
                    |
                    v
            +-----------------+      +--------------------+
            |   AWS Lambda    | < -- |   AWS Code Build   |
            +-----------------+      +--------------------+
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

1. The Lambda function source code is pushed to the AWS CodeCommit repository.
2. AWS CodeBuild builds the Lambda function from the source code.
3. The built function is deployed to AWS Lambda.
4. The Lambda function is triggered by the scheduled event from CloudWatch Events.
5. The function retrieves the client ID, client secret, and refresh token from AWS Secrets Manager.
6. The function then retrieves the access token and its expiry time from AWS Secrets Manager, refreshing if needed. 
7. The function initializes the Spotify object with the access token.
8. The function retrieves the tracks in the source playlist and the target playlist.
9. The function filters out the tracks that already exist in the target playlist.
10. The function adds the new tracks to the target playlist.
11. The function returns the number of new tracks added to the target playlist.

## Requirements 

In order to use this implementation, you need:

- AWS Account
- Spotify Premimum Account
- The following AWS services:


    - AWS Lambda
    - AWS Secrets Manager
    - AWS CloudWatch Events
    - AWS CodeCommit
    - AWS CodeBuild
