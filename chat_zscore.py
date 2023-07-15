import pandas as pd
import numpy as np
import os, re
import xlsxwriter
from bitstring import BitArray

# Constants
SHEET_NAME = 'Zscore'
ONES_COLUMN = 'ones'
BLOCK_COLUMN = 'samples'
TIMESTAMP_COLUMN = 'time'

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
    return pd.DataFrame(data_list, columns=[BLOCK_COLUMN, ONES_COLUMN])

# This function reads a .csv file and returns a DataFrame with timestamp and number of ones.
def read_csv_file(file_path):
    df = pd.read_csv(file_path, header=None, names=[TIMESTAMP_COLUMN, ONES_COLUMN])
    df[TIMESTAMP_COLUMN] = pd.to_datetime(df[TIMESTAMP_COLUMN]).apply(lambda x: x.strftime('%H:%M:%S'))
    return df

# This function calculates the cumulative mean and Z-test value and adds them as new columns to the DataFrame.
def calculate_z_test(dataframe, block_size):
    expected_mean = 0.5 * block_size
    expected_std_dev = np.sqrt(block_size * 0.5 * 0.5)
    dataframe['cumulative_mean'] = dataframe[ONES_COLUMN].expanding().mean()
    dataframe['z_test'] = (dataframe['cumulative_mean'] - expected_mean) / (expected_std_dev / np.sqrt(dataframe.index + 1))
    return dataframe

# This function writes the DataFrame to an Excel file, and adds a line chart to visualize the Z-test value.
def write_to_excel(dataframe, file_path, block_size, interval):
    file_to_save = os.path.splitext(file_path)[0]+'.xlsx'
    writer = pd.ExcelWriter(file_to_save, engine='xlsxwriter')
    dataframe.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    workbook = writer.book
    worksheet = writer.sheets[SHEET_NAME]

    chart = workbook.add_chart({'type': 'line'})

    chart.add_series({
        'categories': [SHEET_NAME, 1, 0, len(dataframe), 0],
        'values':     [SHEET_NAME, 1, 3, len(dataframe), 3],
    })

    chart.set_title({'name': os.path.basename(file_path)})
    chart.set_x_axis({'name': f'Number of Samples - one sample ervery {interval} second(s)', 'date_axis': True})
    chart.set_y_axis({'name': f'Z-Score - Sample Size =  {block_size} bits)'})
    
    chart.set_legend({'none': True})

    worksheet.insert_chart('F2', chart)

    writer.close()

# The main function prompts the user to enter file path and block size, then processes the file accordingly.
def main():
    file_path = input("Enter the path to the file: ")
    interval = find_interval(file_path)
    block_size = find_bit_count(file_path)
    if file_path.endswith(".bin"):
        df = read_bin_file(file_path, block_size)
    elif file_path.endswith(".csv"):
        df = read_csv_file(file_path)
    else:
        raise ValueError("Unsupported file type")
    
    df = calculate_z_test(df, block_size)
    write_to_excel(df, file_path, block_size, interval)
    

if __name__ == "__main__":    
    main()
    