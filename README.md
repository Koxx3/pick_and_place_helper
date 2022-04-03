This tool is to help electronic DIYers to place electronic components on the PCB (aka Pick & place).

Tested only on Windows.
Tested only with EasyEDA exports (SVG and pick&place CSV).

# Installation

It requires Python 3.

Install python libraries :
```
pip install -r requirements.txt
```

You must also install [Uniconverter](requires_install\uniconvertor-2.0rc5-win64_headless.msi)

# EasyEDA Requirements

You must center your design in the lower right corner of the PCB diagram.

![image](easyeda_requirements.PNG)

# Usage

## In EasyEDA

Export SVG :

![image](https://user-images.githubusercontent.com/11454444/161438143-bd530f32-b682-42bb-b1e7-e23d3950a69d.png)

I advise those settings :

![image](https://user-images.githubusercontent.com/11454444/161438158-d4c78f8e-e473-462c-8875-ffcdbf9ca1c1.png)

## Shell command
```
python pick_and_place_helper.py <path_to_svg_pcb_file>.svg <path_to_pick_and_place_file>.csv
```
 
You can also filter desingations with a regular expression :
```
python pick_and_place_helper.py <path_to_svg_pcb_file>.svg <path_to_pick_and_place_file>.csv "^[R|C]d+$"
```

It will output only components with designation starting with R (resistors) and C (capacitors).


# Results

It outputs a PDF next to your SVG file.
Each page is for a specific component (same footprint, same type, same value).

You your printer options, you can adjust multiple pages on a A4 pages if you want.

Check example folder.

Example :
![image](https://user-images.githubusercontent.com/11454444/161437782-1039b5b7-5b72-41a5-b965-9d52ad39bddf.png)
