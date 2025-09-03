# RngKit 3.0
by Thiago Jung  
https://github.com/Thiagojm/RngKitPSG  
thiagojm1984@hotmail.com   
Written in Python 3.13
---

## Important note
**From version 3.0 onwards we adopted a new datetime and file naming format, so analyses made with previously collected files will not work. For those, use the 2.x versions.**

### What changed in 3.x
- Direct BitBabbler support via Python (no seedd.exe daemon needed)
- File names for BitBabbler now include the fold setting (e.g., `_f0`..`_f4`)
- Data Analysis auto-detects sample size and interval from the file name


## Abstract

This application uses two types of TRNGs — True Random Number Generators (TrueRNG and BitBabbler) — and a Pseudo RNG (based on Python’s `secrets` module)
for data collection and statistical analysis for several purposes, including mind–matter interaction research.  
It collects random data in user-defined sample sizes and intervals and counts the number of ‘1’ bits per sample.
Afterwards, the data can be analyzed against the expected value (50%) and visualized as a cumulative Z‑Score.


## Supported hardware

1- TrueRNG and TrueRNGPro (https://ubld.it/);  
2- BitBabbler Black and White (http://www.bitbabbler.org/what.html);  
3- No Hardware: Pseudo RNG (using Python `secrets` module — not truly random).

## Installation

1- Hardware Installation (Windows):
    The default installation path is: "C:\Users\Username\RngKit" - Where Username is the name of the windows current user.  
    1.1- TrueRNG and TrueRNGPro:  
         Choose from the 2-Installation folder (inside the "C:\Users\Username\RngKit") the TrueRng folder, the folder for your device (TrueRng3 or TrueRngPro)
         Within this folder, right-click the TrueRNG.inf or TrueRNGpro.inf file and select Install. Follow the instructions for installation.  
    1.2- BitBabbler:  
         Inside the 2-Installation\BitBabbler folder (inside the "C:\Users\Username\RngKit"), run vcredist_x64.exe and follow the installation guidelines.
         Insert your BitBabbler device into a USB port and run the zadig-2.8.exe file. Select your device and click "Install Driver".
         Wait for the process to finish and close the program.
2- Python dependencies:
    Use the provided requirements file: `pip install -r requirements_streamlit.txt`

## Usage

Run the app:

```bash
streamlit run main_streamlit.py
```

The program has 3 tabs:

- ## Tab 1 — Data Collection & Analysis
>### Collecting:  
>>To collect data, select the device to use, or multiple devices and click "Start". You can set the sample size (in bits) and the sample interval (in seconds). 
BitBabbler supports folds 0–4 (0 = RAW; 1–4 = XOR folding). TrueRNG has no fold option.
PseudoRNG uses the Python `secrets` module that gathers entropy from your system; it is not a good source of true randomness, but you can use it if you don’t have a hardware RNG. 
Hit "Stop" when you wish to stop the process. Two files are going to be created inside the `data/raw/` folder by default (override with env `RNGKIT_DATA_DIR`). One with .bin extension and another with .csv.
The .bin is in binary form and is used as a controller. The .csv contains more info, like the time of each collected series and the count of 'ones' that appeared in each series. Usually it will be better to analyse the .csv file.   

>### Analysing:  
>>To analyse the file and generate an Excel file with Z‑score and a graph, select a previously generated .bin or .csv file with the "Browse" button.
The app now auto‑detects the interval and the sample size from the filename.
Clicking "Generate" will automatically generate a file with the same name as the one selected, but with extension .xlsx, with the analyzed data.
This data and chart represent the cumulative Z‑score of 'ones' that appeared in the samples.
This file will be saved in the `data/raw/` folder. You can click "Open Output Folder" to open Windows Explorer at the file location.  

>### Concatenate:  
>>If you want to concatenate CSV files, browse the files in "Concatenate Multiple CSV Files". It will create a new concatenated file. It’s important to concatenate only files with the same interval and sample size, or you will get wrong results. Select the proper Sample Size and Interval before concatenating from the inputs above.

- ## Tab 2 — Live Plot  
>Select the device to use (BitBabbler folds 0–4 supported).
Click on "Start", the chart will update and at the same time two files will be generated and saved to `data/raw/` (.bin and .csv).
When you finish capturing it is important to click "Stop".

- ## Tab 3 — Instructions

## File naming convention
The file name contains important information about the collected data.
The format is: `YYYYMMDDTHHMMSS_{device}_s{bits}_i{interval}[_f{folds}]`
Where `device` ∈ {`trng`, `bitb`, `pseudo`}. The `_f{folds}` suffix only appears for BitBabbler captures (f0 = RAW, f1–f4 = XOR folding levels).

For example "20201011T142208_bitb_s2048_i1_f0": Collected on October 11, 2020 (20201011), at 14:22:08 (142208), BitBabbler device (bitb), sample of 2048 bits (s2048) every 1 second (i1), RAW mode (f0).

## License

MIT License

Copyright (c) 2025 Thiago Jung Mendaçolli




