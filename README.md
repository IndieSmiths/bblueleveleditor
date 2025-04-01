# Bionic Blue's level editor

Level editor for the [Bionic Blue](https://github.com/IndieSmiths/bionicblue) game.

> [!WARNING]
> Rather than a tool for general use, this is a highly crude tool meant for in-house usage. As such, it lacks many features and is susceptible to crashing/malfunctioning and sudden requirement changes.

This tool was created by me, Kennedy Richard S. Guerra([website](https://kennedyrichard.com) | [GitHub](https://github.com/KennedyRichard)), 34, as part of the Indie Smiths project ([website](https://indiesmiths.com) | [GitHub](https://github.com/IndieSmiths)).

Please, help support my work on this and many other child projects of the Indie Smiths project (the Bionic Blue game, the Nodezator node editor and more) by becoming our [patron](https://patreon.com/KennedyRichard), sponsoring us on [GitHub Sponsors](https://github.com/sponsors/KennedyRichard) or via [other available methods](https://indiesmiths.com/donate).


## Why release a crude tool?

Since this is a crude tool meant for in-house usage, why release it then?

First, for the sake of transparency. That is, since I'm an open-source maintainer, by publishing to GitHub people can inspect my work on this project via the commits.

Second, naturally, for tracking and backing up my work using the git/GitHub combo.

Third, for instructional purposes, as I intend to write text pieces/tutorials referencing/using tools like this one. That is, despite its crude state, it is rather effective and allows for quick iteration and distraction-free progress in making the game. Or rather, it is precisely because I can focus only in the bare features needed to create a level that I can invest most of my time in working on the game rather than maintaining the level editor.

Finally, like all tools/games from the Indie Smiths project, I also wanted to release it to the public domain, so people can learn with it and use it as they see fit, usually changing it according to their needs.


## Usage

To launch it, download the repo, then from inside the repository folder, with a Python instance where pygame-ce is installed, run this command:

```
python3 -m bblueleveleditor
```

Depending on your system, you might need to replace `python3` with `python`.

The `wasd` keys move the canvas.

The `g` key toggles the grid:

![toggling the grid](https://i.imgur.com/Hjn7xjQ.gif)

The `q` and `e` switch between available assets:

![switching between available assets](https://i.imgur.com/rTbXaEk.gif)

If the asset is of seamless type, that is, it can expand over a larger area, like the city block asset for instance, you can click and drag on the screen to "paint" it over that area.

![painting seamless assets over larger areas](https://i.imgur.com/spWG3Df.gif)

If the asset selected is not of seamless type (the robot is the only one for now), you can place one by simply clicking:

![adding simple objects by clicking the canvas](https://i.imgur.com/XEOmWGe.gif)

Press the `x` key to toggle the "erase" mode. In erase mode you can delete assets by clicking on them.

![enabling erase mode and deleting assets](https://i.imgur.com/2UtadX1.gif)

The `r` key toggles the outlines of assets (which are easier to see when the grid is toggled off).

![toggling asset outlines](https://i.imgur.com/FFWOk5d.gif)

Press `v` to save the level file (.lvl), press `p` to export the level as a .png image and press the `Escape` key to quit the program.

The saved `.lvl` or exported `.png` file appears in the `bblueleveleditor/levels` folder created automatically within the repo (the folder is ignored by git/not tracked).

To create and edit a new level file, empty the folder (for instance, by moving an existing .lvl file to another location in your disk) and launch the editor again. When you save, a new .lvl file will be created there again. This is convoluted and may be improved in the future, but it is not actually a problem at all: as I said before this tool is supposed to be very basic and simple, so I can quickly create the levels I need and move on to the next development task of the game.

Likewise, the exported .png file will be overwritten everytime you export the level as .png. However, you don't need to move the .png out of the folder for a new one to be saved there. Renaming it will suffice.


## More info

For now, I actually indicate whether an asset is seamless or not and other properties of the asset in its name.

For instance, consider the name of the grunt robot asset: `grunt_bot.actors.False.midbottom.png`.

The `.actors` part indicates it is to be placed in the `actors` layer. The `False` part indicates it is not a seamless asset. Finally the `midbottom` part indicates which corner of the asset the position should be assigned to. That is, in this case it means the position data stored for the robot should be assigned to the robot's midbottom corner. You can use any of the 9 points defined in a `pygame.Rect`, that is, `topleft`, `topright`, `center`, etc.
