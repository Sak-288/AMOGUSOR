import os
import shutil


def remove_everything():
    if os.path.exists("usage/"):
        for entry in os.scandir('usage/'):
            try:
                os.remove(entry)
            except IsADirectoryError:
                for subentry in os.scandir(entry):
                    os.remove(subentry)


remove_everything()