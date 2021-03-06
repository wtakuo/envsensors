# EnvSensors: A Python Library for I2C Environmental Sensors
# Copyright (C) 2016, Takuo Watanabe

# The sign extension functions are adapted from:
# Henry S. Warren, Jr., "Hacker's Delight (2nd ed)", Addison-Wesley, 2012.


def sb(x):
    """Sign extension of a byte value. Assuming 0 <= x < 0x100"""
    return (x ^ 0x80) - 0x80


def ss(x):
    """Sign extension of a short value. Assuming 0 <= x < 0x10000"""
    return (x ^ 0x8000) - 0x8000

def s24(x):
    """Sign extension of a 24bit value. Assuming 0 <= x < 0x1000000"""
    return (x ^ 0x800000) - 0x800000


def b2us(x, y):
    """Compose an unsigned short value from two bytes"""
    return (x << 8) | y


def b2ss(x, y):
    """Compose a signed short value from two bytes"""
    return ss((x << 8) | y)

def b2s24(x, y, z):
    """Compose a signed 24bit value from three bytes"""
    return s24((x << 16) | (y << 8) | z)