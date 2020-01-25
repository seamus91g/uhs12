import os
import secrets
from PIL import Image
from uhs12app import app


def save_picture(form_picture, sub_dir="wos_pics", output_size=(512, 512)):
    """
    Save a picture to the file system. 
    Assign random name in case users upload two pics with same name. 
    Picture will be resized to specified dimensions before being saved. 
    """
    # Keep the extension but randomise the name
    rand_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = rand_hex + f_ext
    # Save the desired sub directory in the static folder
    pic_path = os.path.join(app.root_path, 'static', sub_dir, picture_fn)
    # Scale the image according to parameters given by output_size
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(pic_path)
    # Return the new name for the picture
    return picture_fn

