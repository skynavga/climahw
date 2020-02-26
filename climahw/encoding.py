import numpy as np 

MAX_WIND_SPEED = 25.
""" Max wind speed that we encode (m/s) """

def encode_to_scaled_byte(raw, max_value):
    """
    Scale a real value so it fits in a byte

    Scales a value between -max_value and max_value to fit in an unsigned int between 1 and 255
    0 is reserved to represent N/A values 
    Values outside of the max_value range are clipped
    """
    return np.around(127*np.maximum(np.minimum(raw/max_value, 1), -1) + 128)

def decode_from_scaled_byte(byte, max_value):
    """
    Get the real value represented by a scaled byte (see encode_to_scaled_byte)
    """
    return max_value*(byte - 128.)/127.

def encode_wind(raw):
    """ Take a real wind component value and turn it into a byte """
    return encode_to_scaled_byte(raw, MAX_WIND_SPEED)

def decode_wind(byte):
    """ Take a wind component value represented as a byte and get the real value """
    return decode_from_scaled_byte(byte, MAX_WIND_SPEED)
