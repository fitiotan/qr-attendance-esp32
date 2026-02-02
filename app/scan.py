import datetime

import cv2
import numpy as np
from fastapi import UploadFile
from sqlalchemy.orm import Session

from .models import QRCode, Attendance

def process_scan(file: UploadFile, db: Session):
    data = np.frombuffer(file.file.read(), np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)

    detector = cv2.QRCodeDetector()
    qr_data, _, _ = detector.detectAndDecode(img)

    if not qr_data:
        return "REJECTED", "QR invalid"

    emp_id, token = qr_data.split("|")
    qr = db.query(QRCode).filter_by(token=token).first()

    if not qr:
        return "REJECTED", "QR not found"

    if qr.used:
        return "REJECTED", "QR already used"

    if datetime.datetime.utcnow() > qr.expires_at:
        return "REJECTED", "QR expired"

    qr.used = True
    db.add(Attendance(employee_id=emp_id, status="OK", reason=""))
    db.commit()

    return "OK", "Attendance recorded"