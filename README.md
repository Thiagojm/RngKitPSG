# RngKit 2.0
by Thiago Jung  
https://github.com/Thiagojm/RngKitPSG  
thiagojm1984@hotmail.com  
Written in Python 3.7.9
-----------------------

# ABSTRACT

This project represents my puttering around with hardware entropy sources and
random number generation in Windows, to help to our project of mind matter interaction.

Kit for working with TRNGs (True Random Number Generators), creating Z-score tables, acquiring data and LivePlot!

# Supported Hardware:

1- TrueRNG and TrueRNGPro (https://ubld.it/);  
2- Bitbabbler Black and White (http://www.bitbabbler.org/what.html).

# Installation

1- Hardware Installation:  
    The default installation path is: "C:\Users\Username\RngKit" - Where Username is the name of the windows current user.  
    1.1- TrueRNG e TrueRNGPro:  
         Choose from the Installation folder the TrueRng folder, the folder for your device (TrueRng3 or TrueRngPro)
         Within this folder, right-click the TrueRNG.inf or TrueRNGpro.inf file and select Install. Follow the instructions for installation.  
    1.2- Bitbabbler:  
         Inside the Installation\BitBabbler folder, run vcredist_x64.exe (source: http://www.microsoft.com/en-us/download/details.aspx?id=30679) and follow the installation guidelines.
         Insert your bitbabbler device into a USB port and run the zadig-2.4.exe file (source: http://zadig.akeo.ie/). Select your device and click "Install WCDI Driver".
         Wait for the process to finish and close the program.

# Usage

1- Start the program;  
2- The program has 3 tabs:
- TAB 1: The first tab is for analysis and collecting data:
> Collecting:  
To collect data, select the device to use, or multiple devices. BitBabbler has different capturing options, with option 0 being in RAW, options between 1 and 4 in XOR, TrueRNG only works in XOR mode, then just click "Start".
Hit "Stop" when you wish to stop the process. Two files are going to be created inside the "1-SavedFiles" folder. One with .bin extension and another with .csv.
The .bin is in binary form and is used as a controller. The .csv contains more info, like the time of each collected series, usually will be better to analyse the .csv file.  
> Analysing:  
To analyse the file and generate a Excel file with z-score and a graph, select a previously generated .bin or .csv file whit the "Browse" button.
Clicking "Generate" will automatically generate a file with the same name as the one selected, but with extension .xlsx, with the analyzed data.
This file will be saved in the "1-SavedFiles" folder. You can click "Open Output Folder" to go there.

- TAB 2: The second tab is for collecting and presenting a live Zscore x Time chart.
Select the device to use (BitBabbler can be set to 0 (RAW) or 1 (XOR)).
Click on "Start", the chart will update and at the same time two files will be generated and saved(.bin and .csv).
When you finish capturing it is important to click "Stop".

- TAB 3: Instructions Tab

# License

MIT License  
  
Copyright (c) 2020 Thiago Jung Mendaçolli
