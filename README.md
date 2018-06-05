Create YouTube Playlists from  Set Lists
========================================

[![License](https://img.shields.io/badge/License-GPL3-blue.svg)](COPYING)

This is a Python script that will take a text file with your cover tunes set list
and create a YouTube playlist containing videos for all the songs in the list.
Perfect for the music director of a working cover band to create playlists to break
in new tunes or new players.

When run, the script reads in the text file. Since it uses youtube's search function
it doesn't need to be a specific format. Each line can be as simple as the song name
and the band that does it. If there is a specific version you'd like to include, just
put in the title as it shows on youtube (e.g. Long version, or metal version).  For 
each line in the list, it searches YouTube for a video of each song and adds the 
first result to a playlist with the title you specified.

This program is built from [Adam Goforth's Billboard Top N Playlist creator](https://github.com/aag/billboard_yt_playlist_creator). Finding his work allowed me to get this working within an house. GPL FTW!

Also note that while this works it is super crufty right now. I'm not sure if the pipenv bits
work at all. There is next to zero argument checking. Running it like this works:

```sh
python3 createsetplaylist.py -l setlist -t "Test Set Play List"
```

An example of what the script creates can be seen here:

https://www.youtube.com/playlist?list=PL3YYv-ltyAmMX-H2CwI9h4awPRAauJ2PI

Dependencies
------------
This script depends on Python 3.4 and these Python packages:
- [Google API v3 Client Library for Python](https://developers.google.com/api-client-library/python/)

Usage
-----
1. Clone the git repository.

2. Install the Python dependencies with [pipenv](https://docs.pipenv.org/).
    Run this command within the root directory of the repository:

    ```sh
    $ pipenv install
    ```

3. Create a new project in the
    [Google Developer Console](https://console.developers.google.com/)
    by clicking the "Select a project" dropdown in the header and clicking the
    "Create a project" button. Give the project any name you like. After
    creating the project, open it if it isn't opened automatically.

4. Enable the Youtube Data API in the Library tab of your 
    [Google Developer Console](https://console.developers.google.com/). Open the
    "Library" tab, then click the "Youtube Data API" link and click the "Enable"
    link.

5. Create an API key. Go to the Credentials tab in the
    [Google Developer Console](https://console.developers.google.com/)
    and click "Create credentials". Select "API key" from the dropdown.

6. Create a new client ID. Still on the Credentials tab of the Google Developer
    console, click "Create credentials". Select "OAuth client ID" from the list
    and select the application type "Other". Click the "Create" button. Click
    "OK" in the modal dialog that appears. The new client ID should appear on
    the Credentials page. Click the "Download JSON" button for your new client
    ID. A download of the JSON key will start in your browser. Save the file
    with the name `client_secrets.json` in the root directory of your clone of
    the git repository.

7. Copy `settings-example.cfg` to `settings.cfg` and fill in the API key you
    created in step #5. Then run:

    ```sh
    $ pipenv run python createsetplaylist.py --noauth_local_webserver
    ```

8. The first time you run the script, you will have to authenticate the
    application in a web browser. Open the URL that the script outputs,
    approve the application for the YouTube Account in which you want to
    create the playlists, and enter the verification code on the command line.
    This will create a file, `oauth2.json`, which must be kept in the root
    of the git repository as long as you want to upload playlists to this
    account.

9. In subsequent runs of the script, you can run it without any command line
    arguments:

    ```sh
    $ pipenv run python createsetplaylist.py
    ```

Troubleshooting
---------------
If the script was working, but you start getting HttpError 404 responses with
the message "Channel not found.", you may have to re-authorize the application.
Do this by deleting the `oauth2.json` file and running the script
with `--noauth_local_webserver`.

License
-------
This code is free software licensed under the GPL 3. See the
[LICENSE.md](LICENSE.md) file for details.
