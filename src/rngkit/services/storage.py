import csv
import os
from contextlib import ExitStack
from datetime import datetime
from typing import Iterable, List

import pandas as pd
import numpy as np
import xlsxwriter  # type: ignore
from bitstring import BitArray  # type: ignore


def write_csv_count(count: int, filename_stem: str) -> None:
    now = datetime.now().strftime("%Y%m%dT%H:%M:%S")
    path = os.path.join(f"{filename_stem}.csv")
    with open(path, 'a', newline='') as f:
        csv.writer(f).writerow([now, count])


def read_bin_counts(file_path: str, block_bits: int) -> pd.DataFrame:
    data_list: List[List[int]] = []
    with open(file_path, 'rb') as binary_file:
        block = 1
        while True:
            data = binary_file.read(block_bits // 8)
            if not data:
                break
            ones = BitArray(data).count(1)
            data_list.append([block, ones])
            block += 1
    return pd.DataFrame(data_list, columns=['samples', 'ones'])


def read_csv_counts(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, header=None, names=['time', 'ones'])
    df['time'] = pd.to_datetime(df['time']).apply(lambda x: x.strftime('%H:%M:%S'))
    return df


def add_zscore(df: pd.DataFrame, block_bits: int) -> pd.DataFrame:
    expected_mean = 0.5 * block_bits
    expected_std_dev = np.sqrt(block_bits * 0.5 * 0.5)
    df['cumulative_mean'] = df['ones'].expanding().mean()
    df['z_test'] = (df['cumulative_mean'] - expected_mean) / (expected_std_dev / np.sqrt(df.index + 1))
    return df


def write_excel_with_chart(df: pd.DataFrame, file_path: str, block_bits: int, interval: int) -> str:
    out_path = os.path.splitext(file_path)[0] + '.xlsx'
    writer = pd.ExcelWriter(out_path, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Zscore', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Zscore']
    chart = workbook.add_chart({'type': 'line'})
    chart.add_series({'categories': ['Zscore', 1, 0, len(df), 0], 'values': ['Zscore', 1, 3, len(df), 3]})
    chart.set_title({'name': os.path.basename(file_path)})
    chart.set_x_axis({'name': f'Number of Samples - one sample every {interval} second(s)', 'date_axis': True})
    chart.set_y_axis({'name': f'Z-Score - Sample Size = {block_bits} bits'})
    chart.set_legend({'none': True})
    worksheet.insert_chart('F2', chart)
    writer.close()
    return out_path


def concat_csv_files(all_filenames: Iterable[str], out_stem: str) -> str:
    out_path = os.path.join(os.path.dirname(next(iter(all_filenames))), f"{out_stem}.csv")
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in all_filenames]
        with open(out_path, 'a') as out:
            for f in files:
                for line in f:
                    out.write(line)
    return out_path


