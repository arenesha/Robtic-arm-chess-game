import urllib.request
import zipfile
import os
import shutil

url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-windows-x86-64-avx2.zip"
zip_path = "stockfish.zip"

print("Downloading Stockfish...")
urllib.request.urlretrieve(url, zip_path)

print("Extracting...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall("stockfish_temp")

# Find the exe
exe_path = None
for root, dirs, files in os.walk("stockfish_temp"):
    for file in files:
        if file.endswith(".exe"):
            exe_path = os.path.join(root, file)
            break

if exe_path:
    shutil.move(exe_path, "stockfish.exe")
    print("Stockfish downloaded and moved to stockfish.exe")

# Cleanup
os.remove(zip_path)
shutil.rmtree("stockfish_temp")
