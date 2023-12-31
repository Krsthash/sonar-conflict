# Sonar Conflict
 A submarine game built with pygame.

 The game is primarily multiplayer (with the exception of a debug-only limited single-player mode) and it uses **Discord** as its server. This simplifies the connection process as it doesn't require a server from my end, and no port forwarding is needed for other people who want to play. However, you will need a functioning Discord bot which will have access to a server. Inside the config file, simply paste the bot's token and you're ready to play. It is also important to note that by default the bot will use the first server it has access to for the purposes of the game, if you want to change this, edit the config file and change the "server_index" value. Both players must be playing on **the same bot token** in order for them to play together.

# How to play

*Make sure you have entered the correct bot token in the config file!*
First off, one player needs to host the game, they do this by pressing the "Host a game" button. Next, they need to choose a mission file by pressing either "Browse" (to load a specific mission) or "Random" to let the game randomly pick from available missions in the "Missions" folder. This is the only essential step, the player can now press "Host". After a short period, they will be given a game code which they need to supply to the other player. The other player needs to simply enter the game code after pressing "Join a game" and then press "Join". In the "Host a game" screen, the host could choose a few additional options such as the team they start as and other important gameplay options by clicking "Options".

# Sonar screen

![image](https://github.com/Krsthash/sonar-conflict/assets/87620691/4d327e39-6787-41b4-868d-a6c387820aea)

When the game starts, you will be presented with the "Sonar screen". This screen will act as your eyes on the battlefield, there you will be able to search, identify and track targets. On the left, there is a big green circle, this is your active sonar. You can enable it by pressing "t" on your keyboard. After turning it on, you will notice a white line propagates through the circle, this is the sonar ping. In the case that the sonar ping reflects back to the player's vessel, a green dot will appear on the circle indicating a target. You can select the target by clicking on its circle. That will bring you information about the contact on the right. The important thing to know is that by enabling the active sonar, other vessels could easily detect you with their passive sonar, so only use active sonar in emergencies or when you have the advantage over your opponent!

On the right, there is a big rectangular section. This is the passive sonar. The passive sonar is essentially a big listening device, it listens for any sounds made in the ocean. If it hears something, the signal will be displayed on the waterfall display. A waterfall display (the name comes from the signal's appearance being like water in a waterfall) is basically a plot where the x-axis represents the bearing (from 0 to 359 degrees) and the y-axis represents time. The display is also split into two parts, the left part is for contacts that are above your vessel and the right is for below it. They are identical, the display is only split to allow easier identification of targets.
Once a signal appears on the passive sonar display you will be able to select it for identification. You can do this by moving your cursor over the signal and clicking on it, you might need to click on it a few times to properly select it (the cursor should go green once selected). Once selected, you will see basic information about the contact on the bottom left. To learn more about the contact, you can select it for identification, this process will take a few seconds and after it is identified you will gain access to much more information about it, including which side it is from (USA or RU), that will be very useful to know during the game.

# Weapons screen

![image](https://github.com/Krsthash/sonar-conflict/assets/87620691/3f7f2951-7263-4fbb-929a-59235af10db9)


To access the weapons screen press "e" on your keyboard. On the top left, there is information about your vessel, its speed, current gear, depth, etc... This information is also present in the sonar screen.
When you just start off, your vessel should be near a friendly port, this means that you will be allowed to supply and resupply yourself with weapons. You can automatically fill up all weapon slots by pressing "r". You can also manually resupply by clicking on the slots in the centre of the screen. You can switch between different weapon types by clicking on the weapon again, which will switch it to the next available one. By clicking on a weapon, you will automatically select it. On the right, you can see all the important information about the currently selected weapon.
The weapon loadout consists of two segments, the "VLS" and torpedo tubes. VLS stands for Vertical Launch System and it is mostly used to launch missiles, meanwhile, torpedo tubes are mostly used for torpedoes and sonar decoys (although in the case of the US, you can also launch anti-ship missiles from them). Another important detail is that both VLS and torpedo tubes have a red outlined part, and a grey outlined part. The red slots represent the actual launch-capable slots. From those slots you can fire the selected weapons, meanwhile, the grey slots are only for storage. Once you use up a weapon from the red slot, you can replace it with another from the storage slot by pressing on the storage slot first, and then on the red slot (this should, however, not work near a port because the weapon will be resupplied after you click on it).

# Firing weapons

To use weapons go to the weapons tab and select one in the launch slot. In the section on the top, you will find 3 boxes. The first one is for the bearing to the target, the second one is the depth and finally the third one is the distance. You can manually enter the position information into these boxes by pressing on them and then using your keyboard to enter the information. You can also use arrow keys to quickly add to the value or subtract from it. Once the information is entered, you can choose the appropriate mode for the weapon type. Torpedoes usually have active/passive mode which refers to the sonar being used on the torpedo. Anti-ship missiles and land attack missiles use the "normal" mode (launch won't be authorized if the mode isn't set up properly). Once everything is ready, you can press the red "fire" button and you should see your launched weapon on the left. You should also get feedback if the weapon hits its target.

# Aiming weapons quickly

Entering the position information of the targets is practically impossible to do manually quickly enough so that by the time you launch the weapon, the target is still there. To solve this issue, there are 3 buttons under the position information boxes for firing weapons. Those buttons are "A", "P" and "R". The "R" button simply resets all values currently entered. The "A" button will automatically fill out the necessary information from the currently selected active sonar contact. Similarly, the "P" button will automatically fill out information from the currently selected passive sonar contact. To properly do this, you need to first press the button, and then go back to the sonar screen. In the sonar screen, if you don't have a contact already selected, you can select it now, otherwise, you can just go back to the weapons screen and the information should automatically be entered! Now you can just click fire.

# The map

![image](https://github.com/Krsthash/sonar-conflict/assets/87620691/2b50b0a8-e708-4ede-ae74-4512dcbdaae5)


You can enter the map screen by pressing "m" on your keyboard. On the map screen, you will notice that your vessel is marked with a big green dot with a red line coming out of it. The red line indicates your current heading. The other big green dots are friendly ports, here you can resupply on weapons. The yellow dots with a percentage next to them are friendly bases, and the orange dots are enemy bases. Smaller green dots with red lines are your friendly ships. These ships patrol the ocean and can transmit information to you in the case of detected threats (like the enemy player), they can also listen to active sonar pings.
You can drag your mouse to move the map around, and you can use your scroll wheel to zoom in and out. On the bottom left, you can see a scale indicator, this can be useful when you are aligning shots on enemy bases with land attack missiles.

# The scoreboard

By pressing the tab key, you can access the scoreboard. The scoreboard contains basic information about the players, including their score in the game. Depending on the game options, when the player reaches a certain score, they instantly win the game.

# Ships

Both sides have ships roaming around the ocean. You can see yours on the map screen, however, you can't see the enemy's ships. You can, of course, detect them with the sonar!
Every time that you successfully destroy an enemy ship you will gain points (you can check that on the scoreboard). However, you have to be careful. Enemy ships are very capable of detecting you, especially if your engines are loud and you are moving in the third gear. They can also hear your active sonar ping and transmit it to the enemy player. Once the ships detect you, they will turn on their active sonar to track you, and they will shoot torpedoes at you. 
