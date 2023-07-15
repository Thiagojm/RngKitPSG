# Default imports
import csv
from datetime import datetime
import re
import os, sys
import socket
import subprocess
from contextlib import ExitStack
import time

# External imports
import pandas as pd
import PySimpleGUI as sg
from bitstring import BitArray
from serial.tools import list_ports
import xlsxwriter
import psutil
import numpy as np


def write_to_csv(count, filename):
    now = datetime.now()

    # Format datetime to look like "2023-07-12T16:35:12"
    formatted_now = now.strftime("%Y%m%dT%H:%M:%S")

    # Open the CSV file in append mode
    with open(os.path.join(filename + '.csv'), 'a', newline='') as file:
        writer = csv.writer(file)

        # Write the current datetime and the count of ones
        writer.writerow([formatted_now, count])


def kill_seedd():
    # Get a list of all running processes
    all_processes = psutil.process_iter()


    # Iterate over the running processes and find the process named 'seedd.exe'
    for process in all_processes:
        if process.name() == 'seedd.exe':
            # Terminate the process
            process.terminate()
            print(f"Process {process.name()} ({process.pid}) has been terminated.")
            break  # Exit the loop once the process is found and terminated

def start_seedd(command):
    process = subprocess.Popen(command, shell=True)

def read_from_deamon(addr, port, bytes_requested, max_msg_size):
    if bytes_requested < 1:
        print("Not reading 0 bytes")
        sys.exit(1)
    elif bytes_requested > max_msg_size:
        print("Maximum request is", max_msg_size)
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Send the requested number of bytes as a network-order short.
    msg = bytes([bytes_requested >> 8, bytes_requested & 0xFF])

    sock.sendto(msg, (addr, port))
    
    data, _ = sock.recvfrom(max_msg_size)
    return data 


def popupmsg(msg_title, msg):
    sg.popup_non_blocking(msg_title, msg, keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                          icon="src/images/BitB.ico")


def extract_datetime(filename):
    datetime_str = re.findall(r'\d{8}T\d{6}', filename)[0]
    return datetime.strptime(datetime_str, '%Y%m%dT%H%M%S')

def concat_files(all_filenames, values):
    try:
        sample_value = int(values["ac_bit_count"])
        interval_value = int(values["ac_time_count"])
        file_name = time.strftime(
        f"%Y%m%dT%H%M%S_concat_s{sample_value}_i{interval_value}.csv")
        
        # get the directory of the first file in the list
        directory = os.path.dirname(all_filenames[0]) if all_filenames else ''
        output_path = os.path.join(directory, file_name)

        all_filenames.sort(key=extract_datetime)  # Sorting filenames by datetime

        with ExitStack() as stack:
            files = [stack.enter_context(open(fname)) for fname in all_filenames]
            with open(output_path, "a") as f:
                for file in files:
                    for line in file:
                        f.write(line)
        popupmsg("Sucess", f"Concatenated file saved as: {output_path}")
    except Exception:
        popupmsg("Error", "Select valid files")
                    

def open_folder():
    script_path = os.getcwd()
    path = f"{script_path}/1-SavedFiles/"
    path = os.path.realpath(path)
    os.startfile(path)


def check_usb_cap(values):
    if values["bit_ac"]:
        return True
    elif values['true3_ac']:
        ports_avaiable = list(list_ports.comports())
        rng_com_port = None
        for temp in ports_avaiable:
            if temp[1].startswith("TrueRNG"):
                if rng_com_port == None:  # always chooses the 1st TrueRNG found
                    rng_com_port = str(temp[0])
        if rng_com_port:
            return True
        else:
            popupmsg("Error", "Check if the the selected device is attached.")
            return False
    elif values["true3_bit_ac"]:
        ports_avaiable = list(list_ports.comports())
        rng_com_port = None
        for temp in ports_avaiable:
            if temp[1].startswith("TrueRNG"):
                if rng_com_port == None:  # always chooses the 1st TrueRNG found
                    rng_com_port = str(temp[0])
        if rng_com_port:
            return True
        else:
            popupmsg("Error", "Check if the the selected devices are attached.")
            return False
    elif values['pseudo_rng_ac']:
        return True

def check_usb_live(values):
    if values['bit_live']:
        return True        
    elif values['true3_live']:
        ports_avaiable = list(list_ports.comports())
        rng_com_port = None
        for temp in ports_avaiable:
            if temp[1].startswith("TrueRNG"):
                if rng_com_port == None:  # always chooses the 1st TrueRNG found
                    rng_com_port = str(temp[0])
        if rng_com_port:
            return True
        else:
            popupmsg("Error", "Check if the the selected device is attached.")
            return False
    elif values['pseudo_rng_live']:
        return True

# ----------------- Analyse Data --------------------------

# This function finds the interval in seconds from the filename.
def find_interval(file_path):
    match_i = re.search(r"_i(\d+).", file_path)
    interval = int(match_i.group(1))
    return interval

# This function finds the bit count from the filename.
def find_bit_count(file_path):
    match = re.search(r"_s(\d+)_i", file_path)
    bit_count = int(match.group(1))
    return bit_count

# This function reads a .csv file and returns a DataFrame with timestamp and number of ones.
def read_csv_file(file_path):
    df = pd.read_csv(file_path, header=None, names=['time', 'ones'])
    df['time'] = pd.to_datetime(df['time']).apply(lambda x: x.strftime('%H:%M:%S'))
    return df

# This function reads a .bin file and returns a DataFrame with block number and number of ones.
def read_bin_file(file_path, block_size):
    data_list = []
    with open(file_path, 'rb') as binary_file:
        block = 1
        while True:
            data = binary_file.read(block_size // 8)
            if len(data) == 0:
                break
            bit_arr = BitArray(data)
            ones = bit_arr.count(1)
            data_list.append([block, ones])
            block += 1
    return pd.DataFrame(data_list, columns=['samples', 'ones'])

# This function calculates the cumulative mean and Z-test value and adds them as new columns to the DataFrame.
def calculate_z_test(dataframe, block_size):
    expected_mean = 0.5 * block_size
    expected_std_dev = np.sqrt(block_size * 0.5 * 0.5)
    dataframe['cumulative_mean'] = dataframe['ones'].expanding().mean()
    dataframe['z_test'] = (dataframe['cumulative_mean'] - expected_mean) / (expected_std_dev / np.sqrt(dataframe.index + 1))
    return dataframe

# This function writes the DataFrame to an Excel file, and adds a line chart to visualize the Z-test value.
def write_to_excel(dataframe, file_path, block_size, interval):
    file_to_save = os.path.splitext(file_path)[0]+'.xlsx'
    writer = pd.ExcelWriter(file_to_save, engine='xlsxwriter')
    dataframe.to_excel(writer, sheet_name='Zscore', index=False)

    workbook = writer.book
    worksheet = writer.sheets['Zscore']

    chart = workbook.add_chart({'type': 'line'})

    chart.add_series({
        'categories': ['Zscore', 1, 0, len(dataframe), 0],
        'values':     ['Zscore', 1, 3, len(dataframe), 3],
    })

    chart.set_title({'name': os.path.basename(file_path)})
    chart.set_x_axis({'name': f'Number of Samples - one sample ervery {interval} second(s)', 'date_axis': True})
    chart.set_y_axis({'name': f'Z-Score - Sample Size =  {block_size} bits)'})
    
    chart.set_legend({'none': True})

    worksheet.insert_chart('F2', chart)

    writer.close()


# This function reads a .csv or .bin file do calculations and save to a .xlsx file.
def file_to_excel(file_path):
    try:
        sg.PopupQuickMessage("Working, please wait... this could take a few seconds.", background_color="Grey",
                             font="Calibri, 18", auto_close_duration=1)
        # an_bit_count = int(an_bit_count)
        # an_time_count = int(an_time_count)
        interval = find_interval(file_path)
        block_size = find_bit_count(file_path)
        if file_path == "":
            popupmsg('Atention', 'Select a file first')
            return
        if file_path.endswith(".bin"):
            df = read_bin_file(file_path, block_size)
        elif file_path.endswith(".csv"):
            df = read_csv_file(file_path)
        df = calculate_z_test(df, block_size)
        write_to_excel(df, file_path, block_size, interval)
    except Exception as e:
        popupmsg("Error",
                 f'Something went wrong, please check the parameters and try again. Is the target file already open?, {e}')


def test_bit_time_rate(bit_count, time_count):
    try:
        if int(bit_count) > 0 and (int(bit_count) % 8) == 0:
            pass
        else:
            popupmsg("Error", "Check if the number is divisible by 8, an integer, greater then 0 and try again.")
            return False
    except Exception:
        popupmsg("Error", "Check if the number is divisible by 8, an integer, greater then 0 and try again.")
        return False
    try:
        if int(time_count) >= 1:
            pass
        else:
            popupmsg("Error", "Choose a sample interval that is an integer number and is equal or greater then 1.")
            return False
    except Exception:
        popupmsg("Error", "Choose a sample interval that is an integer number and is equal or greater then 1.")
        return False
    return True
