def trng3_cap(values, window):
    global thread_cap
    sample_value = int(values["ac_bit_count"])
    interval_value = int(values["ac_time_count"])
    blocksize = int(sample_value / 8)
    #ports = dict()
    ports_avaiable = list(list_ports.comports())
    rng_com_port = None
    for temp in ports_avaiable:
        if temp[1].startswith("TrueRNG"):
            if rng_com_port == None:  # always chooses the 1st TrueRNG found
                rng_com_port = str(temp[0])
    file_name = time.strftime(f"%Y%m%d-%H%M%S_trng_s{sample_value}_i{interval_value}")
    file_name = f"1-SavedFiles/{file_name}"
    while thread_cap:
        start_cap = time.time()
        with open(file_name + '.bin', "ab") as bin_file:  # save binary file
            try:
                ser = serial.Serial(port=rng_com_port, timeout=10)  # timeout set at 10 seconds in case the read fails
                if (ser.isOpen() == False):
                    ser.open()
                ser.setDTR(True)
                ser.flushInput()
            except Exception:
                rm.popupmsg("Warning!", f"Port Not Usable! Do you have permissions set to read {rng_com_port}?")
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                break
            try:
                x = ser.read(blocksize)  # read bytes from serial port
            except Exception:
                rm.popupmsg("Warning!", "Read failed!")
                thread_cap = False
                window['ac_button'].update("Start")
                window["stat_ac"].update("        Idle", text_color="orange")
                break
            # if bin_file != 0:
            bin_file.write(x)
            ser.close()
            # if bin_file != 0:
            #     bin_file.close()
        bin_hex = BitArray(x)  # bin to hex
        bin_ascii = bin_hex.bin  # hex to ASCII
        num_ones_array = bin_ascii.count('1')  # count numbers of ones in the string
        with open(file_name + '.csv', "a+") as write_file:  # open file and append time and number of ones
            write_file.write(f'{strftime("%H:%M:%S", localtime())} {num_ones_array}\n')
        end_cap = time.time()
        # print(1 - (end_cap - start_cap))
        try:
            time.sleep(interval_value - (end_cap - start_cap))
        except Exception:
            pass