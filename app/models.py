import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey

from .database import Base

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class QRCode(Base):
    __tablename__ = "qr_codes"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    token = Column(String, unique=True)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer)
    scan_time = Column(DateTime, default=datetime.datetime.now)
    status = Column(String)
    reason = Column(String)
    check_in = Column(DateTime)
    check_out = Column(DateTime)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="client")  # "client" or "admin"