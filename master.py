import requests
import os
from flask import Flask, request
import threading
import time 
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

@app.route("/input", methods=['POST'])
def save_input():
    if request.method == "POST":
        f = request.files['file']
        f.save(f.filename)
        global active_filename
        active_filename = f.filename
        global arr
        arr = []
        with open(active_filename, 'rb') as f:
            lines = f.readlines()
            num_lines = len(lines)
            slaves = eval(request.form['slaves'])
            num_slaves = len(slaves)
            lines_per_file = num_lines // num_slaves
            for i in range(num_slaves):
                start_line = i * lines_per_file
                end_line = (i + 1) * lines_per_file if i < 2 else num_lines
                with open(f'new_file_{i+1}.txt', 'wb') as f:
                    f.writelines(lines[start_line:end_line])
                with open(f'new_file_{i+1}.txt', 'rb') as f:
                    endpoint = os.getenv(f"{slaves[i]}_API_URL") + '/input'
                    response = requests.post(endpoint, files={'file': f})
                    if response.status_code != 200:
                        print(f"Failed to upload new_file_{i+1}.txt to API route")
                        return message('failed to input')
                    else:
                        print(f"Uploaded new_file_{i+1}.txt to API route")
        return {'message':'input saved', 'file':active_filename}

def message(msg, data = None):
    return {"message": msg, "data": data}

@app.route("/start", methods=["POST"])
def start():
    slave_endpoint = os.getenv(f"{request.data['slave']}_API_URL")
    start_slave = requests.get(f"{slave_endpoint}/start")
    if start_slave.status_code == 200:
        return message("started", start_slave.json)
    else:
        return message("couldn't start")

@app.route("/start/all", methods=["POST"])
def start_all():
    slaves = request.json['slaves']
    for slave in slaves:
        endpoint = os.getenv(f"{slave}_API_URL")
        start_slave = requests.get(f"{endpoint}/start")
    if start_slave.status_code == 200:
        return message("started")
    else:
        return message("couldn't start")

@app.route("/submit", methods=["POST"])
def submit():
    slave_id = request.json['slave_id']
    global results
    results[slave_id] = f"{request.json['slave_id']}_out.txt"
    with open(f"{request.json['slave_id']}_out.txt",'w+') as f:
        f.write(request.json['result'])
    return message("submitted")

@app.route("/status", methods=["GET"])
def get_status():
    return results

@app.route("/")
def get_root():
    return {
        "message":"Master is ready!"
    }

if __name__ == "__main__":
    global results
    results = {}
    app.run(port=5001, debug=True)