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
    if os.path.exists("webapp/static/webapp/final_image.jpg"):
        os.remove("webapp/static/webapp/final_image.jpg")
    if os.path.exists("webapp/static/webapp/final_version_with_audio.mp4"):
        os.remove("webapp/static/webapp/final_version_with_audio.mp4")


remove_everything()