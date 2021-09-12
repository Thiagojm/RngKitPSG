import PySimpleGUI as sg
import sys
from contextlib import ExitStack
import time


def concat_files(all_filenames):
    file_name = time.strftime(f"%Y%m%d-%H%M%S")
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in all_filenames]
        with open(f"1-SavedFiles/{file_name}_concat.csv", "a") as f:
            for file in files:
                for line in file:
                    f.write(line)


if len(sys.argv) == 1:
    event, values = sg.Window('My Script',
                              [[sg.Text('Document to open')],
                               [sg.In(), sg.FilesBrowse(key='open_files', file_types=(
                                   ('CSV', '.csv'),), initial_folder="./1-SavedFiles", size=(8, 1), files_delimiter=",")],
                                  [sg.Open(), sg.Cancel()]]).read(close=True)
    fname = values['open_files'].split(",")
else:
    fname = sys.argv[1]

if not fname:
    sg.popup("Cancel", "No filename supplied")
    raise SystemExit("Cancelling: no filename supplied")
else:
    sg.popup('The filename you chose was', fname)
    #print(type(fname), fname)

    concat_files(fname)
