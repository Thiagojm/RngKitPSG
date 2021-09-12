# Default imports
import time
import threading
import subprocess
from time import localtime, strftime

# External imports
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib import style
from bitstring import BitArray
import serial
from serial.tools import list_ports

# Internal imports
import rng_module as rm

# Setting Globals
global thread_cap
thread_cap = False
global index_number_array
index_number_array = []
global zscore_array
zscore_array = []
global values
values = None


def main():
    # Mensagem para versão console
    print("""Welcome!
Wait for the application to load!
Do not close this window!""")

    with open("src/others/instructions.txt", "r", encoding="utf8") as f:
        instruction_text = f.read()

    # THEME
    # Good Ones: DarkBlue14, Dark, DarkBlue, DarkBlue3, DarkTeal1, DarkTeal10, DarkTeal9, LightGreen
    sg.theme('LightGreen')

    # TAB 1 - Collect / Analyse

    column_1 = [[sg.T("Choose RNG", size=(25, 1))], [sg.Radio('BitBabbler', "radio_graph_1", k="bit_ac", default=True)],
                [sg.Radio('TrueRNG', "radio_graph_1", k="true3_ac")],
                [sg.Radio('TrueRNG + BitBabbler', "radio_graph_1", k="true3_bit_ac")]]

    column_2 = [[sg.T("RAW(0)/XOR (1,2...):", size=(18, 1)),
                 sg.InputCombo((0, 1, 2, 3, 4), default_value=0, size=(5, 1), k="ac_combo", enable_events=False,
                               readonly=True), sg.T(" ", size=(4, 1))],
                [sg.T("Sample Size (bits):", size=(18, 1)), sg.Input(
                    "2048", k="ac_bit_count", size=(6, 1))],
                [sg.T("Sample Interval (s):", size=(18, 1)),
                 sg.Input("1", k="ac_time_count", size=(6, 1))],
                [sg.T(" ")]]

    column_3 = [[sg.B("Start", k='ac_button', size=(20, 1))], [sg.T("")],
                [sg.T("        Idle", k="stat_ac", text_color="orange", size=(10, 1), relief="sunken")]]

    acquiring_data = [[sg.T(" ")],
                      [sg.Column(column_1), sg.Column(column_2), sg.Column(
                          column_3, element_justification="center")],
                      [sg.T(" ")]]

    data_analysis = [[sg.T(" ")], [sg.T(" ", size=(8, 1)), sg.T("Sample Size (bits):", size=(18, 1)),
                                   sg.Input("2048", k="an_bit_count", size=(
                                       6, 1)), sg.T(" ", size=(8, 1)),
                                   sg.T("Sample Interval (s):", size=(18, 1)),
                                   sg.Input("1", k="an_time_count", size=(6, 1))], [sg.T(" ")],
                     [sg.Text('Select file:', size=(10, 1)), sg.Input(size=(60, 1)),
                      sg.FileBrowse(key='open_file', file_types=(('CSV and Binary', '.csv .bin'),),
                                    initial_folder="./1-SavedFiles", size=(8, 1)), sg.T(" ", size=(13, 1))],
                     [sg.T(" ", size=(24, 1)), sg.B("Generate"), sg.T(" ", size=(1, 1)),
                      sg.B("Open Output Folder", k="out_folder")],
                     [sg.Text('Concatenate Multiple CSV Files')],
                     [sg.In(), sg.FilesBrowse(key='open_files', file_types=(
                         ('CSV', '.csv'),), initial_folder="./1-SavedFiles", size=(8, 1), files_delimiter=","), sg.B('Concatenate', k="concat")],
                     ]

    tab1_layout = [
        [sg.Frame("Acquiring Data", font="Calibri, 20",
                  layout=acquiring_data, k="acquiring_data", size=(90, 9))],
        [sg.Frame("Data Analysis", font="Calibri, 20", layout=data_analysis, k="data_analysis", size=(90, 9))]]

    # TAB 2 - Gráfico
    column_graph_1 = [[sg.T("Choose RNG", size=(22, 1))],
                      [sg.Radio('BitBabbler', "radio_graph",
                                k="bit_live", default=True)],
                      [sg.Radio('TrueRNG3', "radio_graph", k="true3_live")]]

    column_graph_2 = [[sg.T("RAW(0)/XOR (1,2):", size=(16, 1)),
                       sg.InputCombo((0, 1), default_value=0, size=(5, 1), k="live_combo", enable_events=False,
                                     readonly=True), sg.T(" ", size=(9, 1))],
                      [sg.T("Sample Size (bits):", size=(16, 1)), sg.Input(
                          "2048", k="live_bit_count", size=(6, 1))],
                      [sg.T("Sample Interval (s):", size=(16, 1)), sg.Input("1", k="live_time_count", size=(6, 1))]]

    column_graph_3 = [[sg.B("Start", k='live_plot', size=(20, 1))], [sg.T("")],
                      [sg.T("        Idle", k="stat_live", text_color="orange", size=(10, 1), relief="sunken")]]

    graph_options = [[sg.Column(column_graph_1), sg.Column(column_graph_2),
                      sg.Column(column_graph_3, element_justification="center")]]

    live_graph = [[sg.Canvas(key='-CANVAS-')]]

    tab2_layout = [[sg.Frame("Options", font="Calibri, 20", layout=graph_options, k="graph_options", size=(90, 9))],
                   [sg.Frame("Live Plot", font="Calibri, 20", layout=live_graph, k="graph", size=(90, 9))]]

    # TAB 3 - Instruções
    tab3_layout = [[sg.T("Instructions", relief="raised", justification="center", size=(70, 1), font=("Calibri, 24"))],
                   [sg.Multiline(default_text=instruction_text, size=(75, 19), disabled=True, enable_events=False,
                                 font=("Calibri, 20"), pad=(5, 5))]]

    # LAYOUT
    layout = [[sg.TabGroup(
        [[sg.Tab('Start', tab1_layout), sg.Tab(
            'Live Plot', tab2_layout), sg.Tab('Instructions', tab3_layout)]],
        tab_location="top", font="Calibri, 18")]]

    # WINDOW
    window = sg.Window("RngKit ver 2.1.5 - by Thiago Jung - thiagojm1984@hotmail.com", layout, size=(1024, 720),
                       location=(50, 50), finalize=True, element_justification="center", font="Calibri 18",
                       resizable=True, icon=("src/images/BitB.ico"))

    # Setting things up!
    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas
    style.use("ggplot")
    global ax
    f, ax = plt.subplots(figsize=(10, 4.4), dpi=100)
    canvas = FigureCanvasTkAgg(f, canvas)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
    ani = animation.FuncAnimation(f, animate, interval=1000)

    # Creating checker for the splashscreen
    open("src/others/checker", mode='w').close()

    # LOOP
    while True:
        global values
        global thread_cap
        event, values = window.read()
        if event == sg.WIN_CLOSED:  # always,  always give a way out!
            break
        elif event == 'ac_button':
            if not thread_cap:
                if rm.test_bit_time_rate(values["ac_bit_count"], values["ac_time_count"]) and rm.check_usb_cap(values):
                    thread_cap = True
                    threading.Thread(target=ac_data, args=(
                        values, window), daemon=True).start()
                    window['ac_button'].update("Stop")
                    window["stat_ac"].update(
                        "  Collecting", text_color="green")
                    window['live_plot'].update("Stop")
                    window["stat_live"].update(
                        "  Collecting", text_color="green")
            else:
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")

        elif event == "out_folder":
            rm.open_folder()
        elif event == "concat":
            all_files = values['open_files'].split(",")
            rm.concat_files(all_files)
        elif event == "Generate":
            if rm.test_bit_time_rate(values["an_bit_count"], values["an_time_count"]):
                rm.file_to_excel(
                    values["open_file"], values["an_bit_count"], values["an_time_count"])
            else:
                pass
        elif event == 'live_plot':
            if not thread_cap:
                if rm.test_bit_time_rate(values["live_bit_count"], values["live_time_count"]) and rm.check_usb_live(values):
                    thread_cap = True
                    ax.clear()
                    threading.Thread(target=live_plot, args=(
                        values, window), daemon=True).start()
                    window['live_plot'].update("Stop")
                    window["stat_live"].update(
                        "  Collecting", text_color="green")
                    window['ac_button'].update("Stop")
                    window["stat_ac"].update(
                        "  Collecting", text_color="green")
            else:
                thread_cap = False
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")

    window.close()


def animate(i):
    global ax
    global index_number_array
    global zscore_array
    global values
    ax.clear()
    ax.plot(index_number_array, zscore_array, color='orange')
    ax.set_title("Live Plot")
    if not values:
        ax.set_xlabel(
            f'Number of samples (one sample every 1 second(s))', fontsize=10)
        ax.set_ylabel(f'Z-Score - Sample Size = 2048 bits', fontsize='medium')
    else:
        ax.set_xlabel(
            f'Number of samples (one sample every {values["live_time_count"]} second(s))', fontsize=10)
        ax.set_ylabel(
            f'Z-Score - Sample Size = {values["live_bit_count"]} bits', fontsize='medium')


# ---------------- Acquire Data Functions -------
def ac_data(values, window):
    if values["bit_ac"]:
        bit_cap(values, window)
    elif values['true3_ac']:
        trng3_cap(values, window)
    elif values["true3_bit_ac"]:
        threading.Thread(target=bit_cap, args=(
            values, window), daemon=True).start()
        trng3_cap(values, window)


def bit_cap(values, window):
    xor_value = values["ac_combo"]
    sample_value = int(values["ac_bit_count"])
    interval_value = int(values["ac_time_count"])
    global thread_cap
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    file_name = time.strftime(
        f"%Y%m%d-%H%M%S_bitb_s{sample_value}_i{interval_value}_f{xor_value}")
    file_name = f"1-SavedFiles/{file_name}"
    while thread_cap:
        start_cap = time.time()
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file
            proc = subprocess.Popen(
                f"src/bin/seedd.exe --limit-max-xfer --no-qa -f{xor_value} -b {int(sample_value / 8)}",
                stdout=subprocess.PIPE, startupinfo=startupinfo)
            chunk = proc.stdout.read()
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
            window['live_plot'].update("Start")
            window["stat_live"].update("        Idle", text_color="orange")
            return
        # count numbers of ones in the string
        num_ones_array = bin_ascii.count('1')
        # open file and append time and number of ones
        with open(file_name + '.csv', "a+") as write_file:
            write_file.write(
                f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
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
    file_name = time.strftime(
        f"%Y%m%d-%H%M%S_trng_s{sample_value}_i{interval_value}")
    file_name = f"1-SavedFiles/{file_name}"
    while thread_cap:
        start_cap = time.time()
        with open(file_name + '.bin', "ab") as bin_file:  # save binary file
            try:
                # timeout set at 10 seconds in case the read fails
                ser = serial.Serial(port=rng_com_port, timeout=10)
                if (ser.isOpen() == False):
                    ser.open()
                ser.setDTR(True)
                ser.flushInput()
            except Exception:
                rm.popupmsg(
                    "Warning!", f"Port Not Usable! Do you have permissions set to read {rng_com_port}?")
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                break
            try:
                x = ser.read(blocksize)  # read bytes from serial port
            except Exception:
                rm.popupmsg("Warning!", "Read failed!")
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                break
            bin_file.write(x)
            ser.close()
        bin_hex = BitArray(x)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        # count numbers of ones in the string
        num_ones_array = bin_ascii.count('1')
        # open file and append time and number of ones
        with open(file_name + '.csv', "a+") as write_file:
            write_file.write(
                f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(interval_value - (end_cap - start_cap))
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass


# ----------------Live Plot Functions------------

# TODO: use secrets to make new capturing function

def live_plot(values, window):
    if values['bit_live']:
        livebblaWin(values, window)
    elif values['true3_live']:
        trng3live(values, window)


def livebblaWin(values, window):  # Function to take live data from bitbabbler
    global thread_cap
    global zscore_array
    global index_number_array
    thread_cap = True
    xor_value = values['live_combo']
    sample_value = int(values["live_bit_count"])
    interval_value = int(values["live_time_count"])
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    file_name = time.strftime(
        f"%Y%m%d-%H%M%S_bitb_s{sample_value}_i{interval_value}_f{xor_value}")
    file_name = f"1-SavedFiles/{file_name}"
    index_number = 0
    csv_ones = []
    zscore_array = []
    index_number_array = []
    while thread_cap:
        start_cap = time.time()
        index_number += 1
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file
            proc = subprocess.Popen(
                f"src/bin/seedd.exe --limit-max-xfer --no-qa -f{xor_value} -b {int(sample_value / 8)}",
                stdout=subprocess.PIPE, startupinfo=startupinfo)
            chunk = proc.stdout.read()
            bin_file.write(chunk)
        bin_hex = BitArray(chunk)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        if not bin_ascii:
            thread_cap = False
            sg.popup_non_blocking('WARNING !!!',
                                  "Something went wrong, is the device attached? Attach it and try again!!!",
                                  keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                                  icon="src/BitB.ico")
            window['live_plot'].update("Start")
            window["stat_live"].update("        Idle", text_color="orange")
            window['ac_button'].update("Start")
            window["stat_ac"].update("        Idle", text_color="orange")
            return
        # count numbers of ones in the string
        num_ones_array = bin_ascii.count('1')
        csv_ones.append(num_ones_array)
        sums_csv = sum(csv_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (sample_value / 2)) / \
            (((sample_value / 4) ** 0.5) / (index_number ** 0.5))
        zscore_array.append(zscore_csv)
        index_number_array.append(index_number)
        # open file and append time and number of ones
        with open(file_name + '.csv', "a+") as write_file:
            write_file.write(
                f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(interval_value - (end_cap - start_cap))
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass


def trng3live(values, window):
    global thread_cap
    global zscore_array
    global index_number_array
    thread_cap = True
    sample_value = int(values["live_bit_count"])
    interval_value = int(values["live_time_count"])
    file_name = time.strftime(
        f"%Y%m%d-%H%M%S_trng_s{sample_value}_i{interval_value}")
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
    while thread_cap:
        start_cap = time.time()
        index_number += 1
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file
            try:
                # timeout set at 10 seconds in case the read fails
                ser = serial.Serial(port=rng_com_port, timeout=10)
            except Exception:
                thread_cap = False
                rm.popupmsg(
                    "Warning!", f"Port Not Usable! Do you have permissions set to read {rng_com_port}?")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                return
            # Open the serial port if it isn't open
            if (ser.isOpen() == False):
                try:
                    ser.open()
                except Exception:
                    thread_cap = False
                    sg.popup_non_blocking('WARNING !!!',
                                          "Something went wrong, is the device attached? Attach it and try again!!!",
                                          keep_on_top=True, no_titlebar=False, grab_anywhere=True, font="Calibri, 18",
                                          icon="src/BitB.ico")
                    window['live_plot'].update("Start")
                    window["stat_live"].update(
                        "        Idle", text_color="orange")
                    window['ac_button'].update("Start")
                    window["stat_ac"].update(
                        "        Idle", text_color="orange")
                    return
            # Set Data Terminal Ready to start flow
            ser.setDTR(True)
            # This clears the receive buffer so we aren't using buffered data
            ser.flushInput()
            try:
                chunk = ser.read(blocksize)  # read bytes from serial port
            except Exception:
                thread_cap = False
                rm.popupmsg("Warning!", "Read Failed!!!")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                return
            bin_file.write(chunk)
            # Close the serial port
            ser.close()
        bin_hex = BitArray(chunk)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        # count numbers of ones in the 2048 string
        num_ones_array = int(bin_ascii.count('1'))
        csv_ones.append(num_ones_array)
        sums_csv = sum(csv_ones)
        avrg_csv = sums_csv / index_number
        zscore_csv = (avrg_csv - (sample_value / 2)) / \
            (((sample_value / 4) ** 0.5) / (index_number ** 0.5))
        zscore_array.append(zscore_csv)
        index_number_array.append(index_number)
        # open file and append time and number of ones
        with open(file_name + '.csv', "a+") as write_file:
            write_file.write(
                f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(interval_value - (end_cap - start_cap) / 1000)
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass


if __name__ == '__main__':
    main()
