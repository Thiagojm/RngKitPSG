# Default imports
import re
import os
import subprocess
from contextlib import ExitStack
import time

# External imports
import pandas as pd
import PySimpleGUI as sg
from bitstring import BitArray
from serial.tools import list_ports
import xlsxwriter

def popupmsg(msg_title, msg):
    sg.popup_non_blocking(msg_title, msg, keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                          icon="src/images/BitB.ico")


def concat_files(all_filenames):
    try:
        file_name = time.strftime(f"%Y%m%d-%H%M%S")
        with ExitStack() as stack:
            files = [stack.enter_context(open(fname)) for fname in all_filenames]
            with open(f"1-SavedFiles/{file_name}_concat.csv", "a") as f:
                for file in files:
                    for line in file:
                        f.write(line)
        popupmsg("Sucess", f"Concatenated file saved as: 1-SavedFiles/{file_name}_concat.csv")
    except Exception:
        popupmsg("Error", "Select valid files")
                    

def open_folder():
    script_path = os.getcwd()
    path = f"{script_path}/1-SavedFiles/"
    path = os.path.realpath(path)
    os.startfile(path)


def check_usb_cap(values):
    if values["bit_ac"]:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(f"src/bin/seedd.exe --limit-max-xfer --no-qa -f0 -b 1",
            stdout=subprocess.PIPE, startupinfo=startupinfo)
        chunk = proc.stdout.read()
        if chunk:
            return True
        else:
            popupmsg("Error", "Check if the the selected device is attached.")
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
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(f"src/bin/seedd.exe --limit-max-xfer --no-qa -f0 -b 1", stdout=subprocess.PIPE,
                                startupinfo=startupinfo)
        chunk = proc.stdout.read()
        ports_avaiable = list(list_ports.comports())
        rng_com_port = None
        for temp in ports_avaiable:
            if temp[1].startswith("TrueRNG"):
                if rng_com_port == None:  # always chooses the 1st TrueRNG found
                    rng_com_port = str(temp[0])
        if rng_com_port and chunk:
            return True
        else:
            popupmsg("Error", "Check if the the selected devices are attached.")
            return False


def check_usb_live(values):
    if values['bit_live']:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(f"src/bin/seedd.exe --limit-max-xfer --no-qa -f0 -b 1",
            stdout=subprocess.PIPE, startupinfo=startupinfo)
        chunk = proc.stdout.read()
        if chunk:
            return True
        else:
            popupmsg("Error", "Check if the the selected device is attached.")
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


# ----------------- Analyse Data --------------------------
def file_to_excel(data_file, an_bit_count, an_time_count):
    try:
        sg.PopupQuickMessage("Working, please wait... this could take a few seconds.", background_color="Grey",
                             font="Calibri, 18", auto_close_duration=1)
        an_bit_count = int(an_bit_count)
        an_time_count = int(an_time_count)
        if data_file == "":
            popupmsg('Atention', 'Select a file first')
            pass
        elif data_file[-3:] == "csv":
            ztest = ztest_pandas(data_file, an_bit_count)
            data_file2 = os.path.basename(data_file)
            data_file2 = data_file2.replace(".csv", "")
            file_to_save = data_file.replace(".csv", ".xlsx")
            number_rows = len(ztest.index)
            writer = pd.ExcelWriter(file_to_save, engine='xlsxwriter')
            ztest.to_excel(writer, sheet_name='Z-Test', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Z-Test']
            chart = create_chart(workbook, data_file2, an_bit_count, an_time_count)
            chart.add_series(
                {'values': ['Z-Test', 1, 5, number_rows, 5], 'categories': ['Z-Test', 1, 1, number_rows, 1]})
            worksheet.insert_chart('G2', chart)
            writer.save()
            popupmsg('File Saved', 'Saved as ' + file_to_save)
            return
        elif data_file[-3:] == "bin":
            sg.PopupQuickMessage("Working, please wait... this could take a few seconds.", background_color="Grey",
                                 font="Calibri, 18", auto_close_duration=2)
            with open(data_file, "rb") as file:  # open binary file
                bin_hex = BitArray(file)  # bin to hex
            bin_ascii = bin_hex.bin
            split_bin_ascii = re.findall("." * an_bit_count, bin_ascii)  # Waaaaay faster then wrap and map zip
            num_ones_array = list(map(lambda x: x.count("1"), split_bin_ascii))
            binSheet = binary_data(num_ones_array, an_bit_count)
            data_file2 = os.path.basename(data_file)
            data_file2 = data_file2.replace(".bin", "")
            file_to_save = data_file.replace(".bin", ".xlsx")
            number_rows = len(binSheet.Sample)
            writer = pd.ExcelWriter(file_to_save, engine='xlsxwriter')
            binSheet.to_excel(writer, sheet_name='Z-Test', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Z-Test']
            chart = create_chart(workbook, data_file2, an_bit_count, an_time_count)
            chart.add_series(
                {'values': ['Z-Test', 1, 4, number_rows, 4], 'categories': ['Z-Test', 1, 0, number_rows, 0]})
            worksheet.insert_chart('G2', chart)
            writer.save()
            popupmsg('File Saved', 'Saved as ' + file_to_save)
            return
        else:
            popupmsg("Warning", 'Wrong File Type, Select a .bin or .csv file')
            pass
    except Exception:
        popupmsg("Error",
                 'Something went wrong, please check the parameters and try again. Is the target file already open?')


def binary_data(num_ones_array, an_bit_count):
    binSheet = pd.DataFrame()  # Array to Pandas Column
    binSheet['Ones'] = num_ones_array
    binSheet.dropna(inplace=True)
    binSheet = binSheet.reset_index()
    binSheet['index'] = binSheet['index'] + 1
    binSheet = binSheet.rename(columns={'index': 'Sample'})
    binSheet['Sum'] = binSheet['Ones'].cumsum()
    binSheet['Average'] = binSheet['Sum'] / (binSheet['Sample'])
    binSheet['Zscore'] = (binSheet['Average'] - (an_bit_count / 2)) / (
            ((an_bit_count / 4) ** 0.5) / (binSheet['Sample'] ** 0.5))
    return binSheet


def ztest_pandas(data_file, an_bit_count):
    ztest = pd.read_csv(data_file, sep=' ', names=["Time", "Ones"])
    ztest.dropna(inplace=True)
    ztest = ztest.reset_index()
    ztest['index'] = ztest['index'] + 1
    ztest = ztest.rename(columns={'index': 'Sample'})
    ztest['Sum'] = ztest['Ones'].cumsum()
    ztest['Average'] = ztest['Sum'] / (ztest['Sample'])
    ztest['Zscore'] = (ztest['Average'] - (an_bit_count / 2)) / (((an_bit_count / 4) ** 0.5) / (ztest['Sample'] ** 0.5))
    return ztest


def create_chart(workbook, data_file2, an_bit_count, an_time_count):
    chart = workbook.add_chart({'type': 'line'})
    chart.set_title({'name': 'Z-Score: ' + data_file2, 'name_font': {'name': 'Calibri', 'color': 'black', }, })

    chart.set_x_axis({'name': f'Number of samples (one sample every {an_time_count} second(s))',
                      'name_font': {'name': 'Calibri', 'color': 'black'},
                      'num_font': {'name': 'Calibri', 'color': 'black', }, })

    chart.set_y_axis(
        {'name': f'Z-Score - Sample Size = {an_bit_count} bits ', 'name_font': {'name': 'Calibri', 'color': 'black'},
         'num_font': {'color': 'black', }, })

    chart.set_legend({'position': 'none'})
    return chart


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
