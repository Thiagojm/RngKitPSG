

def pseudo_cap(values, window):
    global thread_cap
    sample_value = int(values["ac_bit_count"])
    interval_value = int(values["ac_time_count"])
    blocksize = int(sample_value / 8)
    file_name = time.strftime(
        f"%Y%m%d-%H%M%S_pseudo_s{sample_value}_i{interval_value}")
    file_name = f"1-SavedFiles/{file_name}"
    while thread_cap:
        start_cap = time.time()
        with open(file_name + '.bin', "ab") as bin_file:  # save binary file
            try:
                x = secrets.token_bytes(blocksize)  # read bytes from serial port
            except Exception:
                rm.popupmsg("Warning!", "Read failed!")
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                window['live_plot'].update("Start")
                window["stat_live"].update("        Idle", text_color="orange")
                break
            bin_file.write(x)
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