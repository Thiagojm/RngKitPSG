# Default imports
import csv
from datetime import datetime
import re
import os, sys
from contextlib import ExitStack
import time
from typing import Optional

# External imports
import pandas as pd
from bitstring import BitArray
from serial.tools import list_ports
import xlsxwriter
import numpy as np

# BitBabbler (bbpy) integration
try:
    from modules.bbpy.bitbabbler import BitBabbler  # type: ignore
except Exception:
    BitBabbler = None  # Will handle gracefully in detection


def write_to_csv(count, filename):
    now = datetime.now()

    # Format datetime to look like "2023-07-12T16:35:12"
    formatted_now = now.strftime("%Y%m%dT%H:%M:%S")

    # Open the CSV file in append mode
    with open(os.path.join(filename + '.csv'), 'a', newline='') as file:
        writer = csv.writer(file)

        # Write the current datetime and the count of ones
        writer.writerow([formatted_now, count])


## seedd.exe daemon helpers removed (using direct bbpy reading now)


# ----------------- BitBabbler helpers (bbpy) --------------------------
_bb_cached: Optional[object] = None


def _bb_get_device() -> Optional[object]:
    """Return a cached/open BitBabbler device, or None if unavailable.

    Caches the device for reuse to reduce open/init overhead.
    """
    global _bb_cached
    if BitBabbler is None:
        return None
    if _bb_cached is not None:
        return _bb_cached
    try:
        _bb_cached = BitBabbler.open()
        return _bb_cached
    except Exception:
        _bb_cached = None
        return None


def bb_detect() -> bool:
    """Detect whether a BitBabbler device is available using bbpy."""
    dev = _bb_get_device()
    return dev is not None


def bb_read_bytes(out_len: int, folds: int = 0) -> bytes:
    """Read random bytes directly from BitBabbler using bbpy.

    - out_len: number of output bytes desired (after folding)
    - folds: XOR-fold count, 0 = raw
    """
    dev = _bb_get_device()
    if dev is None:
        raise RuntimeError("BitBabbler device not found")
    if folds and folds > 0:
        return dev.read_entropy_folded(out_len, folds)
    return dev.read_entropy(out_len)


def popupmsg(msg_title, msg):
    # Streamlit-compatible version - just print to console
    print(f"{msg_title}: {msg}")


def extract_datetime(filename):
    datetime_str = re.findall(r'\d{8}T\d{6}', filename)[0]
    return datetime.strptime(datetime_str, '%Y%m%dT%H%M%S')

def concat_files(all_filenames, values):
    try:
        sample_value = int(values["an_bit_count"])
        interval_value = int(values["an_time_count"])
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
        popupmsg("Success", f"Concatenated file saved as: {output_path}")
        return True
    except Exception as e:
        popupmsg("Error", f"Select valid files: {str(e)}")
        return False
                    

def open_folder():
    script_path = os.getcwd()
    path = f"{script_path}/1-SavedFiles/"
    path = os.path.realpath(path)
    os.startfile(path)


def check_usb_cap(values):
    if values["bit_ac"]:
        # Use bbpy detection
        if bb_detect():
            return True
        else:
            popupmsg("Error", "Check if the selected BitBabbler is attached.")
            return False
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
        # Mixed mode: require both BitBabbler and TrueRNG present
        bb_ok = bb_detect()
        ports_avaiable = list(list_ports.comports())
        rng_com_port = None
        for temp in ports_avaiable:
            if temp[1].startswith("TrueRNG"):
                if rng_com_port == None:  # always chooses the 1st TrueRNG found
                    rng_com_port = str(temp[0])
        if rng_com_port and bb_ok:
            return True
        else:
            popupmsg("Error", "Check if the the selected devices are attached.")
            return False
    elif values['pseudo_rng_ac']:
        return True

def check_usb_live(values):
    if values['bit_live']:
        if bb_detect():
            return True
        else:
            popupmsg("Error", "Check if the selected BitBabbler is attached.")
            return False       
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
    popupmsg("Success", f"Saved file as: {file_to_save}")


# This function reads a .csv or .bin file do calculations and save to a .xlsx file.
def file_to_excel(file_path):
    try:
        print("Working, please wait... this could take a few seconds.")
        # an_bit_count = int(an_bit_count)
        # an_time_count = int(an_time_count)
        interval = find_interval(file_path)
        block_size = find_bit_count(file_path)
        if file_path == "":
            popupmsg('Attention', 'Select a file first')
            return False
        if file_path.endswith(".bin"):
            df = read_bin_file(file_path, block_size)
        elif file_path.endswith(".csv"):
            df = read_csv_file(file_path)
        df = calculate_z_test(df, block_size)
        write_to_excel(df, file_path, block_size, interval)
        return True
    except Exception as e:
        popupmsg("Error",
                 f'Something went wrong, please check the parameters and try again. Is the target file already open?, {e}')
        return False


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
