import os
import sys
import zipfile


root_directory = sys.path[0]
print(
    """
    This content download script will download approximately 650mb of binary data from dropbox that cannot be stored on github.
    While it is completely optional to do this, you'll receive a lot of errors if you don't, and many commands will not function.

    Make sure you have curl on path! If you're on windows 10 version 1803 or later, you should be okay. If you're using linux, you already know what you're doing.
    If you're using macOS, I can't be bothered helping you. Figure it out yourself.

    With all that in mind, press any key to continue, or ctrl+c to quit.
    """
    )

input("")

path_generated = os.path.join(root_directory, "lobstero", "data", "generated")
path_downloaded = os.path.join(root_directory, "lobstero", "data", "downloaded")
directory_path = os.path.join(root_directory, "lobstero", "data", "static")
concatenated_path = os.path.join(root_directory, "lobstero", "data", "static", "lobstero_content.zip")

print("Attempting preliminary directory configuration...")

os.makedirs(directory_path, exist_ok=True)
os.makedirs(path_generated, exist_ok=True)
os.makedirs(path_downloaded, exist_ok=True)

print("Configuration success! Downloading data archive...")

os.system(f"curl https://www.dropbox.com/s/nadg2y7lysx5flf/lobstero_content.zip?dl=1 -L -o {concatenated_path}")

print("Data archive successfully downloaded. Attempting to decompress...")

zipped_file = zipfile.ZipFile(concatenated_path, "r")
zipped_file.extractall(directory_path)

print("Decompression successful! All data is where it should be. Press any key to exit.")
input("")