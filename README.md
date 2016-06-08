# MusicMatchX

Description
-----------

Thanks to Youtube users' playlists, this software crosses the playlists results to find the best similar songs to the given songs.

Initialization
--------------

```sh
git clone git@github.com:Hackndo/MusicMatchX.git
cd MusicMatchX/
mkvirtualenv mmx -p $(which python3)
pip install -r requirements.txt
```

Then rename `config.ini.example` file into `config.ini` and edit it with your Google API Key

Usage
-----

```sh
python app.py
```

Todo
----

* Remove duplicate songs
* Remove source songs
* Create a matching score
* 
