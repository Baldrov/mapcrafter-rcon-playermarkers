# Mapcrafter RCON Playermarkers

Python script to add playermarkers on a [Mapcrafter](https://github.com/mapcrafter/mapcrafter) map.  
Goal was something like [Mapcrafter-playermarkers](https://github.com/mapcrafter/mapcrafter-playermarkers) that works with a vanilla server.  

Users will have their marker added when they are online.  
Skins will be cached for one day.  
Markers will stay if someone logs out but will be deactivated by default (they get removed after 2 Weeks of inactivity).


## Setup

* Have a mapcrafter map  
* Create a playermarkers.js in your output directory  
* Add the empty variable which will get filled:
```
var MAPCRAFTER_PLAYERMARKERS = [];
```
* Add the new javascript into your index.html template.
```
		<script type="text/javascript" src="playermarkers.js"></script>
```
```
                        if(typeof MAPCRAFTER_PLAYERMARKERS !== "undefined")
                                for(var i = 0; i < MAPCRAFTER_PLAYERMARKERS.length; i++)
                                        markers.push(MAPCRAFTER_PLAYERMARKERS[i]);
```
* Add RCON config to your render.conf
```
[playermarker:world] 
worlds = [world, world_nether]
rcon_ip = 127.0.0.1
rcon_port = 25575 
rcon_pw = password
```
"worlds" is optional and should contain a list of all [world:<xyz>] entries you have on that server and for which you want to add markers.   
If you leave it empty markers are added to all worlds.  
You can have multiple playermarker sections for different servers.
* python dependencies
```
asyncio
json5
requests
pillow
```

## Usage

> python player_markers.py <path/to/render.conf>

