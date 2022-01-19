import subprocess
import sys
import time
import os
import socket
from tabulate import tabulate


def show_help():
    print("Usage:")
    print(tabulate([["--help", "-h", "shows this help"],
                   ["--world worldname", "-w worldname", "(re-)start foundry with given world"],
                   ["--socket", "-s", "start script in socket-mode"],
                   ["--list-worlds", "-l", "lists all available worlds"]]))

    pass


def check_foundry_running():
    screens = subprocess.getoutput("/usr/bin/screen -ls")
    if "foundryserver" in screens:
        return True
    else:
        return False


def kill_foundry():
    subprocess.call(["screen", "-r", "foundryserver", "-X", "stuff", "'^C'"])
    return

def get_worlds(userdatapath):
    folder_scan = os.scandir(userdatapath + "Data/worlds/")
    folder_list = []
    for entry in folder_scan:
        if entry.is_dir():
            folder_list.append(entry.name.lower())
    return folder_list


def check_if_world_exits(user_data_path, world):
    folder_list = get_worlds(user_data_path)
    if world.lower() in folder_list:
        return True
    else:
        return False


def restart_foundry(user_data_path, world=None):
    if (world is None) or (check_if_world_exits(user_data_path, world)):
        if check_foundry_running():
            kill_foundry()

        time.sleep(5)
        x = 0
        while check_foundry_running():
            x += 1
            time.sleep(5)
            if x > 5:
                x = 0
                kill_foundry()

        if world is None:
            world_parameter = ""
        else:
            world_parameter = f"--world={world}"
        subprocess.call(["screen", "-dmS", "foundryserver", "node", "/home/christof/foundryvtt/resources/app/main.js",
                         f"--dataPath={user_data_path}", world_parameter])
    else:
        print(f"World {world} doesn't exists! Choose one of the following:")
        print(get_worlds(user_data_path))
        # raise NotFound(f"World {world} doesn't exists! Choose one of the following:\n" + get_worlds(user_data_path))


HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
USERDATAPATH = "/home/christof/foundrydata/"

arguments = sys.argv
if len(arguments) > 3:
    print(f"To many arguments")
    show_help()
    sys.exit()
elif len(arguments) == 1:
    restart_foundry(USERDATAPATH, world=None)
elif len(arguments) >= 2:
    if arguments[1] in ["--socket", "-s"]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket:
            socket.bind((HOST, PORT))
            socket.listen()
            while True:
                conn, addr = socket.accept()
                with conn:
                    conn.settimeout(30)
                    while True:
                        data = conn.recv(1048576).decode()
                        if data == "getworlds":
                            conn.send(get_worlds(USERDATAPATH).encode())
                        elif data.startswith("setworld"):
                            world = data.split(" ")[1]
                            if world.lower() == "none":
                                world = None
                            restart_foundry(USERDATAPATH, world)
                            conn.send("Die Welt wurde geändert".encode())
                        elif data == "exit":
                            break
    elif arguments[1] in ["--list-worlds", "-l"]:
        print(get_worlds())
    elif arguments[1] in ["-w", "--world"]:
        try:
            world=arguments[2]
        except:
            print("Please provide a world")
            print(get_worlds(USERDATAPATH))
        else:
            restart_foundry(USERDATAPATH, world=arguments[2])
    elif arguments[1] in ["--help", "-h"]:
        show_help()
    else:
        print(f"Unknown parameter: {arguments[1]}")
        show_help()
