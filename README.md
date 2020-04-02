# RL Random Team Creator
Streamlabs Chatbot script allows viewers to register themselves to be assigned to a team to play in a tournament. Team creation can be based on best match based on MMR, or randomly chosen.

## Installation

Some preparation is needed to setup Streamlabs Chatbot to import scripts. First, follow the instructions for preparing if you haven't done this already:

https://github.com/StreamlabsSupport/Streamlabs-Chatbot/wiki/Prepare-&-Import-Scripts

*Note that you have to connect Streamlabs to both your bot and streamer accounts before the scripts tab will show.*

Next, download the zip file from releases and import it as a script into Chatbot:

https://github.com/daftpenguin/StreamLabsRocketLeagueRandomTeamCreator/releases/download/v2.0.7/RandomTeamCreator-v2.0.7.zip

## Configuration

Clicking on the Random Team Creator script from the scripts list will bring up the configuration view. Here you can change the name of the commands for users to register/unregister from the queue, print the total number of players registered, calculate the number of teams that can be currently created from the queue, team creation command and permissions for it, and MMR limitations for registration. Hover over the textboxes for tooltips that help explain the usage of each property.

## Usage

Note: these instructions assume the default command names. Command names can be configured by the streamer.

### Quick Reference:

User registration: `!register <mmr_or_rank> <rocketID (optional)>`

Team creation (mods or streamer only, unless configured by streamer): `!createteams <team_size>`

Unregister: `!unregister`

Unregister another user (mods or streamer only): `!unregister <twitch_username>`

Number of players registered: `!registered`

Number of teams that can be created: `!numteams <team_size>`

### More Details:

`!createteams <num> <type>`: replace `<num>` with any number to create teams with that number of players. The `<type>` can either be `best`, `cluster`, or `random`. The type affects how players will be matched into teams, and if not specified, the `best` matching is used. More details on team creation types are explained in the `Team Creation` section. To create teams for doubles with the `best` matching, run: `!createteams 2`. For random matching for standard: `!createteams 3 random`.

`!register <mmr_or_rank> <rocketID>`: registers the user calling the command with the given mmr or rank. The rocketID is optional, but the mmr or rank is required even if teams will be generated randomly. The rocketID's are used in the team print out when teams are created, so users don't have to @ each other with their rocketID's for party creation (no one ever uses this feature). The MMR or rank can be given as either a number, the first letter of the ranks name followed by the number (eg: c1), or typed out like "diamond 1", "plat 2", "gc", "Grand Champ", etc. I've tried to handle all the cases. These ranks are mapped to an MMR near the start of division 3 for that rank, except Grand Champs which are all mapped to 1515 unless an MMR is given.

`!unregister <twitch_username>`: there are two variations of this command. Any user that calls the `!unregister` command will be unregistered from the queue. Mods and the streamer are also able to unregister other users by giving the twitch username of the user to unregister. To unregister DaftPenguin from the queue, a mod or streamer can run: `!unregister daftpenguin`.

`!registered`: bot will respond with the number of players registered in the queue.

`!numteams <num>`: replace `<num>` with the number of players per team and the bot will respond with the number of full teams that can be generated from the players in the queue. For example, if there are 5 players registered, `!numteams 2` will respond saying 2 teams can be generated from the queue.

## Team Creation Types

There are currently 3 team creation types: `best`, `cluster`, and `random`.

Note: For all team creation types, if the number of registered players cannot be evenly divided into teams (eg: 5 registered for doubles), and the `!createteams` command is run, **players will be dropped from the queue at random until the number of players in the queue can be evenly divided into teams**. Therefore, if you have a queue of 3 players with MMRs at 2000, 1500, and 800, and `!createteams 2 best` is run, it's possible for the 800 to be paired with the 2000 or 1500, instead of the 1500 and 2000.

The `random` team creation type will just randomize the queue of players and generate teams from it.

The `best` team creation type will order the entire queue based on their MMRs, and split the ordered queue into teams. The ordering of players with the same MMR is determined by their registration order.

The `cluster` team creation was added to add some randomization to the `best` team creation. The `cluster` team creation essentially uses the `best` team creation to generate clusters of 3 times the team size, then random teams are created from each cluster. In other words, if 12 players register and `!createteams 2 cluster` is run, the players are ordered by MMR and 3 teams are created randomly from the top 6 players, and another 3 teams from the bottom 6 players. Note that if the number of registered players is less than 3 times the team size, team creation will be the same as `random` team creation.