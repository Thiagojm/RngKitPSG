# Default imports
import time
import threading
import subprocess
from time import localtime, strftime

# External imports
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib import style
from bitstring import BitArray
import serial
from serial.tools import list_ports

# Internal imports
import teste_module as rm

global thread_live
thread_live = False
global thread_cap
thread_cap = False
global index_number_array
index_number_array = []
global zscore_array
zscore_array = []


def main():
    # Mensagem para versão console
    print("""Welcome!
Wait for the application to load!
Do not close this window!""")

    with open("src/instructions.txt", "r", encoding="utf8") as f:
        texto = f.read()

    # THEME
    # Good Ones: DarkBlue14, Dark, DarkBlue, DarkBlue3, DarkTeal1, DarkTeal10, DarkTeal9, LightGreen
    sg.theme('DarkBlue')

    # TAB 1 - Capture / Analyse

    column_1 = [[sg.T("Choose RNG")], [sg.Radio('BitBabbler', "radio_graph_1", k="bit_ac", default=True)],
                [sg.Radio('TrueRNG', "radio_graph_1", k="true3_ac")],
                [sg.Radio('TrueRNG + BitBabbler', "radio_graph_1", k="true3_bit_ac")]]

    column_2 = [[sg.T("RAW(0)/XOR (1,2...)"),
                 sg.InputCombo((0, 1, 2, 3, 4), default_value=0, size=(4, 1), k="ac_combo", enable_events=False,
                               readonly=True)],
                [sg.T("Sample Size (bits):"), sg.Input("2048", k="ac_bit_count", size=(6, 1))],
                [sg.T("Sample Interval (s):"), sg.Input("1", k="ac_time_count", size=(6, 1))], [sg.T(" ")]]

    column_3 = [[sg.B("Start", k='ac_button', size=(20, 1))], [sg.T("")],
                [sg.T("        Idle", k="stat_ac", text_color="orange", size=(10, 1), relief="sunken")]]

    acquiring_data = [[sg.Column(column_1), sg.Column(column_2), sg.Column(column_3, element_justification="center")]]

    data_analysis = [
        [sg.T("Sample Size (bits):"), sg.Input("2048", k="an_bit_count", size=(6, 1)), sg.T("Sample Interval (s):"),
         sg.Input("1", k="an_time_count", size=(6, 1))], [sg.T(" ")], [sg.Text('Select file:'), sg.Input(),
                                                                       sg.FileBrowse(key='open_file', file_types=(
                                                                           ('CSV and Binary', '.csv .bin'),),
                                                                                     initial_folder="./1-SavedFiles")],
        [sg.B("Generate"), sg.B("Open Output Folder", k="out_folder")]]

    tab1_layout = [[sg.Frame("Acquiring Data", layout=acquiring_data, k="acquiring_data", size=(90, 9))],
                   [sg.Frame("Data Analysis", layout=data_analysis, k="data_analysis", size=(90, 9))]]

    # TAB 2 - Gráfico
    column_graph_1 = [[sg.T("Choose RNG")], [sg.Radio('BitBabbler', "radio_graph", k="bit_live", default=True, size=(19, 1))],
                [sg.Radio('TrueRNG3', "radio_graph", k="true3_live", size=(20, 1))]]

    column_graph_2 = [[sg.T("RAW(0)/XOR (1,2)"),
                 sg.InputCombo((0, 1), default_value=0, size=(4, 1), k="live_combo", enable_events=False,
                                    readonly=True)],
                [sg.T("Sample Size (bits):"), sg.Input("2048", k="live_bit_count", size=(6, 1))],
                [sg.T("Sample Interval (s):"), sg.Input("1", k="live_time_count", size=(6, 1))]]

    column_graph_3 = [[sg.B("Start", k='live_plot', size=(20, 1))], [sg.T("")],
                [sg.T("        Idle", k="stat_live", text_color="orange", size=(10, 1), relief="sunken")]]

    graph_options = [[sg.Column(column_graph_1), sg.Column(column_graph_2), sg.Column(column_graph_3, element_justification="center")]]

    live_graph = [[sg.Canvas(key='-CANVAS-')]]

    tab2_layout = [[sg.Frame("Options", layout=graph_options, k="graph_options", size=(90, 9))],
                   [sg.Frame("Live Plot", layout=live_graph, k="graph", size=(90, 9))]]

    # TAB 3 - Instruções
    tab3_layout = [[sg.T("Instructions", relief="raised", justification="center", size=(70, 1), font=("Calibri, 24"))],
                   [sg.Multiline(default_text=texto, size=(75, 19), disabled=True, enable_events=False,
                                 font=("Calibri, 20"), pad=(5, 5))]]

    # LAYOUT
    layout = [[sg.TabGroup(
        [[sg.Tab('Start', tab1_layout), sg.Tab('Live Plot', tab2_layout), sg.Tab('Instructions', tab3_layout)]],
        tab_location="top", font="Calibri, 18")]]

    # WINDOW
    window = sg.Window("RngKit ver 2.0.0 - by Thiago Jung - thiagojm1984@hotmail.com", layout, size=(1024, 720),
                       location=(50, 50), finalize=True, element_justification="center", font="Calibri 18",
                       resizable=True, icon=("src/BitB.ico"))

    # Setting things up!
    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas
    # draw the intitial plot
    style.use("ggplot")
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    fig_agg = rm.draw_figure(canvas, fig)

    # LOOP
    while True:
        event, values = window.read(timeout=200)
        if event == sg.WIN_CLOSED:  # always,  always give a way out!
            break
        elif event == 'ac_button':
            global thread_cap
            if not thread_cap:
                thread_cap = True
                threading.Thread(target=ac_data, args=(values, window), daemon=True).start()
                window['ac_button'].update("Stop")
                window["stat_ac"].update("  Capturing", text_color="green")
            else:
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
        elif event == "out_folder":
            rm.open_folder()
        elif event == "Generate":
            rm.file_to_excel(values["open_file"], values["an_bit_count"], values["an_time_count"])
        elif event == 'live_plot':
            global thread_live
            if not thread_live:
                thread_live = True
                ax.clear()
                threading.Thread(target=live_plot, args=(values, window), daemon=True).start()
                window['live_plot'].update("Stop")
                window["stat_live"].update("  Capturing", text_color="green")
            else:
                thread_live = False
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
        # Live Plot on Loop
        ax.plot(index_number_array, zscore_array, color='orange')
        ax.set_title("Live Plot")
        ax.set_xlabel(f'One sample every {values["live_time_count"]} second(s)', fontsize=10)
        ax.set_ylabel(f'Z-Score - Sample Size = {values["live_bit_count"]} bits', fontsize='medium')
        fig_agg.draw()
    window.close()


# ---------------- Acquire Data Functions -------
def ac_data(values, window):
    if values["bit_ac"]:
        bit_cap(values, window)
    elif values['true3_ac']:
        trng3_cap(values, window)
    elif values["true3_bit_ac"]:
        threading.Thread(target=bit_cap, args=(values, window), daemon=True).start()
        trng3_cap(values, window)


def bit_cap(values, window):
    xor_value = values["ac_combo"]
    sample_value = int(values["ac_bit_count"])
    interval_value = int(values["ac_time_count"])
    global thread_cap
    file_name = time.strftime(f"%Y%m%d-%H%M%S_bitb_s{sample_value}_i{interval_value}_f{xor_value}")
    file_name = f"1-SavedFiles/{file_name}"
    while thread_cap:
        start_cap = time.time()
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file
            proc = subprocess.run(
                f'datafiles/seedd.exe --limit-max-xfer --no-qa -f{xor_value} -b {int(sample_value / 8)}',
                stdout=subprocess.PIPE)
            chunk = proc.stdout
            bin_file.write(chunk)
        bin_hex = BitArray(chunk)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        if not bin_ascii:
            thread_cap = False
            sg.popup_non_blocking('WARNING !!!',
                                  "Something went wrong, is the device attached? Attach it and try again!!!",
                                  keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                                  icon="src/BitB.ico")
            window['ac_button'].update("Start")
            window["stat_ac"].update("        Idle", text_color="orange")
            break
        num_ones_array = bin_ascii.count('1')  # count numbers of ones in the string
        with open(file_name + '.csv', "a+") as write_file:  # open file and append time and number of ones
            write_file.write(f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(interval_value - (end_cap - start_cap))
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass


def trng3_cap(values, window):
    global thread_cap
    sample_value = int(values["ac_bit_count"])
    interval_value = int(values["ac_time_count"])
    blocksize = int(sample_value / 8)
    ports_avaiable = list(list_ports.comports())
    rng_com_port = None
    for temp in ports_avaiable:
        if temp[1].startswith("TrueRNG"):
            if rng_com_port == None:  # always chooses the 1st TrueRNG found
                rng_com_port = str(temp[0])
    file_name = time.strftime(f"%Y%m%d-%H%M%S_trng_s{sample_value}_i{interval_value}")
    file_name = f"1-SavedFiles/{file_name}"
    while thread_cap:
        start_cap = time.time()
        with open(file_name + '.bin', "ab") as bin_file:  # save binary file
            try:
                ser = serial.Serial(port=rng_com_port, timeout=10)  # timeout set at 10 seconds in case the read fails
                if (ser.isOpen() == False):
                    ser.open()
                ser.setDTR(True)
                ser.flushInput()
            except Exception:
                rm.popupmsg("Warning!", f"Port Not Usable! Do you have permissions set to read {rng_com_port}?")
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                break
            try:
                x = ser.read(blocksize)  # read bytes from serial port
            except Exception:
                rm.popupmsg("Warning!", "Read failed!")
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                break
            bin_file.write(x)
            ser.close()
        bin_hex = BitArray(x)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        num_ones_array = bin_ascii.count('1')  # count numbers of ones in the string
        with open(file_name + '.csv', "a+") as write_file:  # open file and append time and number of ones
            write_file.write(f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(interval_value - (end_cap - start_cap))
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass


# ----------------Live Plot Functions------------

def live_plot(values, window):
    if values['bit_live']:
        livebblaWin(values, window)
    elif values['true3_live']:
        trng3live(values, window)


def livebblaWin(values, window):  # Function to take live data from bitbabbler
    global thread_live
    global zscore_array
    global index_number_array
    thread_live = True
    xor_value = values['live_combo']
    sample_value = int(values["live_bit_count"])
    interval_value = int(values["live_time_count"])
    file_name = time.strftime(f"%Y%m%d-%H%M%S_bitb_s{sample_value}_i{interval_value}_f{xor_value}")
    file_name = f"1-SavedFiles/{file_name}"
    index_number = 0
    csv_ones = []
    zscore_array = []
    index_number_array = []
    while thread_live:
        start_cap = time.time()
        index_number += 1
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file
            proc = subprocess.run(
                f'datafiles/seedd.exe --limit-max-xfer --no-qa -f{xor_value} -b {int(sample_value / 8)}',
                stdout=subprocess.PIPE)
            chunk = proc.stdout
            bin_file.write(chunk)
        bin_hex = BitArray(chunk)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        if not bin_ascii:
            thread_live = False
            sg.popup_non_blocking('WARNING !!!',
                                  "Something went wrong, is the device attached? Attach it and try again!!!",
                                  keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                                  icon="src/BitB.ico")
            window['live_plot'].update("Start")
            window["stat_live"].update("        Idle", text_color="orange")
            break
        num_ones_array = bin_ascii.count('1')  # count numbers of ones in the string
        csv_ones.append(num_ones_array)
        sums_csv = sum(csv_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (sample_value / 2)) / (((sample_value / 4) ** 0.5) / (index_number ** 0.5))
        zscore_array.append(zscore_csv)
        index_number_array.append(index_number)
        with open(file_name + '.csv', "a+") as write_file:  # open file and append time and number of ones
            write_file.write(f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        #print(interval_value - (end_cap - start_cap))
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass


def trng3live(values, window):
    global thread_live
    global zscore_array
    global index_number_array
    thread_live = True
    sample_value = int(values["live_bit_count"])
    interval_value = int(values["live_time_count"])
    file_name = time.strftime(f"%Y%m%d-%H%M%S_trng_s{sample_value}_i{interval_value}")
    file_name = f"1-SavedFiles/{file_name}"
    index_number = 0
    csv_ones = []
    zscore_array = []
    index_number_array = []
    blocksize = int(sample_value / 8)
    ports_avaiable = list(list_ports.comports())
    rng_com_port = None
    # Loop on all available ports to find TrueRNG
    for temp in ports_avaiable:
        if temp[1].startswith("TrueRNG"):
            if rng_com_port == None:  # always chooses the 1st TrueRNG found
                rng_com_port = str(temp[0])
    while thread_live:
        start_cap = time.time()
        index_number += 1
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file
            try:
                ser = serial.Serial(port=rng_com_port, timeout=10)  # timeout set at 10 seconds in case the read fails
            except Exception:
                thread_live = False
                rm.popupmsg("Warning!", f"Port Not Usable! Do you have permissions set to read {rng_com_port}?")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                return
            # Open the serial port if it isn't open
            if (ser.isOpen() == False):
                try:
                    ser.open()
                except Exception:
                    thread_live = False
                    sg.popup_non_blocking('WARNING !!!',
                                          "Something went wrong, is the device attached? Attach it and try again!!!",
                                          keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                                          icon="src/BitB.ico")
                    window['live_plot'].update("Start")
                    window["stat_live"].update("        Idle", text_color="orange")
                    return
            # Set Data Terminal Ready to start flow
            ser.setDTR(True)
            # This clears the receive buffer so we aren't using buffered data
            ser.flushInput()
            try:
                chunk = ser.read(blocksize)  # read bytes from serial port
            except Exception:
                thread_live = False
                rm.popupmsg("Warning!", "Read Failed!!!")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                return
            bin_file.write(chunk)
            # Close the serial port
            ser.close()
        bin_hex = BitArray(chunk)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        num_ones_array = int(bin_ascii.count('1'))  # count numbers of ones in the 2048 string
        csv_ones.append(num_ones_array)
        sums_csv = sum(csv_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (sample_value / 2)) / (((sample_value / 4) ** 0.5) / (index_number ** 0.5))
        zscore_array.append(zscore_csv)
        index_number_array.append(index_number)
        with open(file_name + '.csv', "a+") as write_file:  # open file and append time and number of ones
            write_file.write(f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(interval_value - (end_cap - start_cap) / 1000)
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass


if __name__ == '__main__':
    main()
