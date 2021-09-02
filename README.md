# Raid Alert

Simple discord bot to track raid boss spawn and death on L2 Infinity. This is a fun pet project for me, implementation was quick and dirty and I did not implement any way to properly configure the bot, it's not really meant to be used by anyone.

## Installation

Using a virtual environment:

```bash
git clone git git@github.com:RomainFeron/raid_alert.git
cd raid_alert
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Discord configuration parameters need to be defined in `.env` file in the root directory (same as `raid_alert.py`). A template is provided in `.env.example`.

Information about boss drops, adds, and location map are retrieved from https://l2.dropspoil.com with the script `raid_alert/boss_info.py` and stored in `config/boss_info.json`.

To start the bot, just run

```bash
source venv/bin/activate
python3 raid_alert.py
```

## Features

### Boss spawn and death alerts

Raid alert checks the server's website every 30 seconds and automatically sends a message to the `boss-spawn` channel when a boss spawns and to `boss-kill` when a boss dies. These messages provide information on the boss level, good drops, adds, and a link to a map with the boss' location. Good drops are defined in `config/drops.json`.

### Commands

**!alive**: lists all bosses currently alive

## Setup on discord server

Invite the bot with [this link](https://discord.com/api/oauth2/authorize?client_id=882945082515415072&permissions=3072&scope=bot%20applications.commands).

You will need a `boss-spawn` and a `boss-kill` channel in which the bot has permissions to send messages.
