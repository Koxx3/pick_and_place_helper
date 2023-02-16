#!/usr/bin/env python3
# coding=utf-8

import csv
import codecs
import os
import re
import sys

from PIL import Image, ImageOps

import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages
import argcomplete
import argparse


designator_filter = ".*"
designator_print = False


def set_dll_search_path():
    # Python 3.8 no longer searches for DLLs in PATH, so we have to add
    # everything in PATH manually. Note that unlike PATH add_dll_directory
    # has no defined order, so if there are two cairo DLLs in PATH we
    # might get a random one.
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return
    for p in os.environ.get("PATH", "").split(os.pathsep):
        try:
            os.add_dll_directory(p)
        except OSError:
            pass


set_dll_search_path()


# Read parser arguments
parser = argparse.ArgumentParser(description='Test passing arguments')
parser.add_argument('-s', metavar='<input svg>', nargs=1,
                    help="Input file SVG", required=True)
parser.add_argument('-c', metavar='<input csv positions>',
                    nargs=1, help="Input file positions CSV", required=True)
parser.add_argument(
    '-x', metavar='<input format [easyeda|kicad_jlcpcb|kicad_original]>', nargs=1, help="Input format", required=True)
parser.add_argument('-f', metavar='<filter>',
                    nargs=1, help="Designator filter")
parser.add_argument('-ox', metavar='<offsetx>', nargs=1, help="Offset X")
parser.add_argument('-oy', metavar='<offsety>', nargs=1, help="Offset Y")
parser.add_argument(
    '-r', metavar='<ref [True|False]>', nargs=1, help="Print component designator")

argcomplete.autocomplete(parser)
args = parser.parse_args()

pcb_svg_file = args.s[0]
pick_csv_file = args.c[0]
pick_csv_format = args.x[0]
if (args.f):
    designator_filter = args.f[0]
if (args.r):
    designator_print = args.r[0]

output_fn = pcb_svg_file + "_cairo.png"
dpi = 200
size_factor = 18.9

# parse CSV
if (pick_csv_format == "easyeda"):
    f = codecs.open(pick_csv_file, "rb", "utf-16")
    csvread = csv.DictReader(f, delimiter="\t")
    print("UTF16 fields ", csvread.fieldnames)
    field_package = 'Footprint'
    field_value = 'Comment'
    field_designator = 'Designator'
    field_layer = "Layer"
    field_pos_x = 'Mid X'
    field_pos_y = 'Mid Y'
elif (pick_csv_format == "kicad_jlcpcb") or (pick_csv_format == "kicad_original"):
    f = codecs.open(pick_csv_file, "rb", "utf-8")
    csvread = csv.DictReader(f)
    print("UTF8 fields ", csvread.fieldnames)
    if (pick_csv_format == "kicad_jlcpcb"):
        field_package = 'Package'
        field_value = 'Val'
        field_designator = 'Designator'
        field_layer = "Layer"
        field_pos_x = 'Mid X'
        field_pos_y = 'Mid Y'
    elif (pick_csv_format == "kicad_original"):
        field_package = 'Package'
        field_value = 'Val'
        field_designator = 'Ref'
        field_layer = "Side"
        field_pos_x = 'PosX'
        field_pos_y = 'PosY'


# Load offsets
if (args.ox):
    offset_x = float(args.ox[0])
else:
    offset_x = 0
if (args.oy):
    offset_y = float(args.oy[0])
else:
    offset_y = 0


# convert SVG to PNG for mathplot import

# dir_path = os.path.dirname(os.path.realpath(__file__))
# os.environ['path'] += r';' + dir_path + '\libs'
# os.environ['path'] += r';' + dir_path
os.environ['path'] += r';C:/Program Files/UniConvertor-2.0rc5/dlls'
set_dll_search_path()

import cairosvg

# import cairo only after path is complete
cairosvg.svg2png(url=pcb_svg_file, write_to=output_fn, scale=5.0)


# crop image borders
image = Image.open(output_fn)
image.load()

print("image resolution original : " +
      str(image.width) + " / " + str(image.height))

image_data = np.asarray(image)
image_data_bw = image_data.max(axis=2)
if (pick_csv_format == "easyeda"):
    non_empty_columns = np.where(image_data_bw.min(axis=0) < 250)[0]
    non_empty_rows = np.where(image_data_bw.min(axis=1) < 250)[0]
elif (pick_csv_format == "kicad_jlcpcb") or (pick_csv_format == "kicad_original"):
    non_empty_columns = np.where(image_data_bw.max(axis=0) > 0)[0]
    non_empty_rows = np.where(image_data_bw.max(axis=1) > 0)[0]

cropBox = (min(non_empty_rows), max(non_empty_rows),
           min(non_empty_columns), max(non_empty_columns))

image_data_new = image_data[cropBox[0]                            :cropBox[1]+1, cropBox[2]:cropBox[3]+1, :]

new_image = Image.fromarray(image_data_new)
new_image.save(pcb_svg_file + ".png", quality=80)

new_im_width = new_image.width
new_im_height = new_image.height

print("image resolution new : " + str(new_im_width) + " / " + str(new_im_height))


# prepare plotter

mpl.rcParams['figure.dpi'] = dpi

img = plt.imread(pcb_svg_file + ".png")
fig, ax = plt.subplots()
ax.imshow(img, extent=[0, new_im_width, 0, new_im_height], alpha=0.5)


# open PDF
pp = PdfPages(pcb_svg_file + '.pdf')

result = sorted(csvread, key=lambda d: (
    d[field_package], d[field_value], float(d[field_pos_x].split("mm")[0])))


# for row in result:
i_compo = 1
compo_list = []
nbPages = 0

for i, row in enumerate(result):

    print("[" + str(i + 1) + "/" + str(len(result)) + "] " +
          row[field_designator] + " / " + row[field_value] + " / " + row[field_package])

    # get position
    x_str = row[field_pos_x].split("mm")[0]
    y_str = row[field_pos_y].split("mm")[0]

    x = (float(x_str) - float(offset_x)) * size_factor
    y = (float(y_str) + float(offset_y)) * size_factor

    # print("position : x = ", x, "y =", y, "new_im_height = ", new_im_height)

    y = new_im_height + y

    # hide axis
    plt.axis('off')
    ax = plt.gca()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    # display marker
    if (row[field_layer] == "top" or row[field_layer] == "T"):
        item_color = 'darkred'
        item_line_style = '-'
    elif (row[field_layer] == "bottom" or row[field_layer] == "B"):
        item_color = 'darkblue'
        item_line_style = '--'
        # if (pick_csv_format == "kicad_original"):
        #    x = -x

    plt.scatter(x, y, color=item_color, alpha=0.5)
    plt.scatter(x, y, s=1000, facecolors='none',
                edgecolors=item_color, linestyle=item_line_style)

    # display marker text
    plt.text(x - 10, y + 8, i_compo, color=item_color, weight='bold',
             verticalalignment='bottom', horizontalalignment='right')

    if designator_print:
        plt.text(x + 15, y + 8, row[field_designator][0:3], color=item_color,
                 weight='bold', verticalalignment='bottom', horizontalalignment='left')

    compo_list.append(row[field_designator])

    i_compo = i_compo + 1

    if ((i < len(result) - 1) and (result[i][field_value] != result[i+1][field_value])) or (i + 1 == len(result)):

        plt.text(0, new_im_height + 50, "Footprint = " + row[field_package][0:15] + " / Value = " + row[field_value]
                 [0:15] + " / Nb = " + str(i_compo - 1), color='darkred', weight='bold', fontsize='x-small')
        plt.text(0, new_im_height + 10, "List = " + ', '.join(compo_list),
                 color='darkred', weight='bold', fontsize='x-small')

        print("compo list", ', '.join(compo_list))

        filename = pcb_svg_file + "-" + \
            "".join(x for x in row[field_value] if x.isalnum())
        filename_svg = filename + '.svg'
        filename_png = filename + '.png'

        print("  >> " + row[field_value] + " / " + row[field_package])

        if designator_filter == "" or re.match(designator_filter, row[field_designator]):
            print("    >> save")
            nbPages = nbPages + 1 
            pp.savefig(fig, bbox_inches='tight', pad_inches=0)

        #plt.savefig(filename_svg, transparent=True)
        #cairosvg.svg2png(url=filename_svg, write_to=filename_png, scale=5.0)

        # plt.show()

        plt.close()

        fig, ax = plt.subplots()
        img = plt.imread(pcb_svg_file + ".png")
        ax.imshow(img, extent=[0, new_im_width, 0, new_im_height], alpha=0.5)

        i_compo = 1
        compo_list = []

print("=====================================")
print("number of pages : ", nbPages)
print("=====================================")

# close PDF
pp.close()
