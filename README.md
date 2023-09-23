# sonar conflict
 A submarine game built with pygame.

 The game is primarily multiplayer (with the exception of a debug-only limited single player mode) and it uses Discord as its server. This simplifies the connection process as it doesn't require a server from my end, and no port forwarding needed for other people that want to play. However, you will need a functioning Discord bot which will have access to a server. Inside the config file, simply paste the bot's token and you're ready to play. It is also important to note that by default the bot will use the first server it has access to for the purposes of the game, if you want to change this, edit the config file and change "server_index" value. Both players must be playing on the same bot token in order for them to play together.
