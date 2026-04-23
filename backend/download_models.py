import requests
import os

models_dir = "models"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

files = {
    "deploy.prototxt": "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt",
    "mobilenet.caffemodel": "https://github.com/chuanqi305/MobileNet-SSD/raw/master/mobilenet_iter_73000.caffemodel"
}

for filename, url in files.items():
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        print(f"Downloading {filename}...")
        r = requests.get(url, allow_redirects=True)
        with open(path, 'wb') as f:
            f.write(r.content)
        print(f"Finished {filename}")
    else:
        print(f"{filename} already exists.")
