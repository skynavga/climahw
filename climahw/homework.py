"""
ClimaCell Homework

Convert u- and v- wind velocity component data represented by 8-bit gray-scale
(as PNG images) to a scalar field then output as an (optionally rescaled)
8-bit gray-scale PNG file grid fitted to a user specified area of interest.

See README.md for further information.

Created on Feb 24, 2020 by
@author <glenn.adams@colorado.edu>
"""

from sys                        import argv
from os                         import cpu_count
from argparse                   import ArgumentParser, ArgumentTypeError

from imageio                    import imread, imwrite
from numpy                      import around, asarray, maximum, minimum, sqrt
from pyresample.geometry        import AreaDefinition
from pyresample.image           import ImageContainerQuick

from encoding                   import decode_wind, MAX_WIND_SPEED

class Homework():
    
    # defaults
    DEFAULT_AREA_SOURCE         = [1000.0, 500.0]
    DEFAULT_AREA_UNIT           = 'm'
    DEFAULT_IMAGE_SCALE         = 1.0
    DEFAULT_PROJECTION          = "+proj=utm +zone=13 +ellps=WGS84"
    DEFAULT_NUM_PROCS           = cpu_count()

    # other constants
    DEGREES_TO_METERS           = 500.0/0.005
    VERSION                     = "climahw 1.0 02/24/2020"

    def main(self, args):
        self.process_data(self.process_args(args))

    def process_args(self, args):
        """
        Process command line arguments

        Positional Parameters:

        args    - command line arguments

        Returns - Namespace object containing parsed command line arguments
        """
        ap = ArgumentParser(prog="climahw")
        # optional arguments (short and long form)
        ap.add_argument("-o", "--tOffset", dest="tOffset", type=float, nargs=2,
                        help="target area offset in specified units, as longitude and latitude offset")
        ap.add_argument("-p", "--projection", dest="projection", default=self.DEFAULT_PROJECTION,
                        help="projection applied to source and target areas")
        ap.add_argument("-r", "--rescale", dest="rescale", type=self.parse_rescale, default=self.DEFAULT_IMAGE_SCALE,
                        help="(re)scale factor to apply to output image")
        ap.add_argument("-s", "--sShape", dest="sShape", type=float, nargs=2, default=self.DEFAULT_AREA_SOURCE,
                        help="source area shape in specified units, as longitude and latitude dimensions")
        ap.add_argument("-t", "--tShape", dest="tShape", type=float, nargs=2,
                        help="target area shape in specified units, as longitude and latitude dimensions")
        ap.add_argument("-u", "--units", dest="units", type=self.parse_units, default=self.DEFAULT_AREA_UNIT,
                        help="units applied to area shapes, either 'm' (meters) or 'd' (degrees)")
        ap.add_argument("-v", "--version", action="version", version=self.VERSION)
        # optional arguments (long form only)
        ap.add_argument("--nprocs", dest="nprocs", type=self.parse_nprocs, default=self.DEFAULT_NUM_PROCS,
                        help="number of processors to apply to resampling operations")
        # positional arguments
        ap.add_argument("uFile", help="u-component input file, an 8-bit PNG grayscale image")
        ap.add_argument("vFile", help="v-component input file, an 8-bit PNG grayscale image")
        ap.add_argument("oFile", help="wind speed magnitude output file, an 8-bit PNG grayscale image")
        # parse arguments
        del args[0]                     # need to remove 0th argument which contains module name
        pa = ap.parse_args(args)        # now we can parse arguments
        # post-processing
        if pa.nprocs > self.DEFAULT_NUM_PROCS:
            pa.nprocs = self.DEFAULT_NUM_PROCS
        if pa.units == 'd':
            pa = self.normalize_units(pa)
        if pa.tShape is None:
            pa.tShape = pa.sShape
            pa.tOffset = [0,0]
        return pa

    def parse_rescale(self, string):
        """Parse and verify rescale option value."""
        value = float(string)
        if value < 0 or value > 1:
            raise ArgumentTypeError("%r is not a valid scale factor" % value)
        else:
            return value

    def parse_nprocs(self, string):
        """Parse and verify nprocs option value."""
        value = int(string)
        if value < 1:
            raise ArgumentTypeError("%r is not a valid number of processors, must be positive greater than 0" % value)
        elif value > self.DEFAULT_NUM_PROCS:
            raise ArgumentTypeError("%r is not a valid number of processors, must be less than cpu count %d" % (value, self.DEFAULT_NUM_PROCS))
        else:
            return value

    def parse_units(self, value):
        """Parse and verify units option value."""
        if value != 'm' and value != 'd':
            raise ArgumentTypeError("%r is not a valid unit 'm' or 'd'" % value)
        else:
            return value

    def normalize_units(self, pa):
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
        if pa.units == 'd':
            if pa.sShape is not None:
                pa.sShape = [*map(lambda x: x * self.DEGREES_TO_METERS, pa.sShape)]
            if pa.tShape is not None:
                pa.tShape = [*map(lambda x: x * self.DEGREES_TO_METERS, pa.tShape)]
            if pa.tOffset is not None:
                pa.tOffset = [*map(lambda x: x * self.DEGREES_TO_METERS, pa.tOffset)]
            pa.units = 'm'
        return pa

    def process_data(self, pa):
        """
        Perform data processing steps as follows:

        1. input image processing
        2. construct scalar wind velocity field, i.e., wind speed (magnitude), from {u,v} component data
        3. re-sample scalar wind field according to user supplied resolution (grid box size) and re-sample method
        4. encode re-sampled scalar wind field using 8-bit unsigned data denoting |ws| < 25 m/s
        5. output image processing (write wind speed magnitude as png file)

        Positional Parameters:

        pa      - parsed arguments (fom command line), a Namespace object

        Returns - None

        """
        # 1. input image processing
        # ingest u-component image, reporting error if missing or corrupted
        try:
            uData = asarray(imread(pa.uFile),dtype="uint8")
        except FileNotFoundError as exc:
            raise DataError("%s: uData image file not found" % exc)
        # ingest v-component image, reporting error if missing or corrupted
        try:
            vData = asarray(imread(pa.vFile),dtype="uint8")
        except FileNotFoundError as exc:
            raise DataError("%s: uData image file not found" % exc)
        # basic validation of {u,v}-component image geometries
        assert vData.shape == uData.shape;

        # 2. construct scalar wind velocity field, i.e., wind speed (magnitude), from {u,v} component data
        wData = sqrt(decode_wind(uData)**2 + decode_wind(vData)**2)
        
        # 3. re-sample scalar wind field according to user supplied resolution (grid box size) and re-sample method
        rData = self.resample(pa, wData)

        # 4. encode re-sampled scalar wind field using 8-bit unsigned data denoting |ws| < 25 m/s
        mData = self.encode_wind_magnitude(rData).astype(dtype="uint8")

        # 5. output image processing (write wind speed magnitude as png file)
        imwrite(pa.oFile, mData, format="png")

        pass

    def encode_wind_magnitude(self, magnitude):
        """ Take a real wind magnitude value and turn it into a byte """
        return self.encode_magnitude_to_scaled_byte(magnitude, MAX_WIND_SPEED)

    def encode_magnitude_to_scaled_byte(self, magnitude, max_value):
        """
        Scale a real magnitude value so it fits in a byte

        Scales a value between 0 and max_value to fit in an unsigned int between 0 and 255
        Values outside of the max_value range are clipped
        """
        return around(255*maximum(minimum(magnitude/max_value, 1), 0) + 0)

    def resample(self, pa, wData):
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
        s1      = wData.shape                                                                   # a1.{width,height}
        e1      = self.area_extent_from_user_shape(pa.sShape, [0,0])
        a1      = AreaDefinition("a1", "Source Area", "a1p", pa.projection, s1[1], s1[0], e1)
        i1      = ImageContainerQuick(wData, a1, nprocs=pa.nprocs)
        s2      = self.compute_target_image_size(s1, pa.rescale)
        e2      = self.area_extent_from_user_shape(pa.tShape, pa.tOffset)
        a2      = AreaDefinition("a2", "Target Area", "a2p", pa.projection, s2[1], s2[0], e2)
        i2      = i1.resample(a2)
        return i2.image_data
    
    def area_extent_from_user_shape(self, shape, offset):
        """ Compute area extent from shape and offset. """
        w = around(shape[0]/2)
        h = around(shape[1]/2)
        if offset is None:
            dx = -w
            dy = h
        else:
            dx = offset[0]
            dy = offset[1]
        return [-w + dx, -h + dy, w + dx, h + dy]

    def compute_target_image_size(self, source_image_size, scale_factor):
        """ Compute new image size using scale factor. """
        if scale_factor == 1:
            return source_image_size
        else:
            return [*map(lambda x: x * scale_factor, source_image_size)]

class DataError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

if __name__ == '__main__':
    Homework().main(argv)
