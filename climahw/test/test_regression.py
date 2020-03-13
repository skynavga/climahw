"""
Regression Test for ClimaCell Homework

Use unittest framework to perform regression test against previously resampled
wind data examples as described in README.md the output data of which is found in
the top-level data directory. These regression test cases merely rerun the same
resample operations and compare the output image against the previously computed
output images, reporting a failure if any change occurrs in the newly computed
output images.

Created on Feb 26, 2020 by
@author <glenn.adams@colorado.edu>
"""

import tempfile
import shutil
import unittest
import imageio
import numpy

from .. homework import Homework

class RegressionTestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._tempDir = tempfile.mkdtemp()
        
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tempDir)

    def test_regression_1(self):
        self._test_regression('', 'out1')

    def test_regression_2(self):
        self._test_regression('-r 0.25', 'out2')

    def test_regression_3(self):
        self._test_regression('-s 500 500 -t 250 250', 'out3')

    def test_regression_4(self):
        self._test_regression('-s 500 500 -t 250 250 -o 0 0', 'out4')

    def test_regression_5(self):
        self._test_regression('-s 500 500 -t 250 250 -o 125 125', 'out5')

    def test_regression_6(self):
        self._test_regression('-s 500 500 -t 250 250 -o 125 -125 -r 0.25 --nprocs 1', 'out6')

    def _test_regression(self, options, oFileName):
        (rArgs, rFile) = self._mkTestCase(options, oFileName)
        self.assertTrue(self._compareImages(Homework().run(rArgs), rFile))

    def _mkTestCase(self, options, oFileName):
        progn = 'climahw.homework'
        files = 'data/00_u.png data/00_v.png %s/%s.png' % (self._tempDir, oFileName)
        args  = '%s %s %s' % (progn, options, files)
        rArgs = args.split()
        rFile = 'out/' + oFileName + '.png'
        return rArgs, rFile

    def _compareImages(self, oFile, rFile):
        oa = numpy.asarray(imageio.imread(oFile), dtype='uint8')
        ra = numpy.asarray(imageio.imread(rFile), dtype='uint8')
        return numpy.array_equal(oa, ra)
