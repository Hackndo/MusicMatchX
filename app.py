#!/usr/bin/env python

"""
MusicMatchX
===========

Description
-----------
Thanks to Youtube users' playlists, this software crosses the
playlists results to find the best similar songs to the given songs.

Author
------
Hackndo

Requirements
------------
All requirements are indicated in requirements.txt file

Configuration
-------------
A Google project with YoutubeApi v3 is necessary. API key must be provided
in config.ini file as follow:

config.ini:
    [Keys]
    GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE

Version
-------
0.1

"""

import sys
import apiclient
import apiclient.discovery
import apiclient.errors
import configparser

if sys.version_info < (3, 0):
    import Tkinter as tk
else:
    import tkinter as tk


"""
Graphical User Interface
"""
class MusicMatchX(tk.Tk):
    def __init__(self, parent):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        width = 300
        height = 400
        self.geometry("%sx%s" % (width, height))
        self.title('MusicMatchX')
        self.grid()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Song list
        self.music_list = tk.Listbox(self)
        self.music_list.grid(column=0, row=0, columnspan=2)

        # Artist field
        self.music_artist = tk.Entry(self, text="Artist")
        self.music_artist.grid(column=0, row=1)
        self.music_artist.insert(0, "Artist")
        self.music_artist.bind("<FocusIn>", self.clear_artist)

        # Title field
        self.music_title = tk.Entry(self)
        self.music_title.grid(column=1, row=1)
        self.music_title.insert(0, "Title")
        self.music_title.bind("<FocusIn>", self.clear_title)

        # Add button
        self.add_button = tk.Button(self,
                                    text="Add",
                                    command=self.add_music)
        self.add_button.grid(column=0, row=2)

        # Clear button
        self.clear_button = tk.Button(self,
                                      text="Clear",
                                      command=self.clear_list)
        self.clear_button.grid(column=1, row=2)

        # Youtube playlist
        self.playlist_entry = tk.Entry(self)
        self.playlist_entry.grid(column=0, row=3)
        self.playlist_entry.insert(0, "Youtube Playlist")
        self.playlist_entry.bind("<FocusIn>", self.clear_youtube_playlist)

        # Scan Depth
        label = tk.Label(self, text="Scan depth")
        label.grid(column=0, row=4)

        self.depth_scale = tk.Scale(self,
                                   from_=1,
                                   to=10,
                                   orient=tk.HORIZONTAL,
                                   )
        self.depth_scale.grid(column=1, row=4)

        # Magic
        self.add_button = tk.Button(self,
                                    text="Let the magic happen!",
                                    command=self.get_matches)
        self.add_button.grid(column=0, row=5, columnspan=2)

        # Results
        self.result_list = tk.Listbox(self)
        self.result_list.grid(column=0, row=7, columnspan=2)
        self.result_list.config(width=100)
        # Little hack here
        # Make sure all widgets have been rendered
        self.update()

        # Then we update its geometry to old geometry
        # We do not want it to resize depending on widget size
        self.geometry(self.geometry())

        self.lift()

    def clear_artist(self, event):
        self.music_artist.delete(0, tk.END)

    def clear_title(self, event):
        self.music_title.delete(0, tk.END)

    def clear_youtube_playlist(self, event):
        self.playlist_entry.delete(0, tk.END)

    def add_music(self):
        self.music_list.insert(tk.END, "%s %s" % (self.music_artist.get(),
                                                  self.music_title.get()))
        self.music_artist.delete(0, tk.END)
        self.music_title.delete(0, tk.END)

    def clear_list(self):
        self.music_list.delete(0, tk.END)

    def get_matches(self):
        youtubeAPI = YoutubeAPI()
        musicMatch = MusicMatch([], 0, youtubeAPI)

        # Clear old results list
        self.result_list.delete(0, tk.END)

        # Check if songs were added
        songs = self.music_list.get(0, tk.END)

        # If not, take youtube playlist
        if len(songs) <= 0:
            songs = musicMatch.get_songs_from_pl(self.playlist_entry.get())

        musicMatch.songs = songs

        # Get depth level
        musicMatch.depth_level = self.depth_scale.get()

        # Get matches
        sorted_results = musicMatch.get_matches()

        # Update the results list
        self.result_list.delete(0, tk.END)
        for r in sorted_results:
            self.result_list.insert(
                tk.END,
                "%s - %s" % (r[1]["rank"], r[1]["title"])
            )

"""
Youtube API calls
"""
class YoutubeAPI():
    def __init__(self):
        configParser = configparser.RawConfigParser()
        configFilePath = "./config.ini"
        configParser.read(configFilePath)
        google_api_key = configParser["Keys"]["GOOGLE_API_KEY"]
        self.youtube = apiclient.discovery.build(
            "youtube",
            "v3",
            developerKey=google_api_key)

    def youtube_get_playlist(self, playlistId):
        pl_items_list_req = self.youtube.playlistItems().list(
            playlistId=playlistId,
            part="snippet")

        results = []

        while pl_items_list_req:
            pl_items_list_resp = pl_items_list_req.execute()

            # Print information about each video.
            for playlist_item in pl_items_list_resp["items"]:
                results.append({
                    "title": playlist_item["snippet"]["title"],
                    "videoId": playlist_item["snippet"]["resourceId"][
                        "videoId"],
                })

            pl_items_list_req = self.youtube.playlistItems().list_next(
                pl_items_list_req, pl_items_list_resp)
        return results

    def youtube_search(self, options):
        # Call the search.list method to retrieve results matching
        # the specified query term.
        search_response = self.youtube.search().list(
            q=options["q"],
            part="id,snippet",
            type="playlist",
            maxResults=options["max_results"]
        ).execute()

        playlists = []

        for search_result in search_response.get("items", []):
            playlists.append({
                "title": search_result["snippet"]["title"],
                "playlistId": search_result["id"]["playlistId"]
            })

        return playlists


"""
Matching logic
"""
class MusicMatch():
    def __init__(self, songs, depth_level, youtubeAPI):
        self.songs = songs
        self.depth_level = depth_level
        self.youtubeAPI = youtubeAPI

    """
    Extract songs from a playlist

    :return array of songs' titles
    """
    def get_songs_from_pl(self, playlistId):
        return [s["title"] for
                s in self.youtubeAPI.youtube_get_playlist(playlistId)]

    """
    Find matching songs by crossing playlist results

    :return dictionary with titles and occurrence
    """
    def get_matches(self, min_occurrence=0):
        results = {}
        for k, song in enumerate(self.songs):
            print("[*] (%s/%s) Song %s" % (k+1, len(self.songs), song))
            args = {
                'q': song,
                'max_results': self.depth_level
            }
            try:
                playlists = self.youtubeAPI.youtube_search(args)

                for playlist in playlists:
                    videos = self.youtubeAPI.youtube_get_playlist(
                        playlist["playlistId"]
                    )
                    for v in videos:
                        if v["videoId"] in results:
                            results[v["videoId"]]["rank"] += 1
                        else:
                            results[v["videoId"]] = {
                                "title": v["title"],
                                "rank": 1
                            }
            except apiclient.errors.HttpError as e:
                print("An HTTP error %d occurred:\n%s" % (
                    e.resp.status, e.content))

        sorted_results = sorted(results.items(),
                                key=lambda x: x[1]["rank"],
                                reverse=True)

        return sorted_results


if __name__ == "__main__":
    app = MusicMatchX(None)
    app.mainloop()
