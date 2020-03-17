#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
import time
from random import shuffle, randint
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

import clr
clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

TROLL_MSG_TIMER_MINS = 45 # Command added to troll TriHouse

# Splits given list l into chunks of size n. Used for splitting a list of players into teams (chunks).
def chunks(l, n):
    numChunks = len(l) - (len(l) % n)
    for i in range(0, numChunks, n):
        yield l[i:i+n]

# MMRs to map players to when given their rank (eg: c2 => 1340). MMRs chosen are close/equal to the bottom range of div 3 in that rank.
RANKS = {
    "b": [ 147, 217, 176 ],
    "s": [ 338, 398, 459 ],
    "g": [ 517, 580, 648 ],
    "p": [ 728, 808, 887 ],
    "d": [ 968, 1048, 1138 ],
    "c": [ 1235, 1340, 1448 ],
    "gc": [ 1515 ]
}

# Return the MMR and optional rocketID from the params given by the user. Params might be "gc" or "grand champ", thus we parse rocketID here, too.
def parse_mmr_and_rocketid(params):
    if params[0].isnumeric() or (params[0][0] == '-' and params[0][1:].isnumeric()):
        if params[0][0] == '-':
            mmr = -1 * int(params[0][1:])
        else:
            mmr = int(params[0])
        if mmr < 0:
            mmr = 0
        return (mmr, None if len(params) == 1 else params[1])

    (mmr, two_param_mmr) = fix_mmr(params)

    if mmr < 0:
        return (mmr, None)

    rocketID = None
    rocketIDParam = 1 if not two_param_mmr else 2
    if rocketIDParam < len(params):
        rocketID = params[rocketIDParam]

    if mmr == "gc":
        return (RANKS["gc"][0], rocketID)
    rank, level = mmr[:1], mmr[1:]
    if not level.isnumeric() or rank not in RANKS:
        return (-1, rocketID)
    level = int(level)
    if level <= 0 or level - 1 > len(RANKS[rank]) - 1:
        return (-1, rocketID)
    return (RANKS[rank][level - 1], rocketID)


# Attempt to convert unexpected mmr to expected mmr (eg: champ 1 => c1). Returns (expected mmr, bool if second param used in mmr)
def fix_mmr(params):
    mmr = params[0].lower()
    two_param_mmr = False

    if len(mmr) == 1:
        if params[1].isnumeric():
            mmr = mmr + params[1]
            two_param_mmr = True
        else:
            mmr = -1

    elif mmr == "grand":
        if params[1] == "champ" or params[1] == "champion":
            mmr = "gc"
            two_param_mmr = True
        else:
            mmr = -1

    else:
        for rank in [ "bronze", "silver", "gold", "platinum", "plat", "diamond", "dia", "champion", "champ" ]: # Make sure abbreviations come after full rank name (champion before champ)
            if mmr.startswith(rank):
                if len(mmr) > len(rank):
                    mmr = rank[0] + mmr[len(rank):]
                elif params[1].isnumeric():
                    mmr = rank[0] + params[1]
                    two_param_mmr = True
                else:
                    mmr = -1

    return (mmr, two_param_mmr)


# Not technically the "best", just simply orders list of players by MMR then chunks them by team size. Unmatched players are chosen at random.
def best_create_teams(players, teamSize):
    teams = {
        "unmatched": [],
        "teams": []
    }

    # Randomly remove len(players) % teamSize players for unmatched players
    shuffle(players)
    unmatched = len(players) % teamSize
    teams["unmatched"] = [players[i] for i in range(unmatched)]
    players = players[unmatched:]

    # Sort players based on MMR
    players = sorted(players, key = lambda i: i["mmr"])
    teams["teams"] = chunks(players, teamSize)

    return teams


# Create clusters of players based on their MMRs, then random team create teams for players in each cluster. Would probably be better if we incorporated K-means or something.
def cluster_create_teams(players, teamSize):
    teams = {
        "unmatched": [],
        "teams": []
    }

    # Randomly remove len(players) % teamSize players for unmatched players
    shuffle(players)
    unmatched = len(players) % teamSize
    teams["unmatched"] = [players[i] for i in range(unmatched)]
    players = players[unmatched:]

    # Sort players based on MMR
    players = sorted(players, key = lambda i: i["mmr"], reverse=True)

    # Split players into clusters of teamSize * 3 if possible, then randomize
    for cluster in chunks(players, teamSize * 3):
        teams["teams"] += random_create_teams(cluster, teamSize)["teams"]
    teams["teams"] += random_create_teams(players[-1 * (len(players) % (teamSize * 3)):], teamSize)["teams"]

    return teams


# Randomly create teams regardless of MMR
def random_create_teams(players, teamSize):
    teams = {
        "unmatched": [],
        "teams": []
    }

    shuffle(players)
    
    teams["teams"] = chunks(players, teamSize)
    
    if len(players) % teamSize > 0:
        teams["unmatched"] = players[-1 * (len(players) % teamSize):]

    return teams


def player_to_string(player):
    rocketID = "" if "rocketID" not in player or player["rocketID"] is None else "({})".format(player["rocketID"])
    return "@{0}{1}".format(player["twitch"], rocketID)


TEAM_CREATORS = {
    "best": best_create_teams,
    "cluster": cluster_create_teams,
    "random": random_create_teams
}


#   Import your Settings class
from Settings_Module import MySettings
#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "Random Team Creator"
Website = "http://twitch.tv/DaftPenguinRL"
Description = "!register will add users. !createteams will create teams and clear the list. !registered will show how many players were added. !unregister will remove player from list."
Creator = "DaftPenguin"
Version = "2.0.5"

#---------------------------
#   Define Global Variables
#---------------------------
global SettingsFile
SettingsFile = ""
global ScriptSettings
ScriptSettings = MySettings()
global Players
Players = {}

#---------------------------
#   [Required] Initialize Data (Only called on load)
#---------------------------
def Init():
    #   Create Settings Directory
    directory = os.path.join(os.path.dirname(__file__), "Settings")
    if not os.path.exists(directory):
        os.makedirs(directory)

    #   Load settings
    SettingsFile = os.path.join(os.path.dirname(__file__), "Settings\settings.json")
    ScriptSettings = MySettings(SettingsFile)

    return

#---------------------------
#   [Required] Execute Data / Process messages
#---------------------------
def Execute(data):

    # if data.IsChatMessage() and data.GetParam(0).lower() == "!test":
    #    Players["Player4"] = { "twitch": "Player4", "mmr": 730, "rocketID": "afk#1114" }
    #    Players["Player2"] = { "twitch": "Player2", "mmr": 1430, "rocketID": "afk#1112" }
    #    Players["Player1"] = { "twitch": "Player1", "mmr": 1470, "rocketID": "afk#1111" }
    #    Players["Player3"] = { "twitch": "Player3", "mmr": 1030, "rocketID": "afk#1113" }

    # Register command
    if data.IsChatMessage() and data.GetParam(0).lower() == ScriptSettings.RegisterCommand:
        params = [] if data.GetParamCount() < 2 else [data.GetParam(i) for i in range(1, data.GetParamCount())]

        if len(params) == 0:
            Parent.SendStreamMessage("@{0} you must specify your rank, eg: {1} mmr_or_rank rocket_ID (optional)".format(data.User, ScriptSettings.RegisterCommand))
        else:
            (mmr, rocketID) = parse_mmr_and_rocketid(params)
            if mmr < 0:
                Parent.SendStreamMessage("@{0} you must give your rank as mmr, gc, or first letter of rank followed by 1, 2, or 3 (eg: c1 for champ 1)".format(data.User))
            elif ScriptSettings.MaxMMR is not None and mmr > ScriptSettings.MaxMMR:
                Parent.SendStreamMessage("@{0} MMRs that high are not allowed. Try again with a lower MMR.".format(data.User))
            else:
                Players[data.User] = { "twitch": data.User, "mmr": mmr, "rocketID": rocketID }
                Parent.SendStreamMessage("{0} was added to the player list. Type !bothelp if you have questions.".format(player_to_string(Players[data.User])))
                if ScriptSettings.AlertMMR is not None and mmr > ScriptSettings.AlertMMR:
                    Parent.SendStreamMessage("@mods @{0} is either an RL god or trolling".format(data.User))

    # Unregister command
    if data.IsChatMessage() and data.GetParam(0).lower() == ScriptSettings.UnregisterCommand:
        if data.GetParamCount() > 1:
            user = data.GetParam(1)
            if user[0] == "@":
                user = user[1:]
            if Parent.HasPermission(data.User, ScriptSettings.CreateTeamsPermission, ScriptSettings.CreateTeamsInfo):
                del Players[user]
                Parent.SendStreamMessage("@{0} was removed from the player list".format(user))
            else:
                Parent.SendStreamMessage("@{0} you do not have permissions to remove other players".format(data.User))
        else:
            del Players[data.User]
            Parent.SendStreamMessage("@{0} was removed from the player list".format(data.User))
        
    # Registered command
    if data.IsChatMessage() and data.GetParam(0).lower() == ScriptSettings.RegisteredCommand:
        Parent.SendStreamMessage("@{0} there are {1} in the player list".format(data.User, str(len(Players))))
        
    # NumTeams Command
    if data.IsChatMessage() and data.GetParam(0).lower() == ScriptSettings.NumTeamsCommand:
        if data.GetParamCount() < 2:
            Parent.SendStreamMessage("@{0} you must specify a team size".format(data.User))
        else:
            try:
                teamSize = int(data.GetParam(1))
                if teamSize < 2:
                    Parent.SendStreamMessage("@{0} team size must be greater than 1".format(data.User))
                else:
                    unmatched = ""
                    if len(Players) % teamSize > 0:
                        unmatched = " There will be {0} unmatched players".format(len(Players) % teamSize)
                    Parent.SendStreamMessage("@{0} there are {1} teams.{2}".format(data.User, len(Players) / teamSize, unmatched))
            except ValueError:
                Parent.SendStreamMessage("@{0} {1} is an invalid team size".format(data.User, data.GetParam(0)))
    
    # CreateTeams Command
    if data.IsChatMessage() and data.GetParam(0).lower() == ScriptSettings.CreateTeamsCommand:
        if Parent.HasPermission(data.User,ScriptSettings.CreateTeamsPermission,ScriptSettings.CreateTeamsInfo):
            if data.GetParamCount() < 2:
                Parent.SendStreamMessage("@{0} you must specify a team size".format(data.User))
            try:
                teamSize = int(data.GetParam(1))
                if teamSize < 2:
                    Parent.SendStreamMessage("@{0} team size must be greater than 1".format(data.User))
                else:
                    createType = "best" if data.GetParamCount() < 3 else data.GetParam(2)
                    if createType not in TEAM_CREATORS:
                        Parent.SendStreamMessage("@{0} Team creator type must be one of: {1}".format(data.User, ", ".join(TEAM_CREATORS.keys())))
                    else:
                        teams = TEAM_CREATORS[createType]([Players[p] for p in Players], teamSize)

                        Parent.SendStreamMessage("The teams are:")
                        for i, team in enumerate(teams["teams"]):
                            Parent.SendStreamMessage("Team {0}: {1}".format(i + 1,
                                ", ".join(player_to_string(p) for p in team)))
                        if "unmatched" in teams and len(teams["unmatched"]) > 0:
                            unmatched = [player_to_string(p) for p in teams["unmatched"]]
                            Parent.SendStreamMessage("Unmatched players: {0}".format(", ".join(unmatched)))
                    
                        Players.clear()
            except ValueError:
                Parent.SendStreamMessage("@{0} {1} is an invalid team size".format(data.User, data.GetParam(0)))
        else:
            Parent.SendStreamMessage("@{0} you do not have permission to use that command".format(data.User))
    
    return

#---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
    return

#---------------------------
#   [Optional] Parse method (Allows you to create your own custom $parameters) 
#---------------------------
#def Parse(parseString, userid, username, targetid, targetname, message):
#    
#    if "$myparameter" in parseString:
#        return parseString.replace("$myparameter","I am a cat!")
#    
#    return parseString

#---------------------------
#   [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
#---------------------------
def ReloadSettings(jsonData):
    # Execute json reloading here
    global ScriptSettings
    ScriptSettings.Reload(jsonData)
    ScriptSettings.Save(SettingsFile)
    return

#---------------------------
#   [Optional] Unload (Called when a user reloads their scripts or closes the bot / cleanup stuff)
#---------------------------
def Unload():
    Players.clear()
    return

#---------------------------
#   [Optional] ScriptToggled (Notifies you when a user disables your script or enables it)
#---------------------------
def ScriptToggled(state):
    Players.clear()
    return
