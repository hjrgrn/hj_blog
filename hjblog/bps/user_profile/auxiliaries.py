from io import BytesIO
import logging
import os
from flask import abort, current_app, url_for
import qrcode
from base64 import b64encode
import werkzeug
import secrets


def get_b64encoded_qr_image(data: str) -> str:
    """
    `data` is a string representing the content to be embedded within
    the QR code, the function initializes a `QRCode` object using
    the `qrcode` library. It adds the provided data to this `QRcode`
    instance and generates the QR code. The code then converts
    this `QRcode` into an image representation.
    The `BytesIO` object stores this image in memory. The function proceeds
    to encode the content of this in-memory buffer, representing the QR code image
    into Base64 format. Finally, it returns this Base64-encoded string,
    encapsulating the QR code image, ready for transmission or display
    in various applications.
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered)
    return b64encode(buffered.getvalue()).decode("utf-8")


def save_picture(
    current_pic_name: str | None,
    picture: werkzeug.datastructures.file_storage.FileStorage,
) -> str:
    """
    Saves the picture on the filesystem, returns the name to the picture,
    if the procedure wasn't successfull 500 will be sent to the client, but this should
    not happen if the validation has been done correctly.
    The old picture of the user will be deleted.
    This function expects the picture to be validated elsewhere, in the relative
    `FlaskForm` probabily.
    """
    new_name = secrets.token_hex(8)
    pic_name = picture.filename
    index = pic_name.rfind(".")
    if index < 0:
        # this should not happen given the limitations on the form
        abort(500)
    suffix = pic_name[index:]
    new_name = new_name + suffix
    pic_path = os.path.join(current_app.root_path, "static/profile_pics", new_name)
    picture.save(pic_path)
    if current_pic_name is not None:
        try:
            os.remove(
                os.path.join(
                    current_app.root_path, "static/profile_pics", current_pic_name
                )
            )
        except FileNotFoundError as e:
            logging.exception(e)
        except Exception as e:
            logging.exception(e)
    return new_name


def get_profile_pic(pic_name: str | None) -> str:
    """
    Obtains the path to the profile picture or the default
    picture if a picture is not available.
    """
    if pic_name is None:
        # TODO: make default picture configurable server side
        return url_for("static", filename="default_files/anonymous_user.png")
    return url_for("static", filename="profile_pics/" + pic_name)
