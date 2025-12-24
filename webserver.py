import os
from flask import Flask
import threading
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

port = int(os.environ.get("PORT", 10000))

def run_server():
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_server).start()

# Run the main bot file
subprocess.run(["python3", "main.py"])
