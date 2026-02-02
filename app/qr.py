import datetime
import uuid

import qrcode
from sqlalchemy.orm import Session

from .models import QRCode

def generate_qr(client_id: int, db: Session):
    token = str(uuid.uuid4())
    expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)

    qr_entry = QRCode(
        employee_id=client_id,
        token=token,
        expires_at=expires
    )
    db.add(qr_entry)
    db.commit()

    qr_data = f"{client_id}|{token}"
    img = qrcode.make(qr_data)

    img_path = f"qr_{client_id}_{token[:8]}.png"
    img.save(img_path)

    return img_path