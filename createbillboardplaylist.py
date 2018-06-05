#!/usr/bin/python

"""
This is the Create Billboard Charts YouTube Playlist script
It is a Python script that will download some of the current Billboard charts
and create YouTube playlists containing videos for all the songs for the charts.
If it is run regularly, it will create new playlists each week for the new Billboard
charts.

An example of what the script creates can be seen here:
http://www.youtube.com/user/GimmeThatHotPopMusic
"""

# Copyright 2011-2018 Adam Goforth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import print_function
import argparse
import os.path
import time
from six.moves.configparser import SafeConfigParser
from datetime import datetime

import httplib2

# Google Data API
from apiclient.discovery import build
import oauth2client
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

# billboard.py
# import billboard

# Almost every function needs the YouTube resource, so define it globally
youtube = None


def get_video_id_for_search(query):
    """Returns the videoId of the first search result if at least one video
       was found by searching for the given query, otherwise returns None"""

    search_response = youtube.search().list(
        q=query,
        part="id,snippet",
        maxResults=1,
        safeSearch="none",
        type="video",
        fields="items"
    ).execute()

    items = search_response.get('items', [])
    if not items:
        return None

    for item in items:
        # The "type" parameter doesn't always work for some reason, so we have
        # to check each item for its type.
        if item['id']['kind'] == 'youtube#video':
            return item['id']['videoId']
        else:
            print("\tResult is not a video, continuing to next result")

    return None

def playlist_url_from_id(pl_id):
    """Returns the URL of a playlist, given its ID"""
    return "https://www.youtube.com/playlist?list={0}".format(pl_id)

def add_video_to_playlist(pl_id, video_id):
    """Adds the given video as the last video as the last one in the given
    playlist
    """
    print("\tAdding video pl_id: " + pl_id + " video_id: " + video_id)

    video_insert_response = youtube.playlistItems().insert(
        part="snippet",
        body=dict(
            snippet=dict(
                playlistId=pl_id,
                resourceId=dict(
                    kind="youtube#video",
                    videoId=video_id
                )
            )
        ),
        fields="snippet"
    ).execute()

    title = video_insert_response['snippet']['title']

    print('\tVideo added: {0}'.format(title.encode('utf-8')))

def add_first_found_video_to_playlist(pl_id, search_query):
    """Does a search for videos and adds the first result to the given playlist"""
    video_id = get_video_id_for_search(search_query)

    # No search results were found, so print a message and return
    if video_id is None:
        print(("No search results found for '" + search_query + "'. "
              "Moving on to the next song."))
        return

    add_video_to_playlist(pl_id, video_id)

def create_new_playlist(title, description):
    """Creates a new, empty YouTube playlist with the given title and description"""
    playlists_insert_response = youtube.playlists().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
                title=title,
                description=description
            ),
            status=dict(
                privacyStatus="public"
            )
        ),
        fields="id"
    ).execute()

    pl_id = playlists_insert_response['id']
    pl_url = playlist_url_from_id(pl_id)

    print("New playlist added: {0}".format(title))
    print("\tID: {0}".format(pl_id))
    print("\tURL: {0}".format(pl_url))

    return pl_id

def playlist_exists_with_title(title):
    """Returns true if there is already a playlist in the channel with the given name"""
    playlists = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=10,
        fields="items"
    ).execute()

    for playlist in playlists['items']:
        if playlist['snippet']['title'] == title:
            return True

    return False

def add_chart_entries_to_playlist(pl_id, entries):
    """Given the list of entries from a billboard.py listing, search for a video for each
    entry and add it to the given playlist
    """
    song_count = 0
    for entry in entries:
        song_count += 1
        if song_count > 100:
            break

        print('Adding ' + entry)
        add_first_found_video_to_playlist(pl_id, entry)

    print("\n---\n")

def create_playlist_from_chart(options):
    """Create and populate a new playlist with the current Billboard chart with the given ID"""
    # Read in setlist file
    #chart = billboard.ChartData(chart_id)
    with open(options.list) as data_file:
        chart = data_file.read().splitlines()
    print(chart)

    # Create a new playlist, if it doesn't already exist
    pl_id = ""
    pl_title = options.title
    pl_description = "Set list"

    # Check for an existing playlist with the same title
    if playlist_exists_with_title(pl_title):
        print(("Playlist already exists with title '" + pl_title + "'. "
              "Delete it manually and re-run the script to recreate it."))
        return

    pl_id = create_new_playlist(pl_title, pl_description)
    add_chart_entries_to_playlist(pl_id, chart)
    return

def load_config_values():
    """Loads config values from the settings.cfg file in the script dir"""
    config_path = get_script_dir() + 'settings.cfg'
    section_name = 'accounts'

    if not os.path.exists(config_path):
        print ("Error: No config file found. Copy settings-example.cfg to "
               "settings.cfg and customize it.")
        exit()

    config = SafeConfigParser()
    config.read(config_path)

    # Do basic checks on the config file
    if not config.has_section(section_name):
        print ("Error: The config file doesn't have an accounts section. "
               "Check the config file format.")
        exit()

    if not config.has_option(section_name, 'api_key'):
        print("Error: No developer key found in the config file.  Check the config file values.")
        exit()

    config_values = {
        'api_key': config.get(section_name, 'api_key')
    }

    return config_values

def create_youtube_service(config, flags):
    """Create an instance of the YouTube service from the Google Data API library"""
    global youtube

    YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    CLIENT_SECRETS_FILE = get_script_dir() + "client_secrets.json"
    MISSING_SECRETS_MESSAGE = "Error: {0} is missing".format(CLIENT_SECRETS_FILE)
    REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

    # Do OAuth2 authentication
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE,
        message=MISSING_SECRETS_MESSAGE,
        scope=YOUTUBE_READ_WRITE_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    storage = Storage(get_script_dir() + "oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, flags)

    # Create the service to use throughout the script
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=config['api_key'],
        http=credentials.authorize(httplib2.Http())
    )

def get_script_dir():
    """Returns the absolute path to the script directory"""
    return os.path.dirname(os.path.realpath(__file__)) + '/'

def parse_command_line():
    """ Command line argument parser """
    parser = argparse.ArgumentParser(usage="Usage: %(prog)s [options]",
                                     parents=[oauth2client.tools.argparser])

    # yapf: disable
    parser.add_argument("-l", dest="list", type=str,
                        help="file containing set list")
    parser.add_argument("-t", dest="title", type=str,
                        help="Play list title")
    # yapf: enable

    parser.set_defaults(
        list=None
        )

    return parser.parse_args()


def main():
    """Main script function"""
#    print("### Script started at " + time.strftime("%c") + " ###\n")

#    parser = argparse.ArgumentParser(description=__doc__,
#                                     formatter_class=argparse.RawDescriptionHelpFormatter,
#                                     parents=[oauth2client.tools.argparser])
    flags = parse_command_line()

    config = load_config_values()
    create_youtube_service(config, flags)

    create_playlist_from_chart(flags)

    print("### Script finished at " + time.strftime("%c") + " ###\n")

if __name__ == '__main__':
    main()
