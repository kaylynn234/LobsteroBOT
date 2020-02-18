# The code below is not mine, however it has been modified a fair bit to work with Lobstero.
# The screams of PEP8 shall be silent.

from PIL import Image, ImageDraw, ImageFont
from colour import Color
import numpy as np

# The function convert an image to ascii art
# f: Input filename
# SC: the horizontal pixel sampling rate. It should be between 0(exclusive) and 1(inclusive). The larger the number, the more details in the output. 
#   If you want the ascii art output be the same size as input, use ~ 1/ font size width. 
# GCF: >0. It's an image tuning factor. If GCF>1, the image will look brighter; if 0<GCF<1, the image will look darker.
# out_f: output filename
# color1, color2, bgcolor: follow W3C color naming https://www.w3.org/TR/css3-color/#svg-color
#
# Copyright 2017, Shanshan Wang, MIT license


def asciiart(img, SC, GCF, out_f, color1='black', color2='blue', bgcolor='white'):

    # The array of ascii symbols from white to black
    chars = np.asarray(list(' .,:irs?@9B&#'))

    # Load the fonts and then get the the height and width of a typical symbol
    # You can use different fonts here
    font = ImageFont.load_default()
    letter_width = font.getsize("x")[0]
    letter_height = font.getsize("x")[1]

    WCF = letter_height/letter_width

    # Based on the desired output image size, calculate how many ascii letters are needed on the width and height
    widthByLetter = round(img.size[0] * SC * WCF)
    heightByLetter = round(img.size[1]*SC)
    S = (widthByLetter, heightByLetter)

    # Resize the image based on the symbol width and height
    img = img.resize(S)

    # Get the RGB color values of each sampled pixel point and convert them to graycolor using the average method.
    # Refer to https://www.johndcook.com/blog/2009/08/24/algorithms-convert-color-grayscale/ to know about the algorithm
    img = np.sum(np.asarray(img), axis=2)

    # Normalize the results, enhance and reduce the brightness contrast.
    # Map grayscale values to bins of symbols
    img -= img.min()
    img = (1.0 - img / img.max()) ** GCF * (chars.size - 1)

    # Generate the ascii art symbols 
    lines = ("\n".join(("".join(r) for r in chars[img.astype(int)]))).split("\n")

    # Create gradient color bins
    nbins = len(lines)
    colorRange = list(Color(color1).range_to(Color(color2), nbins))

    # Create an image object, set its width and height
    newImg_width = letter_width * widthByLetter
    newImg_height = letter_height * heightByLetter
    newImg = Image.new("RGBA", (newImg_width, newImg_height), bgcolor)
    draw = ImageDraw.Draw(newImg)

    # Print symbols to image
    leftpadding = 0
    y = 0
    lineIdx = 0
    for line in lines:
        color = colorRange[lineIdx]
        lineIdx += 1

        draw.text((leftpadding, y), line, color.hex, font=font)
        y += letter_height

    return newImg
