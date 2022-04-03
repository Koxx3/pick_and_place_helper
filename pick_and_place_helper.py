#!/usr/bin/env python3
# coding=utf-8

import csv
import codecs
import os
import re
import sys

from PIL import Image

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages


designator_filter = ".*"

# image cropper
def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


# parse arguments
if len(sys.argv) == 3:
    pcb_svg_file = sys.argv[1]
    pick_csv_file = sys.argv[2]
elif len(sys.argv) == 4:
    pcb_svg_file = sys.argv[1]
    pick_csv_file = sys.argv[2]
    designator_filter = sys.argv[3]
else:
    print("ERR: project name missing!")
    exit()	


output_fn = pcb_svg_file + "_cairo.png"


### convert SVG to PNG for mathplot import 

dir_path = os.path.dirname(os.path.realpath(__file__))
os.environ['path'] += r';' + dir_path + '\libs'
os.environ['path'] += r';C:\\Program Files\\UniConvertor-2.0rc5\\dlls'

# import cairo only after path is complete
import cairosvg
cairosvg.svg2png(url=pcb_svg_file, write_to=output_fn, scale=5.0)



### crop image borders

im = Image.open(output_fn)

new_im_width = im.width - 90
new_im_height = im.height - 90

im_new = crop_center(im, new_im_width, new_im_height)
im_new.save(pcb_svg_file + ".png", quality=80)

print("image resolution : " + str(new_im_width) + " / " + str(new_im_height))


### prepare plotter

mpl.rcParams['figure.dpi'] = 200

img = plt.imread(pcb_svg_file + ".png")
fig, ax = plt.subplots()
ax.imshow(img, extent=[0, new_im_width * 2, 0, new_im_height * 2])


### open PDF
pp = PdfPages(pcb_svg_file + '.pdf')


### parse CSV

f=codecs.open(pick_csv_file,"rb","utf-16")
csvread=csv.DictReader(f,delimiter='\t')

result = sorted(csvread, key=lambda d: (d['Footprint'], d['Comment'], float(d['Mid X'].split("mm")[0])))

#print(result)

lastComment = ""
lastFootprint = ""
lastDesignator = ""
i_compo = 1

filelist = []

for row in result:
    
    if row['Comment'] != lastComment :
        
        if lastComment != "" :
            plt.text(0, new_im_height + 20, "Footprint = " + lastFootprint[0:15] + " / Value = " + lastComment[0:15] + " / Nb = " + str(i_compo - 1), color='darkred', weight='bold', fontsize='x-small')

            filename = pcb_svg_file + "-" + "".join(x for x in lastComment if x.isalnum())
            filename_svg = filename +  '.svg'
            filename_png = filename +  '.png'

#            plt.savefig(filename_svg, transparent=True)

            if designator_filter == "" :
                print("save")
                pp.savefig(fig)
            elif re.match(designator_filter, lastDesignator) :
                pp.savefig(fig)
                print("save")


#            cairosvg.svg2png(url=filename_svg, write_to=filename_png, scale=5.0)
#            filelist.append(filename_png)

        #plt.show()
        plt.close()         
        
        fig, ax = plt.subplots()
        img = plt.imread(pcb_svg_file + ".png")
        ax.imshow(img, extent=[0, new_im_width, 0, new_im_height], alpha=0.5)

        i_compo = 1
        lastComment = row['Comment']
        lastFootprint = row['Footprint']
        lastDesignator = row['Designator']
       
        print("" + lastDesignator + " / " + lastComment + " / " + lastFootprint)

    # get position        
    x_str = row['Mid X'].split("mm")[0]
    y_str = row['Mid Y'].split("mm")[0]
    x = float(x_str) * 19
    y = float(y_str) * 19

    y = new_im_height + y

    # hide axis
    plt.axis('off')
    ax = plt.gca()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    # display marker
    plt.scatter(x, y, color='darkred', alpha=0.5)
    plt.scatter(x, y, s=1000, facecolors='none', edgecolors='darkred')

    # display marker text
    plt.text(x - 10, y + 8, i_compo, color='darkred', weight='bold', verticalalignment='bottom', horizontalalignment='right')

    i_compo = i_compo + 1


# close PDF
pp.close()
