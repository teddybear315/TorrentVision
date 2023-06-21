# TorrentVision
 An easy way to setup a LAN web stream of your favorite shows and movies

## Installation:
* Download project zip
* Install ffmpeg (required)
* Install mediamtx (optional)
    - Use to redirect RTMP stream to HLS stream for viewing in browser
    - You can use the custom .yml file for best results
    - Here are a few recommended changes if you choose to use your own config
        * rtspDisable: yes
        * hlsAddress: :80
        * hlsAlwaysRemux: yes
        * rtspRangeType: clock
        * rtspRangeStart: clock
## Setup
Create a .json file for each channel you would like. There are 2 main modes for a channel, Movie Marathon, or TV Shows
* HD parameter does nothing at the moment
* shuffle can be "off"/false "files"/true "groups"/"seasons"
    - "files" shuffles all episodes
    - "groups"/"seasons" shuffles the seasons but not the episodes
* You can add movies but the file needs to be alone in a folder unless you want a whole series of movies in a folder
* If putting movie in show channel, use name of franchise if possible for show name, as file name will be used as the "episode name"
### Show Channel Example
    {
        "channel": 5,
        "type":"shows",
        "shuffle":"seasons",
        "shows": [
            {
                "name": "Star Wars",
                "seasons": [
                    {
                        "HD":false,
                        "path":"G:\\TV\\Star Wars\\The Clone Wars (2008)"
                    }
                ]
            },
            {
                "name": "The Regular Show",
                "seasons": [
                    {
                        "HD":true,
                        "path":"G:\\TV\\The Regular Show\\Season 1"
                    },
                    {
                        "HD":true,
                        "path":"G:\\TV\\The Regular Show\\Season 2"
                    },
                    {
                        "HD":true,
                        "path":"G:\\TV\\The Regular Show\\Season 3"
                    },
                    {
                        "HD":true,
                        "path":"G:\\TV\\The Regular Show\\Season 4"
                    }
                ]
            },
            {
                "name": "Star Wars: The Bad Batch",
                "seasons": [
                    {
                        "HD":true,
                        "path":"G:\\TV\\Star Wars\\The Clone Wars\\The Bad Batch\\Season 1"
                    },
                    {
                        "HD":true,
                        "path":"G:\\TV\\Star Wars\\The Clone Wars\\The Bad Batch\\Season 2"
                    }
                ]
            }
        ]
    }

### Movie Channel Example
    {
        "channel": 3,
        "type":"movies",
        "shuffle":false,
        "movies": [
            {
                "name": "Star Wars: Episode I - The Phantom Menace",
                "HD":true,
                "path" "
            },
            {
                "name": "Star Wars: Episode II - Attack of the Clones",
                "HD":true,
                "path": " "
            },
            {
                "name": "Star Wars: Episode III - Revenge of the Sith",
                "HD":true,
                "path": " "
            },
            {
                "name": "Star Wars: Episode IV - A new Hope",
                "HD":true,
                "path": " "
            },
            {
                "name": "Star Wars: Episode V - The Empire Strikes Back",
                "HD":true,
                "path": " "
            },
            {
                "name": "Star Wars: Episode VI - Return of the Jedi",
                "HD":true,
                "path": " "
            },
            {
                "name": "Star Wars: Episode VII - The Force Awakens",
                "HD":true,
                "path": " "
            },
            {
                "name": "Star Wars: Episode VIII - The Last Jedi",
                "HD":true,
                "path": " "
            },
            {
                "name": "Star Wars: Episode IX - The Rise of Skywalker",
                "HD":true,
                "path": " "
            }
        ]
    }