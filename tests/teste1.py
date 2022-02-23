def pseudo_live(values, window):
    global thread_cap
    global zscore_array
    global index_number_array
    thread_cap = True
    sample_value = int(values["live_bit_count"])
    interval_value = int(values["live_time_count"])
    file_name = time.strftime(
        f"%Y%m%d-%H%M%S_pseudo_s{sample_value}_i{interval_value}")
    file_name = f"1-SavedFiles/{file_name}"
    index_number = 0
    csv_ones = []
    zscore_array = []
    index_number_array = []
    blocksize = int(sample_value / 8)
    while thread_cap:
        start_cap = time.time()
        index_number += 1
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file            
            try:
                chunk = secrets.token_bytes(blocksize)  # read bytes
            except Exception:
                thread_cap = False
                rm.popupmsg("Warning!", "Read Failed!!!")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                return
            bin_file.write(chunk)
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
