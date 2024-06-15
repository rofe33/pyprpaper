#!/usr/bin/env python3

# Author: Raphael Tannous
# Source: https://github.com/rofe33/pyprpaper
# License: GPLv3

# Exit codes:
# 33: something went wrong with hyprpaper.
# 34: hyprpaper is not running.

import argparse
import pathlib
import sys
import random
import socket
import os
import pwd
import time


class Pyprpaper():
    def __init__(self,
                 socket_path: pathlib.Path,
                 directories: list[pathlib.Path],
                 monitors: list[str],
                 additional_file_types: list[str] = [],
                 keep_wallpapers_loaded: bool = False,
                 recursive: bool = False):
        self.directories = [x.absolute() for x in directories]
        self.additional_file_types = additional_file_types
        self.keep_wallpapers_loaded = keep_wallpapers_loaded
        self.monitors = monitors
        self.recursive = recursive
        self.socket_path = str(socket_path.absolute())

        self.file_types = [
            'png',
            'jpg',
            'jpeg'
        ]

        self.file_types += self.additional_file_types

        self.wallpapers: list[pathlib.Path] = self.get_images()
        self.wallpapers_used: list[pathlib.Path] = []

    def _get_directory_images(self,
                              directory: pathlib.Path) -> list[pathlib.Path]:
        """Get all images with all file types, for a directory."""
        images: list[pathlib.Path] = []

        for file_type in self.file_types:
            if self.recursive:
                images += list(directory.rglob(f'*.{file_type}'))
                continue

            images += list(directory.glob(f'*.{file_type}'))

        return images

    def get_images(self) -> list[pathlib.Path]:
        """Get all images for all directories."""
        images: list[pathlib.Path] = []

        for directory in self.directories:
            images += self._get_directory_images(directory)

        return images

    def _unload_used_wallpapers(self):
        """Unloads loaded and used wallpapers."""
        loaded_wallpapers: list = []

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(self.socket_path)

            s.sendall(
                b'listloaded'
            )

            response = s.recv(1024)

        loaded_wallpapers = response.decode().split('\n')

        for wallpaper in self.wallpapers_used:
            if (str(wallpaper.absolute()) not in loaded_wallpapers):
                continue

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(self.socket_path)

                s.sendall(
                    'unload '
                    f'{wallpaper}'.strip().encode()
                )

                data = s.recv(1024)

                if data != b'ok':
                    print('Something went wrong with hyprpaper.')
                    print(data.decode())
                    sys.exit(33)

    def change_wallpapers(self):
        """Change wallpaper randomly for all monitors."""
        for monitor in self.monitors:
            random_wallpaper = random.choice(list(self.wallpapers))

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(self.socket_path)

                s.sendall(
                    'preload '
                    f'{random_wallpaper}'.encode()
                )

                data = s.recv(1024)

                if data != b'ok':
                    print('Something went wrong with hyprpaper.')
                    print(data.decode())
                    sys.exit(33)

            self.wallpapers_used.append(random_wallpaper)

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(self.socket_path)

                s.sendall(
                    'wallpaper '
                    f'{monitor},{random_wallpaper}'.encode()
                )

                data = s.recv(1024)

                if data != b'ok':
                    print('Something went wrong with hyprpaper.')
                    print(data.decode())
                    sys.exit(33)

            # Give hyprpaper  a little bit  of time,
            # to change the wallpaper or it will not
            # be changed.
            if len(self.monitors) >= 2:
                time.sleep(0.5)

        if not self.keep_wallpapers_loaded:
            self._unload_used_wallpapers()


def get_socket_path() -> pathlib.Path:
    """Returns the socket path."""
    socket_path = pathlib.Path('/tmp/hypr/.hyprpaper.sock')

    if not socket_path.is_file():
        user_id = pwd.getpwuid(os.getuid()).pw_uid
        socket_path = list(
            pathlib.Path(f'/run/user/{user_id}/hypr').rglob('.hyprpaper.sock')
        )

        # Getting the working hyprpaper socket
        socket_path = [
            x for x in socket_path
            if x.parent.joinpath('hyprland.lock').is_file()
        ]

    if len(socket_path) == 0:
        print('Is Hyrpaper running?')
        sys.exit(34)

    return socket_path[0]


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='pyprpaper',
        description='A simple wallpaper changer.',
        epilog='All The Glory To Jesus God...',
        add_help=True,
        allow_abbrev=True,
        exit_on_error=True,
    )

    parser.add_argument(
        'directories',
        nargs='+',
        type=pathlib.Path,
        help='Path to directories containing the images.',
        metavar='path/to/directories',
    )

    parser.add_argument(
        '-m',
        '--monitors',
        help='Monitor(s) to change wallpapers on.',
        nargs='+',
        metavar='monitor1 monitor2',
        required=True,
    )

    parser.add_argument(
        '-s',
        '--socket-path',
        type=pathlib.Path,
        help='Override socket path.',
    )

    parser.add_argument(
        '-k',
        '--keep-wallpapers-loaded',
        action='store_true',
        help='Whether to keep wallpapers loaded in RAM or not.',
    )

    parser.add_argument(
        '-r',
        '--recursive',
        action='store_true',
        help='Whether to recursive get the images from the directories.'
    )

    parser.add_argument(
        '-f',
        '--additional-file-types',
        nargs='*',
        default=[],
        metavar='additional file types',
        help='Additional image file types.',
    )

    args = parser.parse_args()

    return vars(args)


def main():
    args = parse_arguments()

    socket_path = args.get('socket_path') or get_socket_path()

    pyprpaper = Pyprpaper(
        socket_path,
        args.get('directories'),
        args.get('monitors'),
        args.get('additional_file_types'),
        args.get('keep_wallpapers_loaded'),
        args.get('recursive'),
    )

    pyprpaper.change_wallpapers()

    sys.exit(0)
