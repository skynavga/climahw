# ClimaCell Python Homework

## Approach

In order to resample (regrid) the input wind data, I have made use of the [pyresample](https://pyresample.readthedocs.io/en/latest/) package, which was specifically designed "for resampling geospatial image data" for use with the [SatPy](https://github.com/pytroll/satpy) library, a python library used for "manipulating meterological remote sensing data". Since [pyresample](https://pyresample.readthedocs.io/en/latest/) makes use of the [PROJ](https://proj.org/) project, common cartographic projections used by meterological applications are available for use for resampling purposes.

For this simple assignment, I have selected the [UTM](https://proj.org/operations/projections/utm.html) projection, zone 13 (covering, e.g., Boulder), ellipsoid [WGS84](https://en.wikipedia.org/wiki/World_Geodetic_System) as the default projection. Although the forms of [Mercator](https://en.wikipedia.org/wiki/Mercator_projection) projection (such as the [UTM](https://proj.org/operations/projections/utm.html)) are not area preserving (like the [Lambert Azimuthal Equal Area](https://proj.org/operations/projections/laea.html) projection), they are angle preserving, i.e., they are conformal mappings, and, therefore, are good for applications that employ small scale maps, particularly local weather analyses such as used with the data sets supplied here. If an alternate projection is preferred for grid resampling, it may be specified by means of the ``-p/--projection`` command line option, which expects a PROJ4 projection string format. The specified projection must be compatible with units based on meters rather than degrees, as the current code normalizes all area coordinates to meters. The specified (or default) projection applies to both source and target areas.

## Additional Notes

1. Both source and target areas, specified with the ``-s/--sShape`` and ``-t/--tShape`` command line options, are interpreted in meters or degrees depending on the value of the ``-u/--units`` option (default is ``m``). If not specified, the source area defaults to 1000 meters longitude and 500 meters latitude (corresponding to 0.010 and 0.005 degrees). If the target shape is not specified, it defaults to the source shape. For the purpose of resampling, the centers of the areas are their centroids (and not their top, left corners). In order to allow specifying a target area which center is not coincident with the source area's center, a ``-o/--tOffset`` option is available which takes a longitude/latitude offset (in meters or degrees according to the applicable units) with respect to the center of the source area. If no offset is specified, and the target shape is not the same as the source shape, then an offset is implied that places the target area such that its upper left corner coincides with the upper left corner of the source area; however, if the target area is not specified (but defaulted to the source area), then its offset will default to ``[0,0]`` which places it coincident to the center of the source area.

2. Although [pyresample](https://pyresample.readthedocs.io/en/latest/) provides a number of resampling algorithms, I have selected a simple and quick approximate nearest neighbor algorithm for this exercise. Other algorithms are available, including bilinear, elliptical weighted average (EWA), and Gaussian weighted, but are not yet exposed by this tool.

3. In addition to first order resampling (mapping from source to target areas), the present implementation can also optionally perform a second order downsampling of the output image data by scaling the output image with a specified scaling factor as specified by the ``-r/--rescale`` option, which takes a ratio (less than or equal to 1.0).

4. The [pyresample](https://pyresample.readthedocs.io/en/latest/) implementation supports multiprocessor platforms. For this exercise, the maximum number of processors available are used for resampling operations, however, a command line option ``--nprocs`` is available to permit user control over the actual cpu count.

5. The given problem description indicates that the input data corresponds to a 0.005 degree spatial resolution grid. Since the input image data is rectangular according to a pixel ratio 2:1 (longitudinally by latitudinally), and I have no information to the contrary, I will assume that image pixels correspond to square spatial samples, and, therefore, that each image corresponds to a grid box having dimensions of 0.010 by 0.005 degrees, which, according to the provided documentation, are to be treated as 1000 by 500 meters using a conversion factor of 500 meters to 0.005 degrees (100km/degree).

6. In further comment to the last note, I will just mention that the relationship between degrees latitude and longitude and linear distance is not constant on the surface of the Earth; for latitude, it is nearly constant at ~111km/degree, slightly increasing towards the poles; however, for longitude, it is at a maximum (also ~111km) near the equator, and decreasing to zero at the poles. As a consequence, using a constant mapping of 100km/degree, while a convenient simplification, introduces gross errors when used to process real world data. However, since we are using the [UTM](https://proj.org/operations/projections/utm.html) projection for resampling (by default), which has its origin on the Equator, then the mapping turns out to be nearly equal, so the stated conversion is not unreasonable as a rough approximation.

## Example Usage

The following examples may be performed from the top-level directory of the source (or binary) distribution.

1. Perform identity mapping (modulo resampling artifacts).

```% python -m climahw.homework data/00_u.png data/00_v.png out/out1.png```

2. Resample with same target area as source area but rescale (downsample) output image to 25% of original resolution.

```% python -m climahw.homework -r 0.25 data/00_u.png data/00_v.png out/out2.png```

3. Resample with target area as top left quadrant of source area

```% python -m climahw.homework -s 1000 500 -t 500 250 data/00_u.png data/00_v.png out/out3.png```

4. Resample with target area as central [50% 50%] of source area

```% python -m climahw.homework -s 1000 500 -t 500 250 -o 0 0 data/00_u.png data/00_v.png out/out4.png```

5. Resample with target area as top right quadrant of source area

```% python -m climahw.homework -s 1000 500 -t 500 250 -o 250 125 data/00_u.png data/00_v.png out/out5.png```

6. Resample with target area as bottom right quadrant of source area, and further rescale output image to 25% of original, also, use single processor.

```% python -m climahw.homework -s 1000 500 -t 500 250 -o 250 -125 -r 0.25 --nprocs 1 data/00_u.png data/00_v.png out/out6.png```

7. Get usage information.

```% python -m climahw.homework --help```

```
usage: climahw [-h] [-o TOFFSET TOFFSET] [-p PROJECTION] [-r RESCALE] [-s SSHAPE SSHAPE] [-t TSHAPE TSHAPE] [-u UNITS] [-v] [--nprocs NPROCS]
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
  -s SSHAPE SSHAPE, --sShape SSHAPE SSHAPE
                        source area shape in specified units, as longitude and latitude dimensions
  -t TSHAPE TSHAPE, --tShape TSHAPE TSHAPE
                        target area shape in specified units, as longitude and latitude dimensions
  -u UNITS, --units UNITS
                        units applied to area shapes, either 'm' (meters) or 'd' (degrees)
  -v, --version         show program's version number and exit
  --nprocs NPROCS       number of processors to apply to resampling operations
```

8. Get version information.

```
% python -m climahw.homework --version
climahw 1.0 02/24/2020
```
## Testing

A simple regression test may be performed by running the following from the top-level directory:

```
% python -m unittest discover -v
```

This will re-run the examples described above, comparing the output images against the images previously computed and saved in the top-level ``data`` directory.

## Dependencies

  - [imageio](https://imageio.readthedocs.io/en/stable/index.html) 2.8.0
  - [numpy](https://numpy.org/) 1.18.1
  - [pyresample](https://pyresample.readthedocs.io/en/latest/) 1.14.0
  - [python](https://www.python.org/) 3.6
  
Later versions of the above are presumed to work (but have not been tested).

## Potential Improvements

1. Improve usage message (add default option values, improve option argument labels, etc).

2. Test alternative projections.

3. Eliminate assumptions about degree to length conversions, in which case it will be necessary to add option for user to specify lat/lon origin of source area. At present, defaults to origin of UTM zone.

4. Add further inline code documentation and expand variable name length should this code evolve into production code.

5. Add support for additional resample methods (bilinear, kdtree, elliptical, Gaussian, etc)

6. Obtain performance benchmarking metrics by resampling method and cpu count.
