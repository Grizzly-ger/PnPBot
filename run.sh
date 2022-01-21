#!/bin/bash
screen -rd bot -X stuff "^C"
sleep 5
screen -rd bot -X stuff "exit\n"
screen -dmS bot
screen -S bot -X stuff "cd ~/PnPBot/\n"
screen -S bot -X stuff ". bot-venv/bin/activate\n"
screen -S bot -X stuff "pip3 install -U nextcord[voice] python-dotenv Beautifulsoup4 urllib3 tabulate\n"
screen -S bot -X stuff "python3 bot.py\n"

screen -rd foundrysocket -X stuff "^C"
sleep 5
screen -rd foundrysocket -X stuff "exit\n"
screen -dmS foundrysocket
screen -S foundrysocket -X stuff "cd ~/PnPBot/\n"
screen -S foundrysocket -X stuff ". bot-venv/bin/activate\n"
screen -S foundrysocket -X stuff "python3 foundrysocket.py -s\n"
