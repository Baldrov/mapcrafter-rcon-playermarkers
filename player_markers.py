from async_mcrcon.async_mcrcon import MinecraftClient
import asyncio
import re
import json5
import sys
import os
import base64
import requests
import time
from shutil import copyfile
from PIL import Image, ImageOps
from io import BytesIO


async def player_markers(conf):
    conf = load_config(conf)
    for server in conf["servers"]:
        players = await get_online_players(conf["servers"][server]["rcon_ip"], conf["servers"][server]["rcon_port"], conf["servers"][server]["rcon_pw"])
        for player in players:
            load_skin(player, conf)

        maps = {}
        for map in conf["servers"][server]["worlds"].strip("[]").split(", "):
            maps[map] = conf["worlds"][map]
        update_markers(os.path.join(conf["output_dir"], "playermarkers.js"), players, maps)


def load_config(file):
    dimensions = {
        "overworld": "overworld",
        "end": "the_end",
        "nether": "the_nether"
    }
    conf = {
        "worlds": {},
        "servers": {}
    }
    with open(file) as f:
        data = f.readlines()
    section = ""
    for line in data:
        if "output_dir" in line:
            conf["output_dir"] = line.split("=")[1].strip()
        match = re.match(r"\[(.*)\]", line)
        if match:
            section = match[1]
        else:
            if ":" in section and "playermarker" in section:
                if "=" in line:
                    s_name = section.split(":")[1]
                    name, value = line.split("=")
                    if s_name not in conf["servers"]:
                        conf["servers"][s_name] = {}
                    conf["servers"][s_name][name.strip()] = value.strip()
            if ":" in section and "world" in section:
                if "=" in line:
                    s_name = section.split(":")[1]
                    name, value = line.split("=")
                    if s_name not in conf["worlds"]:
                        conf["worlds"][s_name] = "overworld"
                    if "dimension" in name.strip():
                        if value.strip() in dimensions:
                            conf["worlds"][s_name] = dimensions[value.strip()]

    return conf


async def get_online_players(ip, port, pw):
    async with MinecraftClient(ip, port, pw) as mc:
        output = await mc.send('list uuids')
        players = re.findall(r'([a-zA-Z0-9_]*) \(([a-z0-9-]*)\)', output)
        players_dict = {}
        for player in players:
            dimension = await mc.send('data get entity ' + str(player[1]) + " Dimension")
            dimension = re.findall(r'\"minecraft:([a-z_]*)\"', dimension)[0]
            position = await mc.send('data get entity ' + str(player[1]) + " Pos")
            position = re.findall(r'\[([d0-9., -]*)\]', position)[0].split(", ")
            position = [int(x.split(".")[0]) for x in position]
            # MC: x, z, y
            # Map: x, y, z
            position[1], position[2] = position[2], position[1]
            players_dict[player[1]] = (player[0], dimension, position)

    return players_dict


def update_markers(file, players, maps):
    with open(file) as f:
        data = re.findall(r'MAPCRAFTER_PLAYERMARKERS = \[(.*)\];', f.read(), re.DOTALL)[0]
        data = json5.loads('{ "groups" : [' + data + '] }')
    for group in data["groups"]:
        if "uuid" in group["id"]:
            uuid = group["id"].split("_")[1]
            if uuid in players:
                group["showDefault"] = True
                player = players.pop(uuid)
                group["name"] = player[0]
                for entry in group["markers"]:
                    group["markers"][entry] = []
                for map in maps:
                    if maps[map] == player[1]:
                        group["markers"][map].append({'pos': player[2], "title": player[0], "text": player[0]})

            else:
                group["showDefault"] = False
    for player in players:
        group = {
            "id": "uuid_" + player,
            "name": players[player][0],
            "icon": player + ".png",
            "showDefault": True,
            "markers": {},
        }
        for map in maps:
            group["markers"][map] = []
            # dimension
            if maps[map] == players[player][1]:
                group["markers"][map].append({'pos': players[player][2], "title": players[player][0], "text": players[player][0]})
        data["groups"].append(group)
    with open(file, "w") as f:
        f.write("MAPCRAFTER_PLAYERMARKERS = ")
        f.write(json5.dumps(data["groups"], quote_keys=True))
        f.write(";")


def is_alex(uuid):
    uuid = uuid.replace("-", "")
    sub = []
    for i in range(0, 4):
        sub.append(int("0x" + uuid[i*8:i*8+8], 16))
    return ((sub[0] ^ sub[1]) ^ (sub[2] ^ sub[3])) % 2


def load_skin(uuid, conf):
    file = os.path.join(conf["output_dir"], "static", "markers", uuid + ".png")
    if not os.path.isfile(file) or time.time() - os.path.getmtime(file) >= 86400:
        r = requests.get('https://sessionserver.mojang.com/session/minecraft/profile/' + uuid)
        if r.status_code == requests.codes.ok:
            data = r.json()
            data = data["properties"][0]["value"]
            data = json5.loads(base64.b64decode(data))
            if "SKIN" in data["textures"]:
                ri = requests.get(data["textures"]["SKIN"]["url"])
                if ri.status_code == requests.codes.ok:
                    img = Image.open(BytesIO(ri.content))
                    width, height = img.size
                    skin = Image.new('RGBA', (16, 32), (0, 0, 0, 0))
                    big = 0 if "metadata" in data["textures"]["SKIN"] else 1
                    # inverted to paste the arm with spacing
                    small = 1 if "metadata" in data["textures"]["SKIN"] else 0
                    # New Texture Format
                    if height == 64:
                        head = img.crop((8, 8, 16, 16))
                        head_o = img.crop((40, 8, 48, 16))
                        legr = img.crop((4, 20, 8, 32))
                        legr_o = img.crop((4, 36, 8, 48))
                        body = img.crop((20, 20, 28, 32))
                        body_o = img.crop((20, 36, 28, 48))
                        armr = img.crop((44, 20, 47+big, 32))
                        armr_o = img.crop((44, 36, 47+big, 48))
                        legl = img.crop((20, 52, 24, 64))
                        legl_o = img.crop((4, 52, 8, 64))
                        arml = img.crop((36, 52, 39+big, 64))
                        arml_o = img.crop((52, 52, 55+big, 64))

                        skin.paste(head, (4, 0, 12, 8))
                        skin.paste(head_o, (4, 0, 12, 8), head_o)

                        skin.paste(legr, (4, 20, 8, 32))
                        skin.paste(legr_o, (4, 20, 8, 32), legr_o)

                        skin.paste(body, (4, 8, 12, 20))
                        skin.paste(body_o, (4, 8, 12, 20), body_o)

                        skin.paste(armr, (0+small, 8, 4, 20))
                        skin.paste(armr_o, (0+small, 8, 4, 20), armr_o)

                        skin.paste(legl, (8, 20, 12, 32))
                        skin.paste(legl_o, (8, 20, 12, 32), legl_o)

                        skin.paste(arml, (12, 8, 15+big, 20))
                        skin.paste(arml_o, (12, 8, 15+big, 20), arml_o)

                    elif height == 32:
                        head = img.crop((8, 8, 16, 16))
                        head_o = img.crop((40, 8, 48, 16))
                        body = img.crop((20, 20, 28, 32))
                        legr = img.crop((4, 20, 8, 32))
                        armr = img.crop((44, 20, 48, 32))
                        legl = ImageOps.mirror(legr)
                        arml = ImageOps.mirror(armr)

                        skin.paste(head, (4, 0, 12, 8))
                        skin.paste(head_o, (4, 0, 12, 8), head_o)

                        skin.paste(legr, (4, 20, 8, 32))
                        skin.paste(body, (4, 8, 12, 20))
                        skin.paste(armr, (0, 8, 4, 20))
                        skin.paste(legl, (8, 20, 12, 32))
                        skin.paste(arml, (12, 8, 16, 20))

                    skin.save(file)
                    return None
        if os.path.isfile(file):
            return None
        if is_alex(uuid):
            copyfile(os.path.join(sys.path[0], "alex.png"), file)
        else:
            copyfile(os.path.join(sys.path[0], "steve.png"), file)
        return None
    return None


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(player_markers(sys.argv[1]))
    loop.close()


if __name__ == '__main__':
    main()
