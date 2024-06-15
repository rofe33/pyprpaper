# Pyprpaper

Pyprpaper  is  a   `hyprpaper`  client,  its  main
purpose   is   to   change   wallpapers   randomly
(for  given   set  of   monitors)  from   a  given
directory(ies).

## Features

- Randomly change wallpapers for given monitors.
- Recursive image look-up in all directories.

## Installation

You can install [pyprpaper](https://pypi.org/project/pyprpaper/) using `pip`:

```sh
pip install pyprpaper
```

It is also available in the AUR ([pyprpaper](https://aur.archlinux.org/packages/pyprpaper)) for the arch linux
btw users:

```sh
# With yay
yay -S pyprpaper
```

The `PKGBUILD` and `.SRCINFO` files are at
[rofe33/pyprpaper-aur](https://github.com/rofe33/pyprpaper-aur).

## Usage

```
usage: pyprpaper [-h] -m monitor1 monitor2 [monitor1 monitor2 ...] [-s SOCKET_PATH] [-k] [-r]
                 [-f [additional file types ...]]
                 path/to/directories [path/to/directories ...]

A simple wallpaper changer.

positional arguments:
  path/to/directories   Path to directories containing the images.

options:
  -h, --help            show this help message and exit
  -m monitor1 monitor2 [monitor1 monitor2 ...], --monitors monitor1 monitor2 [monitor1 monitor2 ...]
                        Monitor(s) to change wallpapers on.
  -s SOCKET_PATH, --socket-path SOCKET_PATH
                        Override socket path.
  -k, --keep-wallpapers-loaded
                        Whether to keep wallpapers loaded in RAM or not.
  -r, --recursive       Whether to recursive get the images from the directories.
  -f [additional file types ...], --additional-file-types [additional file types ...]
                        Additional image file types.

All The Glory To Jesus God...
```

### Example

Change  wallpaper  for  all monitors in hyprland/hyprpaper set-up:

```sh
pyprpaper -m $(hyprctl -j monitors | jq -r '.[].name' | tr '\n' ' ') -- /path/to/wallpaper/directories
```
