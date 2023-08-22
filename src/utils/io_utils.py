import os
from shutil import copyfile, rmtree
from pytube import YouTube


def create_path(path):
    try:
        if os.path.exists(path):
            delete_path(path)
        os.mkdir(path)
    except OSError:
        assert False, "Creation of the directory failed."


def delete_path(path):  # Dangerous! Watch out!
    try:
        rmtree(path, ignore_errors=False)
    except OSError:
        print("Deletion of the directory %s failed" % path)
        print(OSError)


def download_file(url):
    name = YouTube(url).streams.first().download()
    new_name = name.replace(' ', '_')
    os.rename(name, new_name)
    return new_name
