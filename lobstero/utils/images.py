"""Everything to do with Lobstero's image generation."""

import sys

from PIL import Image, ImageDraw, ImageFont

root_directory = f"{sys.path[0]}/LobsteroBOT/".replace("\\", "/")


def make_meme(top_string: str, bottom_string: str, filename: str) -> None:
    """Makes a meme """

    img = Image.open(filename).convert("RGBA")
    image_size = img.size

    # find biggest font size that works
    font_size = int(image_size[1]/5)
    font = ImageFont.truetype(root_directory + "/data/fonts/impact.ttf", font_size)
    top_text_size = font.getsize(top_string)
    bottom_text_size = font.getsize(bottom_string)

    while top_text_size[0] > image_size[0]-20 or bottom_text_size[0] > image_size[0]-20:
        font_size -= 1
        font = ImageFont.truetype(root_directory + "/data/fonts/impact.ttf", font_size)
        top_text_size = font.getsize(top_string)
        bottom_text_size = font.getsize(bottom_string)

    # where it do what it go
    top_text_position_x = (image_size[0]/2) - (top_text_size[0]/2)
    top_text_position_y = 0
    top_text_position = (top_text_position_x, top_text_position_y)

    # what it go where it do
    bottom_text_position_x = (image_size[0]/2) - (bottom_text_size[0]/2)
    bottom_text_position_y = image_size[1] - bottom_text_size[1]
    bottom_text_position = (bottom_text_position_x, bottom_text_position_y)

    draw = ImageDraw.Draw(img)

    # do a bad job drawing outlines
    outline_range = int(font_size/15)
    for x in range(-outline_range, outline_range+1):
        for y in range(-outline_range, outline_range+1):
            draw.text(
                (top_text_position[0]+x, top_text_position[1]+y),
                top_string, (0, 0, 0), font=font)
            draw.text(
                (bottom_text_position[0]+x, bottom_text_position[1]+y),
                bottom_string, (0, 0, 0), font=font)

    draw.text(top_text_position, top_string, (255, 255, 255), font=font)
    draw.text(bottom_text_position, bottom_string, (255, 255, 255), font=font)

    img.save(root_directory + "image_downloads/comedy.png")
