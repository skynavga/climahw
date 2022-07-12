"""
ClimaCell Homework

Convert u- and v- wind velocity component data represented by 8-bit gray-scale
(as PNG images) to a scalar field then output as an (optionally rescaled)
8-bit gray-scale PNG file grid fitted to a user specified area of interest.

See README.md for further information.

Created on Feb 24, 2020 by
@author <glenn.adams@colorado.edu>
"""

# pylint: disable=consider-using-f-string
# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring

import sys
import os
import argparse
import warnings

from imageio import imread, imwrite
from numpy import around, asarray, maximum, minimum, sqrt
from pyresample.geometry import AreaDefinition
from pyresample.image import ImageContainerQuick

from climahw.encoding import decode_wind, MAX_WIND_SPEED

# defaults
DEFAULT_AREA_SOURCE = [500.0, 500.0]
DEFAULT_AREA_UNIT = "m"
DEFAULT_IMAGE_SCALE = 1.0
DEFAULT_PROJECTION = "+proj=utm +zone=13 +ellps=WGS84 +units=m"
DEFAULT_NUM_PROCS = os.cpu_count()

# other constants
DEGREES_TO_METERS = 500.0 / 0.005
VERSION = "climahw 1.0.1 03/11/2020"


def _parse_rescale(string):
    """Parse and verify rescale option value."""
    value = float(string)
    if value < 0 or value > 1:
        raise argparse.ArgumentTypeError("%r is not a valid scale factor" % value)
    return value


def _parse_units(value):
    """Parse and verify units option value."""
    if value not in ("m", "d"):
        raise argparse.ArgumentTypeError("%r is not a valid unit 'm' or 'd'" % value)
    return value


def _normalize_units(pa):
    """
    Normalize units to meters. If specified units are meters, then do
    nothing; otherwise, if degrees, then convert degrees to meters using
    fixed conversion ratio of 500 meters per 0.005 degrees. N.B. that this
    conversion ratio is only an approximation, and not particularly good:
    a more accurate conversion would be closer to 555 meters, and would
    vary by latitude, increasing from ~552 meters at the equator to ~558
    meters at the poles. Morever, this is for latitudinal components, and
    not longitudnal components, which vary from 556 meters at the equator
    to zero at the poles. For the purpose of this exercise, we make a
    gross simplification and effectively ignore this reality, assuming
    instead the ideally global and uniform conversion described above.

    Positional Parameters:

    pa      - parsed arguments (fom command line), a Namespace object

    Returns - parsed arguments with parsed argument state normalized to meters.
    """
    if pa.units == "d":
        if pa.sArea is not None:
            pa.sArea = [*map(lambda x: x * DEGREES_TO_METERS, pa.sArea)]
        if pa.tArea is not None:
            pa.tArea = [*map(lambda x: x * DEGREES_TO_METERS, pa.tArea)]
        if pa.tOffset is not None:
            pa.tOffset = [*map(lambda x: x * DEGREES_TO_METERS, pa.tOffset)]
        pa.units = "m"
    return pa


def _parse_nprocs(string):
    """Parse and verify nprocs option value."""
    value = int(string)
    if value < 1:
        raise argparse.ArgumentTypeError(
            "%r is not a valid number of processors, must be positive greater than 0"
            % value
        )
    if value > DEFAULT_NUM_PROCS:
        raise argparse.ArgumentTypeError(
            "%r is not a valid number of processors, must be less than cpu count %d"
            % (value, DEFAULT_NUM_PROCS)
        )
    return value


def _process_args(args):
    """
    Process command line arguments

    Positional Parameters:

    args    - command line arguments

    Returns - Namespace object containing parsed command line arguments
    """
    ap = argparse.ArgumentParser(prog="climahw.homework")
    # optional arguments (short and long form)
    ap.add_argument(
        "-o",
        "--tOffset",
        dest="tOffset",
        type=float,
        nargs=2,
        help="target area offset in specified units, as longitude and latitude offset",
    )
    ap.add_argument(
        "-p",
        "--projection",
        dest="projection",
        default=DEFAULT_PROJECTION,
        help="projection applied to source and target areas",
    )
    ap.add_argument(
        "-r",
        "--rescale",
        dest="rescale",
        type=_parse_rescale,
        default=DEFAULT_IMAGE_SCALE,
        help="(re)scale factor to apply to output image",
    )
    ap.add_argument(
        "-s",
        "--sArea",
        dest="sArea",
        type=float,
        nargs=2,
        default=DEFAULT_AREA_SOURCE,
        help="source area shape in specified units, as longitude and latitude dimensions",
    )
    ap.add_argument(
        "-t",
        "--tArea",
        dest="tArea",
        type=float,
        nargs=2,
        help="target area shape in specified units, as longitude and latitude dimensions",
    )
    ap.add_argument(
        "-u",
        "--units",
        dest="units",
        type=_parse_units,
        default=DEFAULT_AREA_UNIT,
        help="units applied to area shapes, either 'm' (meters) or 'd' (degrees)",
    )
    ap.add_argument("-v", "--version", action="version", version=VERSION)
    # optional arguments (long form only)
    ap.add_argument(
        "--nprocs",
        dest="nprocs",
        type=_parse_nprocs,
        default=DEFAULT_NUM_PROCS,
        help="number of processors to apply to resampling operations",
    )
    # positional arguments
    ap.add_argument(
        "uFile", help="u-component input file, an 8-bit PNG grayscale image"
    )
    ap.add_argument(
        "vFile", help="v-component input file, an 8-bit PNG grayscale image"
    )
    ap.add_argument(
        "oFile", help="wind speed magnitude output file, an 8-bit PNG grayscale image",
    )
    # parse arguments
    pa = ap.parse_args(args[1:])
    # post-processing
    pa.nprocs = min(pa.nprocs, DEFAULT_NUM_PROCS)
    if pa.units == "d":
        pa = _normalize_units(pa)
    if pa.tArea is None:
        pa.tArea = pa.sArea
        pa.tOffset = [0, 0]
    return pa


def _encode_magnitude_to_scaled_byte(magnitude, max_value):
    """
    Scale a real magnitude value so it fits in a byte

    Scales a value between 0 and max_value to fit in an unsigned int between 0 and 255
    Values outside of the max_value range are clipped
    """
    return around(255 * maximum(minimum(magnitude / max_value, 1), 0) + 0)


def _encode_wind_magnitude(magnitude):
    """ Take a real wind magnitude value and turn it into a byte """
    return _encode_magnitude_to_scaled_byte(magnitude, MAX_WIND_SPEED)


def _area_extent_from_user_area(area, offset):
    """ Compute area extent from area and offset. """
    w = around(area[0] / 2)
    h = around(area[1] / 2)
    if offset is None:
        dx = -w
        dy = h
    else:
        dx = offset[0]
        dy = offset[1]
    return [-w + dx, -h + dy, w + dx, h + dy]


def _compute_target_image_size(source_image_size, scale_factor):
    """ Compute new image size using scale factor. """
    if scale_factor == 1:
        return source_image_size
    return [*map(lambda x: x * scale_factor, source_image_size)]


def _resample(pa, wData):
    """
    Resample (grid fit) wind speed magnitude data, wData, a 2-D numpy
    float64 array, using specified projection, creating a new
    array with a user specified area of interest (extent) and optionally
    rescaled at a new pixel resolution. Resampling is performed using an
    approximate, but fast nearest neighbor method.

    Positional Parameters:

    pa      - parsed arguments (fom command line), a Namespace object
    wData   - wind speed magnitude data, a 2-D numpy float64 array

    Returns - a 2-D numpy float64 array representinting resampled wind data
                using user specified target area of interest optionally rescaled

    """
    s1 = wData.shape  # a1.{width,height}
    e1 = _area_extent_from_user_area(pa.sArea, [0, 0])
    a1 = AreaDefinition("a1", "Source Area", "a1p", pa.projection, s1[1], s1[0], e1)
    i1 = ImageContainerQuick(wData, a1, nprocs=pa.nprocs)
    s2 = _compute_target_image_size(s1, pa.rescale)
    e2 = _area_extent_from_user_area(pa.tArea, pa.tOffset)
    a2 = AreaDefinition("a2", "Target Area", "a2p", pa.projection, s2[1], s2[0], e2)
    # ignore warning about proj4 string from pyproj.crs
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        i2 = i1.resample(a2)
        return i2.image_data


def _process_data(pa):
    """
    Perform data processing steps as follows:

    1. input image processing
    2. construct scalar wind velocity field, i.e., wind speed (magnitude),
        from {u,v} component data
    3. re-sample scalar wind field according to user supplied resolution
        (grid box size) and re-sample method
    4. encode re-sampled scalar wind field using 8-bit unsigned data
        denoting |ws| < 25 m/s
    5. output image processing (write wind speed magnitude as PNG file)

    Positional Parameters:

    pa      - parsed arguments (fom command line), a Namespace object

    Returns - path of output PNG file, i.e., oFile command line argument

    """
    # pylint: disable=raise-missing-from

    # 1. input image processing
    # ingest u-component image, reporting error if missing or corrupted
    try:
        uData = asarray(imread(pa.uFile), dtype="uint8")
    except FileNotFoundError as exc:
        raise DataError("%s: uData image file not found" % exc)
    # ingest v-component image, reporting error if missing or corrupted
    try:
        vData = asarray(imread(pa.vFile), dtype="uint8")
    except FileNotFoundError as exc:
        raise DataError("%s: uData image file not found" % exc)
    # basic validation of {u,v}-component image geometries
    assert vData.shape == uData.shape

    # 2. construct scalar wind velocity field, i.e., wind speed (magnitude),
    # from {u,v} component data
    wData = sqrt(decode_wind(uData) ** 2 + decode_wind(vData) ** 2)

    # 3. re-sample scalar wind field according to user supplied resolution
    # (grid box size) and re-sample method
    rData = _resample(pa, wData)

    # 4. encode re-sampled scalar wind field using 8-bit unsigned data
    # denoting |ws| < 25 m/s
    mData = _encode_wind_magnitude(rData).astype(dtype="uint8")

    # 5. output image processing (write wind speed magnitude as png file)
    imwrite(pa.oFile, mData, format="png")

    return pa.oFile


class Homework:
    """ Climate Homework """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        pass

    def run(self, args):
        # pylint: disable=no-self-use
        return _process_data(_process_args(args))


class DataError(Exception):
    # pylint: disable=missing-class-docstring
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


if __name__ == "__main__":
    Homework().run(sys.argv)
