def bit_cap(values, window):  # criar função para quando o botão for clicado
    xor_value = values["ac_combo"]
    sample_value = int(values["ac_bit_count"])
    interval_value = int(values["ac_time_count"])
    global thread_cap
    file_name = time.strftime(f"%Y%m%d-%H%M%S_bitb_s{sample_value}_i{interval_value}_f{xor_value}")
    file_name = f"1-SavedFiles/{file_name}"
    while thread_cap:
        start_cap = time.time()
        with open(file_name + '.bin', "ab+") as bin_file:  # save binary file
            proc = subprocess.run(
                f'datafiles/seedd.exe --limit-max-xfer --no-qa -f{xor_value} -b {int(sample_value / 8)}',
                stdout=subprocess.PIPE)
            chunk = proc.stdout
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
            break
        num_ones_array = bin_ascii.count('1')  # count numbers of ones in the 2048 string
        with open(file_name + '.csv', "a+") as write_file:  # open file and append time and number of ones
            write_file.write(f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(1 - (end_cap - start_cap))
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass