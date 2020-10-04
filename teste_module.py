# Default imports
import re
from datetime import datetime
import time
import os

# External imports
import pandas as pd
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from bitstring import BitArray


# Internal imports

def popupmsg(msg_title, msg):
    sg.popup_non_blocking(msg_title, msg, keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                          icon="src/BitB.ico")


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def open_folder():
    script_path = os.getcwd()
    path = f"{script_path}/1-SavedFiles/"
    path = os.path.realpath(path)
    os.startfile(path)


# ----------------- Analyse Data --------------------------
def file_to_excel(data_file, an_bit_count, an_time_count):
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
        chart = create_chart(workbook, data_file2)
        chart.add_series({'values': ['Z-Test', 1, 5, number_rows, 5], 'categories': ['Z-Test', 1, 1, number_rows, 1]})
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
        chart = create_chart(workbook, data_file2)
        chart.add_series({'values': ['Z-Test', 1, 4, number_rows, 4], 'categories': ['Z-Test', 1, 0, number_rows, 0]})
        worksheet.insert_chart('G2', chart)
        writer.save()
        popupmsg('File Saved', 'Saved as ' + file_to_save)
        return
    else:
        popupmsg("Warning", 'Wrong File Type, Select a .bin or .csv file')
        pass


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


def create_chart(workbook, data_file2):
    chart = workbook.add_chart({'type': 'line'})
    chart.set_title({'name': 'Z-Score: ' + data_file2, 'name_font': {'name': 'Calibri', 'color': 'black', }, })

    chart.set_x_axis({'name': 'Time', 'name_font': {'name': 'Calibri', 'color': 'black'},
                      'num_font': {'name': 'Calibri', 'color': 'black', }, })

    chart.set_y_axis(
        {'name': 'Z-Score', 'name_font': {'name': 'Calibri', 'color': 'black'}, 'num_font': {'color': 'black', }, })

    chart.set_legend({'position': 'none'})
    return chart


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
