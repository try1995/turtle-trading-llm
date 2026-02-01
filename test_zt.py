import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

url = "https://api.zhituapi.com/hs/list/all?token="+os.environ.get("ZT_TOKEN")

# response = requests.get(url)

# data = response.json()

# with open("symbol","w") as f:
#     f.write(json.dumps(data, indent=4, ensure_ascii=False))