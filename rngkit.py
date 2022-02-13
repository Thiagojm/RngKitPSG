import os

if os.path.exists("src/others/checker"):
    os.remove("src/others/checker")

os.startfile("main.py")

import PySimpleGUI as sg

FILENAME = r'src/images/bitb.png'  # if you want to use a file instead of data, then use this in Image Element

gif = r"src/images/line_boxes.gif"

layout = [[sg.Image(FILENAME)],
          [sg.T(" ", size=(18,1)), sg.Image(gif, key='-GIF-')]]

window = sg.Window('Window Title', layout, transparent_color=sg.theme_background_color(), no_titlebar=True)

a = 0
while True:
    event, values = window.read(timeout=30)
    a += 1
    if os.path.exists("src/others/checker"):
        os.remove("src/others/checker")
        break
    if a == 1666:
        break
    if event == sg.WIN_CLOSED:  # always,  always give a way out!
        break
    window['-GIF-'].update_animation(gif, time_between_frames=60)