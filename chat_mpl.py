import time
import datetime
import signal
from secrets import token_bytes
from bitstring import BitArray
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from threading import Thread

# Global flag to stop the data collection thread
stop_flag = False

# Global lists to store data for the plot
x_data = []
y_data = []

def handle_interrupt(signal, frame):
    global stop_flag
    stop_flag = True
    print('Data collection stopped by user.')

signal.signal(signal.SIGINT, handle_interrupt)

def collect_random_numbers(blocksize: int, interval_value: int, file_name: str) -> None:
    """
    A function to collect random numbers, save to a .bin file, count number of ones, 
    and save timestamp and count to a .csv file. 

    blocksize: Number of bytes
    interval_value: Interval between collections in seconds
    file_name: Base name for the output files
    """
    global stop_flag, x_data, y_data
    while not stop_flag:
        start_cap = time.time()
        with open(f'{file_name}.bin', "ab") as bin_file:
            data = token_bytes(blocksize)
            bin_file.write(data)

        bin_hex = BitArray(data)
        bin_ascii = bin_hex.bin
        num_ones = bin_ascii.count('1')

        now = datetime.datetime.now().replace(microsecond=0)
        with open(f'{file_name}.csv', "a+") as write_file:
            write_file.write(f'{now},{num_ones}\n')

        x_data.append(now)
        y_data.append(num_ones)

        end_cap = time.time()
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except ValueError:
            print('Warning: data collection is slower than the specified interval.')

def animate(i: int) -> None:
    """
    Function to animate the matplotlib figure. 

    i: The current frame number (ignored in this function)
    """
    plt.cla()
    plt.plot(x_data, y_data)
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.20)

if __name__ == "__main__":
    blocksize = 256 # in bytes
    interval_value = 1 # in seconds
    file_name = 'output'

    data_collection_thread = Thread(target=collect_random_numbers, args=(blocksize, interval_value, file_name))
    data_collection_thread.start()

    fig = plt.figure()
    ani = animation.FuncAnimation(fig, animate, interval=1000)
    plt.show()

    stop_flag = True
    print('Data collection stopped.')
