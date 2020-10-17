import PySimpleGUI as sg
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pandas._libs.tslibs.base


array_is = np.ones((3,4))
print(array_is)
s = pd.Series([1, 3, 5, np.nan, 6, 8])
print(s)
sg.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
layout = [  [sg.Text('Some text on Row 1')],
            [sg.Text('Enter something on Row 2'), sg.InputText()],
            [sg.Button('Ok'), sg.Button('Cancel')] ]

# Create the Window
window = sg.Window('Window Title', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
        break
    print('You entered ', values[0])
    if event == "Ok":
        sg.popup_auto_close(f"Boa: {values[0]}, {array_is}, {s}")

window.close()
