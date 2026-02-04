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

    if datetime.datetime.now() > qr.expires_at:
        return "REJECTED", "QR expired"

    qr.used = True
    
    # Check if this is a check-out (looking for existing check-in today without check-out)
    today = datetime.date.today()
    existing_checkin = db.query(Attendance).filter(
        Attendance.employee_id == int(emp_id),
        Attendance.check_in >= datetime.datetime.combine(today, datetime.time.min),
        Attendance.check_in < datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time.min),
        Attendance.check_out == None
    ).first()
    
    # Get username for confirmation
    from .models import User
    user = db.query(User).filter(User.id == int(emp_id)).first()
    username = user.username if user else f"ID:{emp_id}"
    
    if existing_checkin:
        # Check-out: update existing record
        existing_checkin.check_out = datetime.datetime.now()
        existing_checkin.status = "checked_out"
        db.add(existing_checkin)
        db.commit()
        return "OK", f"✓ {username} - Checked out at {datetime.datetime.now().strftime('%H:%M:%S')}"
    else:
        # Check-in: create new record
        attendance = Attendance(
            employee_id=emp_id, 
            status="present", 
            reason="ESP32 Scan",
            check_in=datetime.datetime.now()
        )
        db.add(attendance)
        db.commit()
        return "OK", f"✓ {username} - Checked in at {datetime.datetime.now().strftime('%H:%M:%S')}"