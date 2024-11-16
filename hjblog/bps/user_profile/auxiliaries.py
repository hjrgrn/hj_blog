from io import BytesIO
import qrcode
from base64 import b64encode

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
    img = qr.make_image(fill_color='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered)
    return b64encode(buffered.getvalue()).decode("utf-8")

