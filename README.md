# ClimaCell Python Homework

## Approach

In order to resample (regrid) the input wind data, I have made use of the [pyresample](https://pyresample.readthedocs.io/en/latest/) package, which was specifically designed "for resampling geospatial image data" for use with the [SatPy](https://github.com/pytroll/satpy) library, a python library used for "manipulating meterological remote sensing data". Since [pyresample](https://pyresample.readthedocs.io/en/latest/) makes use of the [PROJ](https://proj.org/) project, common cartographic projections used by meterological applications are available for use for resampling purposes.

For this simple assignment, I have selected the [UTM](https://proj.org/operations/projections/utm.html) projection, zone 13 (covering, e.g., Boulder), ellipsoid [WGS84](https://en.wikipedia.org/wiki/World_Geodetic_System) as the default projection with its natural origin, i.e., neglecting the application of the nominal UTM false easting and northing. Although the [Transverse Mercator](https://en.wikipedia.org/wiki/Transverse_Mercator_projection) projections (such as [UTM](https://proj.org/operations/projections/utm.html)) are not area preserving (like the [Lambert Azimuthal Equal Area](https://proj.org/operations/projections/laea.html) projection), they are angle preserving, i.e., they are conformal mappings, and, therefore, are good for applications that employ small scale maps, particularly local weather analyses such as used with the data sets supplied here. If an alternate projection is preferred for grid resampling, it may be specified by means of the `-p/--projection` command line option, which expects a PROJ4 projection string format. The specified projection must be compatible with units based on meters rather than degrees, as the current code normalizes all area coordinates to meters. The specified (or default) projection applies to both source and target areas.

## Additional Notes

1. Both source and target areas, specified with the `-s/--sArea` and `-t/--tArea` command line options, are interpreted in meters or degrees depending on the value of the `-u/--units` option (default is `m`). If not specified, the source area defaults to 500 meters width (longitude) and height (latitude). If the target shape is not specified, it defaults to the source shape. For the purpose of resampling, the centers of the areas are their centroids (and not their top, left corners). In order to allow specifying a target area which center is not coincident with the source area's center, a `-o/--tOffset` option is available which takes a longitude/latitude offset (in meters or degrees according to the applicable units) with respect to the center of the source area. If no offset is specified, and the target shape is not the same as the source shape, then an offset is implied that places the target area such that its upper left corner coincides with the upper left corner of the source area; however, if the target area is not specified (but defaulted to the source area), then its offset will default to `[0,0]` which places it coincident to the center of the source area.

2. Although [pyresample](https://pyresample.readthedocs.io/en/latest/) provides a number of resampling algorithms, I have selected a simple and quick approximate nearest neighbor algorithm for this exercise. Other algorithms are available, including bilinear, elliptical weighted average (EWA), and Gaussian weighted, but are not yet exposed by this tool.

3. In addition to first order resampling (mapping from source to target areas), the present implementation can also optionally perform a second order downsampling of the output image data by scaling the output image with a specified scaling factor as specified by the `-r/--rescale` option, which takes a ratio (less than or equal to 1.0).

4. The [pyresample](https://pyresample.readthedocs.io/en/latest/) implementation supports multiprocessor platforms. For this exercise, the maximum number of processors available are used for resampling operations, however, a command line option `--nprocs` is available to permit user control over the actual cpu count.

5. For the purpose of converting between degrees to linear distance, the instructions specify use of a fixed conversion factor of 500 meters per 0.005 degrees latitude (and longitude), which works out to 100km/degree. I will just mention that the relationship between degrees latitude and longitude and linear distance is not constant on the surface of the Earth; for latitude, it is nearly constant at ~111km/degree, slightly increasing towards the poles; however, for longitude, it is at a maximum (also ~111km) near the equator, and decreasing to zero at the poles. As a consequence, using a constant mapping of 100km/degree, while a convenient simplification, introduces gross errors when used to process real world data. However, since we are using the [UTM](https://proj.org/operations/projections/utm.html) projection for resampling (by default), which has its origin on the Equator, then the mapping turns out to be nearly constant, so the stated conversion is not unreasonable as a rough approximation.

## Dependencies

  - [imageio](https://imageio.readthedocs.io/en/stable/index.html) 2.8.0
  - [numpy](https://numpy.org/) 1.18.1
  - [pyresample](https://pyresample.readthedocs.io/en/latest/) 1.14.0
  - [python](https://www.python.org/) 3.8
  
Later versions of the above are presumed to work (but have not been tested).

## Installation

```
conda env create -f environment.yml
conda activate climahw
... run climahw examples, tests, etc. ...
conda deactivate
```

## Deinstallation

```
conda env remove --name climahw
```

## Example Usage

The following examples may be performed from the top-level directory of the source (or binary) distribution.

1. Perform identity mapping (modulo resampling artifacts).

`% python -m climahw.homework data/00_u.png data/00_v.png out/out1.png`

2. Resample with same target area as source area but rescale (downsample) output image to 25% of original resolution.

`% python -m climahw.homework -r 0.25 data/00_u.png data/00_v.png out/out2.png`

3. Resample with target area as top left quadrant of source area

`% python -m climahw.homework -s 500 500 -t 250 250 data/00_u.png data/00_v.png out/out3.png`

4. Resample with target area as central [50% 50%] of source area

`% python -m climahw.homework -s 500 500 -t 250 250 -o 0 0 data/00_u.png data/00_v.png out/out4.png`

5. Resample with target area as top right quadrant of source area

`% python -m climahw.homework -s 500 500 -t 250 250 -o 125 125 data/00_u.png data/00_v.png out/out5.png`

6. Resample with target area as bottom right quadrant of source area, and further rescale output image to 25% of original, also, use single processor.

`% python -m climahw.homework -s 500 500 -t 250 250 -o 125 -125 -r 0.25 --nprocs 1 data/00_u.png data/00_v.png out/out6.png`

7. Get usage information.

`% python -m climahw.homework --help`

```
usage: climahw [-h] [-o TOFFSET TOFFSET] [-p PROJECTION] [-r RESCALE] [-s SAREA SAREA] [-t TAREA TAREA] [-u UNITS] [-v] [--nprocs NPROCS]
               uFile vFile oFile

positional arguments:
  uFile                 u-component input file, an 8-bit PNG grayscale image
  vFile                 v-component input file, an 8-bit PNG grayscale image
  oFile                 wind speed magnitude output file, an 8-bit PNG grayscale image

optional arguments:
  -h, --help            show this help message and exit
  -o TOFFSET TOFFSET, --tOffset TOFFSET TOFFSET
                        target area offset in specified units, as longitude and latitude offset
  -p PROJECTION, --projection PROJECTION
                        projection applied to source and target areas
  -r RESCALE, --rescale RESCALE
                        (re)scale factor to apply to output image
  -s SAREA SAREA, --sArea SAREA SAREA
                        source area shape in specified units, as longitude and latitude dimensions
  -t TAREA TAREA, --tArea TAREA TAREA
                        target area shape in specified units, as longitude and latitude dimensions
  -u UNITS, --units UNITS
                        units applied to area shapes, either 'm' (meters) or 'd' (degrees)
  -v, --version         show program's version number and exit
  --nprocs NPROCS       number of processors to apply to resampling operations
```

8. Get version information.

```
% python -m climahw.homework --version
climahw 1.0.1 03/11/2020
```

## Testing

After the `conda` environment is activated as described in [Installation](#installation),
testing may be performed by running the`test.sh` script from the top-level directory:

```
% bash test.sh
```

This will perform style, lint, and type checks, then re-run the examples described above, comparing the output images against the images previously computed and saved in the top-level `out` directory.

The nominal output from a successful test should read as follows:

```
python -m black --check climahw
All done! ✨ 🍰 ✨
5 files would be left unchanged.
python -m pylint climahw

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

python -m mypy climahw
Success: no issues found in 5 source files
python -m unittest discover -v climahw
test_regression_1 (test.test_regression.RegressionTestClass) ... ok
test_regression_2 (test.test_regression.RegressionTestClass) ... ok
test_regression_3 (test.test_regression.RegressionTestClass) ... ok
test_regression_4 (test.test_regression.RegressionTestClass) ... ok
test_regression_5 (test.test_regression.RegressionTestClass) ... ok
test_regression_6 (test.test_regression.RegressionTestClass) ... ok

----------------------------------------------------------------------
Ran 6 tests in 96.224s

OK
```

<<<<<<< HEAD
## Dependencies

- [imageio](https://imageio.readthedocs.io/en/stable/index.html) 2.8.0
- [numpy](https://numpy.org/) 1.18.1
- [pyresample](https://pyresample.readthedocs.io/en/latest/) 1.14.0
- [python](https://www.python.org/) 3.8

Later versions of the above are presumed to work (but have not been tested).

=======
>>>>>>> c53836965395beafa5a5881aaeb35c9d5251a550
## Potential Improvements

1. Improve usage message (add default option values, improve option argument labels, etc).

2. Test alternative projections.

3. Eliminate assumptions about degree to length conversions, in which case it will be necessary to add option for user to specify lat/lon origin of source area. At present, defaults to origin of UTM zone.

4. Add further inline code documentation and expand variable name length should this code evolve into production code.

5. Add support for additional resample methods (bilinear, kdtree, elliptical, Gaussian, etc)

6. Obtain performance benchmarking metrics by resampling method and cpu count.
