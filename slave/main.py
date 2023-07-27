from flask import Flask, request
import os
import threading
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

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
            for line in f.readlines():
                arr.append(line)
        print("Input received by slave!")
        return {'message':'input saved', 'file':active_filename}

# Implementation of the algo whatever it is
def run_algo():
    global is_active, task_complete, end_time, arr, result
    is_active = True
    for a in arr:
        while on_pause:
            pass
        result += a
        time.sleep(0.1)
    is_active = False
    task_complete = True
    end_time = datetime.now()
    send_result(result)

def send_result(res):
    results_url = os.getenv('MASTER_API_URL')
    status = {
        "input_received":True if len(arr)>0 else False,
        "is_paused":on_pause,
        "is_active":is_active,
        "task_complete":task_complete,
        "start_time":start_time,
        "end_time":end_time,
        "result":result
    }
    send = requests.post(f'{results_url}/submit', status)
    if send.status_code == 200:
        return True
    else:
        return False
    

@app.route("/start")
def start():
    global on_pause,is_active,arr
    if not is_active:
        if on_pause:
            on_pause = False
            is_active = True
            return {"message":"task resumed."}
        if len(arr) > 0:
            threading.Thread(target=run_algo).start()
            global start_time
            start_time = datetime.now()
            return {'message':'task started'}
        else:
            return {'message':'input not received'}
    else:
        return {'message':'already started'}

@app.route("/pause")
def pause():
    global on_pause,arr,is_active
    if on_pause:
        return {'message':'already on pause!'}
    else:
        if len(arr) <= 0:
            return {'message':'input not received'}
        if not is_active:
            return {'message':'task not active to be paused.'}
        if task_complete:
            return {'message':'task completed.'}
        on_pause = True
        is_active = False
        return {'message':'task paused.'}

@app.route("/status")
def get_status():
    return {
        "input_received":True if len(arr)>0 else False,
        "is_paused":on_pause,
        "is_active":is_active,
        "task_complete":task_complete,
        "start_time":start_time,
        "end_time":end_time,
        "result":result
    }

@app.route("/")
def get_root():
    return {
        "message":"Slave is ready!"
    }

if __name__ == "__main__":
    is_active = False
    active_filename = ""
    task_complete = False
    on_pause = False
    start_time = 0
    end_time = 0
    result = 0
    arr = []
    app.run(debug = True)