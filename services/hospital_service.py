# services/hospital_service.py

from database.db import blood_stock

def get_stock():
    return blood_stock


def can_fulfill_request(bg, units, stock):
    return stock.get(bg, 0) >= units


def is_critical(bg, units):
    stock = get_stock()
    return not can_fulfill_request(bg, units, stock)
