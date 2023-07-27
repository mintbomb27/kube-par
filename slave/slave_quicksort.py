from flask import Flask, request
import os
import threading
import time
from datetime import datetime
import requests
import numpy
import json
from typing import Final
import copy
import multiprocessing

app = Flask(__name__)

@app.route("/input", methods=['POST'])
def save_input():
    if request.method == "POST":
        f = request.files['file']
        f.save(f.filename)
        global active_filename
        active_filename = f.filename
        global string_list
        string_list = []
        with open(active_filename, 'rb') as f:
            for line in f.readlines():
                string_list.append(line)
        
        print("Input received by slave!")
        return {'message':'input saved', 'file':active_filename}

# Functions for Quicksort Algo
def serial_quicksort(a_list):

    assert a_list is not None

    if (len(a_list) > 0):

        partitioning_element = a_list.pop((len(a_list) - 1) // 2)

        no_larger_than_list = []

        larger_than_list = []

        partition(a_list=a_list,
                     no_larger_than_list=no_larger_than_list,
                     larger_than_list=larger_than_list,
                                partitioner=partitioning_element)

        serial_quicksort(no_larger_than_list)
        serial_quicksort(larger_than_list)
 
        a_list.extend(no_larger_than_list)
        a_list.append(partitioning_element)
        a_list.extend(larger_than_list)

def partition(a_list, no_larger_than_list, larger_than_list, partitioner):
    assert a_list is not None
    assert no_larger_than_list is not None
    assert larger_than_list is not None
    assert partitioner is not None

    no_larger_than_list.clear()
    larger_than_list.clear()

    while (len(a_list) > 0):
        #global on_pause
        #while on_pause:
        #    pass
        element = a_list.pop()
        if (element > partitioner):
            larger_than_list.append(element)
        else:
            no_larger_than_list.append(element)

def parallel_quicksort(a_list, sending_socket, current_processes_count,
                                                    MAX_PROCESSES_COUNT):

    assert a_list is not None
    assert sending_socket is not None
    assert current_processes_count is not None
    assert MAX_PROCESSES_COUNT is not None

    if (len(a_list) > 0):
       
        if (current_processes_count >= MAX_PROCESSES_COUNT):
            serial_quicksort(a_list=a_list)

            sending_socket.send(a_list)
            sending_socket.close()
        else:
            partitioning_element = a_list.pop((len(a_list) - 1) // 2)
            no_larger_than_list = []
            larger_than_list = []
            partition(a_list=a_list, no_larger_than_list=no_larger_than_list,
                           larger_than_list=larger_than_list, partitioner=partitioning_element)
            receive_sock_no_larger_than_proc, send_sock_no_larger_than_proc = \
                                                    multiprocessing.Pipe(duplex=False)
            receive_sock_larger_than_proc, send_sock_larger_than_proc = \
                                                    multiprocessing.Pipe(duplex=False)
            new_process_count = 2 * current_processes_count + 1
            no_larger_than_proc = multiprocessing.Process(target=parallel_quicksort,
                                                            args=(no_larger_than_list,
                                                                  send_sock_no_larger_than_proc,
                                                                  new_process_count,
                                                                  MAX_PROCESSES_COUNT))
            larger_than_proc = multiprocessing.Process(target=parallel_quicksort,
                                                            args=(larger_than_list,
                                                                  send_sock_larger_than_proc,
                                                                  new_process_count,
                                                                  MAX_PROCESSES_COUNT))
            no_larger_than_proc.start()
            larger_than_proc.start()
            no_larger_than_list = receive_sock_no_larger_than_proc.recv()
            larger_than_list = receive_sock_larger_than_proc.recv()
            a_list.extend(no_larger_than_list)
            a_list.append(partitioning_element)
            a_list.extend(larger_than_list)
            sending_socket.send(a_list)
            sending_socket.close()
            no_larger_than_proc.join()
            larger_than_proc.join()
            no_larger_than_proc.close()
            larger_than_proc.close()
    else:
        sending_socket.send(a_list)
        sending_socket.close()

# Implementation of the algo whatever it is
LENGTH_OF_STRING: Final = 10
# Length of randomly generated string list
LENGTH_OF_STRING_LIST: Final = 500000

def run_algo():
    global is_active, task_complete, end_time, string_list, result
    is_active = True
    print("\nInitializing list copies to be sorted (this may take some time)...")
    
    string_list_copy = copy.deepcopy(string_list)

    print("\nGenerating reference sorted list using Python's \"sorted\" "
          "built-in function for\n    validating correctness of serial "
          "version and parallel version of quicksort... ", end="")

    reference_sorted_list = sorted(string_list)

    print("Done!")

    print(f"\nTime to sort list of {LENGTH_OF_STRING_LIST} strings "
          f"where each string is {LENGTH_OF_STRING} characters long...\n")

    start_sort_time = time.time()
    serial_quicksort(a_list=string_list)
    end_sort_time = time.time()

    print(f"...using serial version of quicksort: "
          f"{end_sort_time - start_sort_time:.6f} seconds.\n")

    start_sort_time = time.time()

    receive_sorted_list_socket, send_sorted_list_socket = \
        multiprocessing.Pipe(duplex=False)

    quicksort_parent_process = multiprocessing.Process(target=parallel_quicksort,
                                                       args=(string_list_copy,
                                                             send_sorted_list_socket,
                                                             1,
                                                             multiprocessing.cpu_count()))

    quicksort_parent_process.start()

    string_list_copy = receive_sorted_list_socket.recv()

    quicksort_parent_process.join()
    end_sort_time = time.time()

    print(f"...using parallel version of quicksort\n"
          f"    (parallelized over a target of "
          f"{multiprocessing.cpu_count()} processes): "
          f"{end_sort_time - start_sort_time:.6f} seconds.\n")

    print("Validating result of serial version of quicksort...")

    numpy.testing.assert_array_equal(numpy.array(string_list),
                                     numpy.array(reference_sorted_list),
                                     err_msg="serial version of quicksort " \
                                             "did not produce a correctly sorted list.")

    print("    Congratulations, expected and actual lists are equal!\n")

    print("Validating result of parallel version of quicksort...")

    numpy.testing.assert_array_equal(numpy.array(string_list_copy),
                                     numpy.array(reference_sorted_list),
                                     err_msg="parallel version of quicksort "
                                             "did not produce a correctly sorted list.")

    print("    Congratulations, expected and actual lists are equal!\n")
    is_active = False
    task_complete = True
    end_time = datetime.now()
    send_result(string_list_copy)

def send_result(res):
    results_url = os.getenv('MASTER_API_URL')
    status = {
        "slave_id":os.getenv('SLAVE_ID'),
        "result":str(res)
    }
    headers = {'Content-Type': 'application/json'}
    json_data = json.dumps(status)
    print(status)
    send = requests.post(f'{results_url}/submit', data=json_data, headers=headers)
    if send.status_code == 200:
        print("Result sent success")
        return True
    else:
        print("result sent failed")
        return False

@app.route("/start")
def start():
    global on_pause,is_active,string_list
    if not is_active:
        if on_pause:
            on_pause = False
            is_active = True
            return {"message":"task resumed."}
        if len(string_list) > 0:
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
    global on_pause,string_list,is_active
    if on_pause:
        return {'message':'already on pause!'}
    else:
        if len(string_list) <= 0:
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
        "input_received":True if len(string_list)>0 else False,
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
        "message":"Slave is running!"
    }

if __name__ == "__main__":
    is_active = False
    active_filename = ""
    task_complete = False
    on_pause = False
    start_time = 0
    end_time = 0
    result = 0
    string_list = []
    app.run(debug = True)