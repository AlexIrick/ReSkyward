import os
import shutil
from os.path import dirname, join


def delete_folder(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)


WINDOW_ICON = join(dirname(__file__), 'img', 'logo-min.svg')
