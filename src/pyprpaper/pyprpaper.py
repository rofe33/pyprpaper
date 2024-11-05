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
import signal


class Pyprpaper():
    def __init__(self,
                 socket_path: pathlib.Path,
                 directories: list[pathlib.Path],
                 monitors: list[str],
                 additional_file_types: list[str] = [],
                 keep_wallpapers_loaded: bool = False,
                 keep_wallpapers_consistent: bool = False,
                 recursive: bool = False):
        self.directories = [x.absolute() for x in directories]
        self.additional_file_types = additional_file_types
        self.keep_wallpapers_loaded = keep_wallpapers_loaded
        self.keep_wallpapers_consistent = keep_wallpapers_consistent
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

        # active_wallpapers  are   the  wallpapers
        # that  are  currently  displayed  on  the
        # monitor(s).
        self.active_wallpapers: list[pathlib.Path] = []

        # used_wallpapers  are the  wallpapers are
        # now being used.
        self.used_wallpapers: list[pathlib.Path] = []

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

    def _get_active_wallpapers(self) -> list[pathlib.Path]:
        """Returns a list of active wallpapers."""

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(self.socket_path)

            s.sendall(
                b'listactive'
            )

            response = s.recv(1024)

        if response == b'no wallpapers active':
            return []

        # listactive example:
        # DP-1 = /path/wallpaper_01.jpg
        # eDP-1 = /path/wallpaper_02.jpg

        return [
            pathlib.Path(x.split()[2]) for x in response.decode().split('\n')
        ]

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

        for wallpaper in self.used_wallpapers:
            # Do not unload not loaded wallpapers by pyprpaper.
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
        self.active_wallpapers = self._get_active_wallpapers()

        random_wallpaper: pathlib.Path = pathlib.Path(
            random.choice(self.wallpapers)
        )

        for monitor in self.monitors:
            if not self.keep_wallpapers_consistent:
                # Do not use active and used wallpapers.
                # Wallpaper will change for the second time.
                while True:
                    if (random_wallpaper not in self.active_wallpapers
                            and random_wallpaper not in self.used_wallpapers):
                        break

                    random_wallpaper = pathlib.Path(
                        random.choice(self.wallpapers)
                    )

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

            self.used_wallpapers.append(random_wallpaper)

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

        if not self.keep_wallpapers_loaded:
            # Give hyprpaper  a little bit  of time,
            # to change the wallpaper or it will not
            # be changed.
            time.sleep(0.5)

            self._unload_used_wallpapers()

        # Cleaning self.used_wallpapers
        self.used_wallpapers = []


def get_socket_path() -> pathlib.Path:
    """Returns the socket path."""
    socket_path = pathlib.Path('/tmp/hypr/.hyprpaper.sock')

    # None-Hyprland/Hyprpaper setup
    if socket_path.is_file():
        return socket_path

    # Hyprland/Hyprpaper setup
    user_id = pwd.getpwuid(os.getuid()).pw_uid

    available_sockets = pathlib.Path(
        f'/run/user/{user_id}/hypr'
    ).rglob('.hyprpaper.sock')

    # Getting the working hyprpaper socket
    for socket_ in available_sockets:
        if socket_.parent.joinpath('hyprland.lock').is_file():
            return socket_

    print('Is Hyrpaper running?')
    sys.exit(34)


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
        '-v',
        '--version',
        action='version',
        version='%(prog)s 0.3.2',
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
        '-K',
        '--keep-wallpapers-consistent',
        action='store_true',
        help='Whether to randomly set the same wallpaper for all the monitors.',
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

    parser.add_argument(
        '-t',
        '--timer',
        type=int,
        help='Timer to change the wallpaper each n seconds'
    )

    args = parser.parse_args()

    return vars(args)


def timer(delay, func):
    """Timer function to run func each delay seconds."""
    next_time = time.time() + delay

    while True:
        time.sleep(max(0, next_time - time.time()))

        func()

        next_time += (time.time() - next_time) // delay * delay + delay


def signal_handling(signum, frame):
    sys.exit()


def main():
    signal.signal(signal.SIGINT, signal_handling)
    args = parse_arguments()

    if args.get('timer') is not None and args.get('timer') < 10:
        print('Delay should be greater than 10.')

        sys.exit(0)

    socket_path = args.get('socket_path') or get_socket_path()

    pyprpaper = Pyprpaper(
        socket_path,
        args.get('directories'),
        args.get('monitors'),
        args.get('additional_file_types'),
        args.get('keep_wallpapers_loaded'),
        args.get('keep_wallpapers_consistent'),
        args.get('recursive'),
    )

    pyprpaper.change_wallpapers()

    if args.get('timer') is None:
        sys.exit(0)

    timer(args.get('timer'), pyprpaper.change_wallpapers)

    sys.exit(0)
