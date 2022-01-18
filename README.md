# PnPBot
* clone repo
* create venv "bot-venv" in repo-folder 
* install nextcord[voice]: [nextcord installing instructions](https://nextcord.readthedocs.io/en/latest/intro.html#installing)
* install python-dotenv
* install Beautifulsoup4
* install urllib3
* install tabulate


* rename duplicate .env_example to .env and fill the fields
* Create GM role
* Create Category "Foundry Status" with view permission but joining voice-channels forbidden and 2 voice-channels in this category
* create Category "Internal" for GMs with at least a textchannel fot the bot to send messages
* create Category "General" with a dummy "default" channel. The default-channel should be hidden for everyone
* set all settings