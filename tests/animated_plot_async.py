import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from random import randint
import time
import threading
import asyncio

# Usage of MatPlotLib with matplotlib.animation for better performance

def main():
    sg.theme('DarkBlue14')


    layout = [[sg.Text('Live Plot Matplotlib - FuncAnimation')],
              [sg.Canvas(k="-CANVAS-")],
              [sg.Button('Start'), sg.Button('Stop'), sg.Exit()]]

    window = sg.Window('Live Plot Matplotlib - FuncAnimation', layout, size=(640, 580),
                       location=(50, 50), finalize=True, element_justification="center", font="Calibri 18",
                       resizable=True)

    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas
    style.use("ggplot")
    global ax
    f, ax = plt.subplots(figsize=(10, 4.4), dpi=100)
    canvas = FigureCanvasTkAgg(f, canvas)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
    global xar
    global yar
    xar = [1, 2, 3, 4]
    yar = [10, 5, 3, 5]
    ani = animation.FuncAnimation(f, animate, interval=1000)

    while True:                             # The Event Loop
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        elif event == "Start":
            global thread
            thread = True
            # x = threading.Thread(target=live_plotting, daemon=True)
            # x.start()
            xar = async_return(xar, yar)
        elif event == "Stop":
            thread = False

    window.close()


def animate(i):
    global ax
    global xar
    global yar
    ax.clear()
    ax.plot(xar, yar, color='orange')
    ax.set_title("Live Plot")
    ax.set_xlabel('X-Label', fontsize=10)
    ax.set_ylabel('Y-Label', fontsize='medium')


def live_plotting():
    global xar
    global yar
    global thread
    while thread:
        xar.append(xar[len(xar) - 1] + 1)
        yar.append(randint(0, 10))
        time.sleep(1)


async def async_plot(xar, yar):
    xar.append(xar[len(xar) - 1] + 1)
    #yar.append(randint(0, 10))
    #await asyncio.sleep(1)
    return xar

async def async_return(xar, yar):
    task = asyncio.create_task(async_plot(xar, yar))
    xar = await task
    return xar



if __name__ == '__main__':
    main()