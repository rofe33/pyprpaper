#!/usr/bin/env python3

# Author: Raphael Tannous
# Source: https://github.com/rofe33/pyprpaper
# License: GPLv3

# Exit codes:
# 33: hyprland doesn't have any instances running.
# 34: hyprpaper is not running.
# 127: hyprctl command is not found.

import argparse
import pathlib
import subprocess
import sys
import json
import random


class Pyprpaper():
    def __init__(self,
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

    def change_wallpapers(self):
        """Change wallpaper randomly for all monitors."""
        for monitor in self.monitors:
            random_wallpaper = random.choice(list(self.wallpapers))

            subprocess.run(
                [
                    'hyprctl',
                    'hyprpaper',
                    'preload',
                    f'{random_wallpaper}'.strip(),
                ],
                stdout=subprocess.DEVNULL,
            )

            self.wallpapers_used.append(random_wallpaper)

            subprocess.run(
                [
                    'hyprctl',
                    'hyprpaper',
                    'wallpaper',
                    f'{monitor},{random_wallpaper}',
                ],
                stdout=subprocess.DEVNULL,
            )

        if not self.keep_wallpapers_loaded:
            for wallpaper in self.wallpapers_used:
                subprocess.run(
                    [
                        'hyprctl',
                        'hyprpaper',
                        'unload',
                        f'{wallpaper}'.strip(),
                    ],
                    stdout=subprocess.DEVNULL,
                )


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


def check_hyprs_status():
    """Checks if hyprland and hyprpaper are running."""
    try:
        instances = subprocess.run(
            [
                'hyprctl',
                '-j',
                'instances',
            ],
            capture_output=True,
        )

        if len(json.loads(instances.stdout)) == 0:
            print('You don\'t have any hyprland instance running.')
            sys.exit(33)
    except FileNotFoundError:
        print('Do you have hyprland installed?')
        sys.exit(127)  # Command not found

    hyprpaper = subprocess.run(
        [
            'hyprctl',
            'hyprpaper',
        ],
        capture_output=True,
    )

    if (hyprpaper.returncode == 3 or
            hyprpaper.stdout.decode().strip().endswith('(3)')):
        print('Is hyprpaper running?')
        sys.exit(34)


def get_monitors() -> list[str]:
    monitors_info = subprocess.run(
        [
            'hyprctl',
            '-j',
            'monitors',
        ],
        capture_output=True,
    )

    return [
        monitor.get('name') for monitor in json.loads(monitors_info.stdout)
    ]


def main():
    check_hyprs_status()

    args = parse_arguments()

    pyprpaper = Pyprpaper(
        args.get('directories'),
        get_monitors(),
        args.get('additional_file_types'),
        args.get('keep_images_loaded'),
        args.get('recursive'),
    )

    pyprpaper.change_wallpapers()

    sys.exit(0)
