from scipy.optimize import leastsq
import numpy as np
import matplotlib.pyplot as plt
import lmfit
from tools import *

from scipy.stats import linregress

import pickle

CALIB_STAGE_LOWMAG = "calib_stage_lowmag.pickle"
CALIB_BEAMSHIFT = "calib_beamshift.pickle"
CALIB_BRIGHTNESS = "calib_brightness.pickle"
CALIB_DIFFSHIFT = "calib_diffshift.pickle"


class CalibDiffShift(object):
    """Simple class to hold the methods to perform transformations from one setting to another
    based on calibration results

    NOTE: The TEM stores different values for diffshift depending on the mode used
        i.e. mag1 vs sa-diff"""
    def __init__(self, rotation, translation, neutral_beamshift=None):
        super(CalibDiffShift, self).__init__()
        self.rotation = rotation
        self.translation = translation
        if not neutral_beamshift:
            neutral_beamshift = (32576, 31149)
        self.neutral_beamshift = neutral_beamshift
        self.has_data = False

    def __repr__(self):
        return "CalibDiffShift(rotation=\n{},\n translation=\n{})".format(
            self.rotation, self.translation)

    def diffshift2beamshift(self, diffshift):
        diffshift = np.array(diffshift)
        r = self.rotation
        t = self.translation

        return (np.dot(diffshift, r) + t).astype(int)

    def beamshift2diffshift(self, beamshift):
        beamshift = np.array(beamshift)
        r_i = np.linalg.inv(self.rotation)
        t = self.translation

        return np.dot(beamshift - t, r_i).astype(int)

    def compensate_beamshift(self, ctrl):
        if not ctrl.mode == "diff":
            print " >> Switching to diffraction mode"
            ctrl.mode_diffraction()
        beamshift = ctrl.beamshift.get()
        diffshift = self.beamshift2diffshift(beamshift)
        ctrl.diffshift.set(*diffshift)

    def compensate_diffshift(self, ctrl):
        if not ctrl.mode == "diff":
            print " >> Switching to diffraction mode"
            ctrl.mode_diffraction()
        diffshift = ctrl.diffshift.get()
        beamshift = self.diffshift2beamshift(diffshift)
        ctrl.beamshift.set(*beamshift)

    def reset(self, ctrl):
        ctrl.beamshift.set(*self.neutral_beamshift)
        self.compensate_diffshift()

    @classmethod
    def from_data(cls, diffshift, beamshift, neutral_beamshift):
        r, t = fit_affine_transformation(diffshift, beamshift, translation=True, shear=True)

        c = cls(rotation=r, translation=t, neutral_beamshift=neutral_beamshift)
        c.data_diffshift = diffshift
        c.data_beamshift = beamshift
        c.has_data = True
        return c

    @classmethod
    def from_file(cls, fn=CALIB_DIFFSHIFT):
        try:
            return pickle.load(open(fn, "r"))
        except IOError as e:
            prog = "instamatic.calibrate_diffshift"
            raise IOError("{}: {}. Please run {} first.".format(e.strerror, fn, prog))

    def to_file(self, fn=CALIB_DIFFSHIFT):
        pickle.dump(self, open(fn, "w"))

    def plot(self):
        if not self.has_data:
            return
    
        diffshift = self.data_diffshift

        r_i = np.linalg.inv(self.rotation)
        beamshift_ = np.dot(self.data_beamshift - self.translation, r_i)
    
        plt.scatter(*diffshift.T, label="Observed Diffraction shift")
        plt.scatter(*beamshift_.T, label="Calculated DiffShift from BeamShift")
        plt.legend()
        plt.show()


class CalibBeamShift(object):
    """Simple class to hold the methods to perform transformations from one setting to another
    based on calibration results"""
    def __init__(self, transform, reference_shift, reference_pixel):
        super(CalibBeamShift, self).__init__()
        self.transform = transform
        self.reference_shift = reference_shift
        self.reference_pixel = reference_pixel
        self.has_data = False
   
    def __repr__(self):
        return "CalibBeamShift(transform=\n{},\n   reference_shift=\n{},\n   reference_pixel=\n{})".format(
            self.transform, self.reference_shift, self.reference_pixel)

    def beamshift_to_pixelcoord(self, beamshift):
        """Converts from beamshift x,y to pixel coordinates"""
        r_i = np.linalg.inv(self.transform)
        pixelcoord = np.dot(self.reference_shift - beamshift, r_i) + self.reference_pixel
        return pixelcoord
        
    def pixelcoord_to_beamshift(self, pixelcoord):
        """Converts from pixel coordinates to beamshift x,y"""
        r = self.transform
        beamshift = self.reference_shift - np.dot(pixelcoord - self.reference_pixel, r)
        return beamshift.astype(int)

    @classmethod
    def from_data(cls, shifts, beampos, reference_shift, reference_pixel):
        r, t = fit_affine_transformation(shifts, beampos)

        c = cls(transform=r, reference_shift=reference_shift, reference_pixel=reference_pixel)
        c.data_shifts = shifts
        c.data_beampos = beampos
        c.has_data = True
        return c

    @classmethod
    def from_file(cls, fn=CALIB_BEAMSHIFT):
        try:
            return pickle.load(open(fn, "r"))
        except IOError as e:
            prog = "instamatic.calibrate_beamshift"
            raise IOError("{}: {}. Please run {} first.".format(e.strerror, fn, prog))

    def to_file(self, fn=CALIB_BEAMSHIFT):
        pickle.dump(self, open(fn, "w"))

    def plot(self):
        if not self.has_data:
            return

        beampos = self.data_beampos
        shifts = self.data_shifts

        r_i = np.linalg.inv(self.transform)
        beampos_ = np.dot(beampos, r_i)

        plt.scatter(*shifts.T, label="Observed pixel shifts")
        plt.scatter(*beampos_.T, label="Positions in pixel coords")
        plt.legend()
        plt.show()


class CalibBrightness(object):
    """docstring for calib_brightness"""
    def __init__(self, slope, intercept):
        self.slope = slope
        self.intercept = intercept
        self.has_data = False

    def __repr__(self):
        return "CalibBrightness(slope={}, intercept={})".format(self.slope, self.intercept)

    def brightness_to_pixelsize(self, val):
        return self.slope*val + self.intercept

    def pixelsize_to_brightness(self, val):
        return int((val - self.intercept) / self.slope)

    @classmethod
    def from_data(cls, brightness, pixeldiameter):
        slope, intercept, r_value, p_value, std_err = linregress(brightness, pixeldiameter)
        print
        print "r_value: {:.4f}".format(r_value)
        print "p_value: {:.4f}".format(p_value)

        c = cls(slope=slope, intercept=intercept)
        c.data_brightness = brightness
        c.data_pixeldiameter = pixeldiameter
        c.has_data = True
        return c

    @classmethod
    def from_file(cls, fn=CALIB_BRIGHTNESS):
        try:
            return pickle.load(open(fn, "r"))
        except IOError as e:
            prog = "instamatic.calibrate_brightness"
            raise IOError("{}: {}. Please run {} first.".format(e.strerror, fn, prog))

    def to_file(self, fn=CALIB_BRIGHTNESS):
        pickle.dump(self, open(fn, "w"))

    def plot(self):
        if not self.has_data:
            pass

        mn = self.data_brightness.min()
        mx = self.data_brightness.max()
        extend = abs(mx - mn)*0.1
        x = np.linspace(mn - extend, mx + extend)
        y = self.brightness_to_pixelsize(x)
    
        plt.plot(x, y, "r-", label="linear regression")
        plt.scatter(self.data_brightness, self.data_pixeldiameter)
        plt.title("Fit brightness")
        plt.legend()
        plt.show()


class CalibStage(object):
    """Simple class to hold the methods to perform transformations from one setting to another
    based on calibration results"""
    def __init__(self, rotation, translation=np.array([0, 0]), reference_position=np.array([0, 0])):
        super(CalibStage, self).__init__()
        self.has_data = False
        self.rotation = rotation
        self.translation = translation
        self.reference_position = reference_position
   
    def __repr__(self):
        return "CalibStage(rotation=\n{},\n translation=\n{},\n reference_position=\n{})".format(self.rotation, self.translation, self.reference_position)

    def _reference_setting_to_pixelcoord(self, px_ref, image_pos, r, t, reference_pos):
        """
        Function to transform stage position to pixel coordinates
        
        px_ref: `list`
            stage position (x,y) to transform to pixel coordinates on 
            current image
        r: `2d ndarray`, shape (2,2)
            transformation matrix from calibration
        image_pos: `list`
            stage position that the image was captured at
        reference_pos: `list`
            stage position of the reference (center) image
        """
        image_pos = np.array(image_pos)
        reference_pos = np.array(reference_pos)
        px_ref = np.array(px_ref)
        
        # do the inverse transoformation here
        r_i = np.linalg.inv(r)
        
        # get stagepos vector from reference image (center) to current image
        vect = image_pos - reference_pos
        
        # px_ref -> pixel coords, and add offset for pixel position
        px = px_ref - np.dot(vect - t, r_i)
    
        return px
     
    def _pixelcoord_to_reference_setting(self, px, image_pos, r, t, reference_pos):
        """
        Function to transform pixel coordinates to pixel coordinates in reference setting
        
        px: `list`
            image pixel coordinates to transform to stage position
        r: `2d ndarray`, shape (2,2)
            transformation matrix from calibration
        image_pos: `list`
            stage position that the image was captured at
        reference_pos: `list`
            stage position of the reference (center) image
        """
        image_pos = np.array(image_pos)
        reference_pos = np.array(reference_pos)
        px = np.array(px)
        
        # do the inverse transoformation here
        r_i = np.linalg.inv(r)
        
        # get stagepos vector from reference image (center) to current image
        vect = image_pos - reference_pos
        
        # stagepos -> pixel coords, and add offset for pixel position
        px_ref = np.dot(vect - t, r_i) + np.array(px)
    
        return px_ref

    def _pixelcoord_to_stagepos(self, px, image_pos, r, t, reference_pos):
        """
        Function to transform pixel coordinates to stage position
        
        px: `list`
            image pixel coordinates to transform to stage position
        r: `2d ndarray`, shape (2,2)
            transformation matrix from calibration
        image_pos: `list`
            stage position that the image was captured at
        reference_pos: `list`
            stage position of the reference (center) image
        """
        reference_pos = np.array(reference_pos)
        
        px_ref = self._pixelcoord_to_reference_setting(px, image_pos, r, t, reference_pos)
    
        stagepos = np.dot(px_ref - 1024, r) + t + reference_pos
        
        return stagepos

    def _stagepos_to_pixelcoord(self, stagepos, image_pos, r, t, reference_pos):
        """
        Function to transform pixel coordinates to stage position
        
        px: `list`
            image pixel coordinates to transform to stage position
        r: `2d ndarray`, shape (2,2)
            transformation matrix from calibration
        image_pos: `list`
            stage position that the image was captured at
        reference_pos: `list`
            stage position of the reference (center) image
        """
        stagepos = np.array(stagepos)
        image_pos = np.array(image_pos)
        reference_pos = np.array(reference_pos)
        
        # do the inverse transoformation here
        r_i = np.linalg.inv(r)

        px_ref = np.dot(stagepos - t - reference_pos, r_i) + 1024

        px = self._reference_setting_to_pixelcoord(px_ref, image_pos, r, t, reference_pos)

        return px

    def reference_setting_to_pixelcoord(self, px_ref, image_pos):
        """
        Function to transform pixel coordinates in reference setting to current frame
        """
        return self._reference_setting_to_pixelcoord(px_ref, image_pos, self.rotation, self.translation, self.reference_position)

    def pixelcoord_to_reference_setting(self, px, image_pos):
        """
        Function to transform pixel coordinates in current frame to reference setting
        """
        return self._pixelcoord_to_reference_setting(px, image_pos, self.rotation, self.translation, self.reference_position)

    def pixelcoord_to_stagepos(self, px, image_pos):
        """
        Function to transform pixel coordinates to stage position coordinates
        """
        return self._pixelcoord_to_stagepos(px, image_pos, self.rotation, self.translation, self.reference_position)

    def stagepos_to_pixelcoord(self, stagepos, image_pos):
        """
        Function to stage position coordinates to pixel coordinates on current frame
        """
        return self._stagepos_to_pixelcoord(stagepos, image_pos, self.rotation, self.translation, self.reference_position)

    @classmethod
    def from_data(cls, shifts, stagepos, reference_position):
        r, t = fit_affine_transformation(shifts, stagepos)

        c = cls(rotation=r, translation=t, reference_position=reference_position)
        c.data_shifts = shifts
        c.data_stagepos = stagepos
        c.has_data = True
        return c

    @classmethod
    def from_file(cls, fn=CALIB_STAGE_LOWMAG):
        try:
            return pickle.load(open(fn, "r"))
        except IOError as e:
            prog = "instamatic.calibrate_stage_lowmag"
            raise IOError("{}: {}. Please run {} first.".format(e.strerror, fn, prog))

    def to_file(self, fn=CALIB_STAGE_LOWMAG):
        pickle.dump(self, open(fn, "w"))

    def plot(self):
        if not self.has_data:
            return

        stagepos = self.data_stagepos
        shifts = self.data_shifts

        r_i = np.linalg.inv(self.rotation)

        stagepos_ = np.dot(stagepos - self.translation, r_i)

        plt.scatter(*shifts.T, label="Observed pixel shifts")
        plt.scatter(*stagepos_.T, label="Positions in pixel coords")
        
        for i, (x,y) in enumerate(shifts):
            plt.text(x+5, y+5, str(i), size=14)

        plt.legend()
        plt.show()


def fit_affine_transformation(a, b, x0=None, rotation=True, scaling=True, translation=False, shear=False):
    params = lmfit.Parameters()
    params.add("angle", value=0, vary=rotation, min=-np.pi, max=np.pi)
    params.add("sx"   , value=1, vary=scaling)
    params.add("sy"   , value=1, vary=scaling)
    params.add("tx"   , value=0, vary=translation)
    params.add("ty"   , value=0, vary=translation)
    params.add("k1"   , value=1, vary=shear)
    params.add("k2"   , value=1, vary=shear)
    
    def objective_func(params, arr1, arr2):
        angle = params["angle"].value
        sx    = params["sx"].value
        sy    = params["sy"].value 
        tx    = params["tx"].value
        ty    = params["ty"].value
        k1    = params["k1"].value
        k2    = params["k2"].value
        
        sin = np.sin(angle)
        cos = np.cos(angle)

        r = np.array([
            [ sx*cos, -sy*k1*sin],
            [ sx*k2*sin,  sy*cos]])
        t = np.array([tx, ty])

        fit = np.dot(arr1, r) + t
        return fit-arr2
    
    method = "leastsq"
    args = (a, b)
    res = lmfit.minimize(objective_func, params, args=args, method=method)
    
    lmfit.report_fit(res)
    
    angle = res.params["angle"].value
    sx    = res.params["sx"].value
    sy    = res.params["sy"].value 
    tx    = res.params["tx"].value
    ty    = res.params["ty"].value
    k1    = res.params["k1"].value
    k2    = res.params["k2"].value
    
    sin = np.sin(angle)
    cos = np.cos(angle)
    
    r = np.array([
        [ sx*cos, -sy*k1*sin],
        [ sx*k2*sin,  sy*cos]])
    t = np.array([tx, ty])
    
    return r, t


# lowmag
# pixel dimensions from calibration in Digital Micrograph
# x,y dimensions of 1 pixel in micrometer
lowmag_dimensions = {
50:      (0.895597,  0.895597),
80:      (0.559748,  0.559748),
100:     (0.447799,  0.447799),
150:     (0.298532,  0.298532),
200:     (0.223899,  0.223899),
250:     (0.179119,  0.179119),
300:     (0.149266,  0.149266),
400:     (0.111949,  0.111949),
500:     (0.089559,  0.089559),
600:     (0.074633,  0.074633),
800:     (0.055974,  0.055974),
1000:    (0.044779,  0.044779),
1200:    (0.037316,  0.037316),
1500:    (0.029853,  0.029853),
2000:    (0.020800,  0.020800),
2500:    (0.016640,  0.016640),
3000:    (0.013866,  0.013866),
5000:    (0.008320,  0.008320),
6000:    (0.006933,  0.006933),
8000:    (0.005200,  0.005200),
10000:   (0.004160,  0.004160),
12000:   (0.003466,  0.003466),
15000:   (0.002773,  0.002773)
}

lowmag_om_standard_focus = {
50:      24722,
80:      32582,
100:     32582,
150:     42134,
200:     41622,
250:     41338,
300:     40858,
400:     40300,
500:     39914,
600:     39808,
800:     39642,
1000:    39234,
1200:    38362,
1500:    37930,
2000:    37718,
2500:    37293,
3000:    49025,
5000:    49010,
6000:    49000,
8000:    48983,
10000:   48960,
12000:   48931,
15000:   48931
}

lowmag_neutral_beamtilt = {
50:      (33201,     24555),
80:      (33201,     24555),
100:     (33201,     24555),
150:     (33201,     24555),
200:     (33201,     24555),
250:     (33201,     24555),
300:     (33201,     24555),
400:     (33201,     24555),
500:     (33201,     24555),
600:     (33201,     24555),
800:     (33201,     24555),
1000:    (33201,     24555),
1200:    (33201,     24555),
1500:    (33201,     24555),
2000:    (33201,     24555),
2500:    (33201,     24555),
3000:    (33201,     24555),
5000:    (33201,     24555),
6000:    (33201,     24555),
8000:    (33201,     24555),
10000:   (33201,     24555),
12000:   (33201,     24555),
15000:   (33201,     24555)
}

lowmag_neutral_imageshift = {
50:      (33152,     32576),
50:      (33152,     32576),
50:      (33152,     32576),
80:      (33152,     32576),
100:     (33152,     32576),
150:     (32384,     33280),
200:     (32384,     33280),
250:     (32384,     33280),
300:     (32384,     33280),
400:     (32384,     33280),
500:     (32384,     33280),
600:     (32384,     33280),
800:     (32384,     33280),
1000:    (32384,     33280),
1200:    (32384,     33280),
1500:    (32384,     33280),
2000:    (32384,     33280),
2500:    (32384,     33280),
3000:    (31104,     31296),
5000:    (31104,     31296),
6000:    (31104,     31296),
8000:    (31104,     31296),
10000:   (31104,     31296),
12000:   (31104,     31296),
15000:   (31104,     31296),
}

lowmag_neutral_beamshift = {
50:      (30450,     29456),
80:      (30450,     29456),
100:     (30450,     29456),
150:     (30450,     29456),
200:     (30450,     29456),
250:     (30450,     29456),
300:     (30450,     29456),
400:     (30450,     29456),
500:     (30450,     29456),
600:     (30450,     29456),
800:     (30450,     29456),
1000:    (30450,     29456),
1200:    (30450,     29456),
1500:    (30450,     29456),
2000:    (30450,     29456),
2500:    (30450,     29456),
3000:    (30450,     29456),
5000:    (30450,     29456),
6000:    (30450,     29456),
8000:    (30450,     29456),
10000:   (30450,     29456),
12000:   (30450,     29456),
15000:   (30450,     29456),
}

# mag1
# pixel dimensions from calibration in Digital Micrograph
# x,y dimensions of 1 pixel in micrometer
mag1_dimensions = {
2500:    (0,         0),
3000:    (0,         0),
4000:    (0,         0),
5000:    (0,         0),
6000:    (0,         0),
8000:    (0,         0),
10000:   (0,         0),
12000:   (0,         0),
15000:   (0,         0),
20000:   (0,         0),
25000:   (0,         0),
30000:   (0,         0),
40000:   (0,         0),
50000:   (0,         0),
60000:   (0,         0),
80000:   (0,         0),
100000:  (0,         0),
120000:  (0,         0),
150000:  (0,         0),
200000:  (0,         0),
250000:  (0,         0),
300000:  (0,         0),
400000:  (0,         0),
500000:  (0,         0),
600000:  (0,         0),
800000:  (0,         0),
1000000: (0,         0),
2000000: (0,         0),
2000000: (0,         0)
}

mag1_neutral_beamtilt = {
2500:    (43393,     34122),
3000:    (43393,     34122),
4000:    (43393,     34122),
5000:    (43393,     34122),
6000:    (43393,     34122),
8000:    (43393,     34122),
10000:   (43393,     34122),
12000:   (43393,     34122),
15000:   (43393,     34122),
20000:   (43393,     34122),
25000:   (43393,     34122),
30000:   (43393,     34122),
40000:   (43393,     34122),
50000:   (43393,     34122),
60000:   (43393,     34122),
80000:   (43393,     34122),
100000:  (43393,     34122),
120000:  (43393,     34122),
150000:  (43393,     34122),
200000:  (43393,     34122),
250000:  (43393,     34122),
300000:  (43393,     34122),
400000:  (43393,     34122),
500000:  (43393,     34122),
600000:  (43393,     34122),
800000:  (43393,     34122),
1000000: (43393,     34122),
2000000: (43393,     34122)
}

mag1_neutral_imageshift = {
2500:    (33088,     33216),
3000:    (33088,     33216),
4000:    (33088,     33216),
5000:    (33088,     33216),
6000:    (33088,     33216),
8000:    (33088,     33216),
10000:   (33088,     33216),
12000:   (31808,     31296),
15000:   (31808,     31296),
20000:   (31808,     31296),
25000:   (31808,     31296),
30000:   (31808,     31296),
40000:   (32768,     32768),
50000:   (32768,     32768),
60000:   (32768,     32768),
80000:   (32768,     32768),
100000:  (32768,     32768),
120000:  (32768,     32768),
150000:  (32768,     32768),
200000:  (32768,     32768),
250000:  (32768,     32768),
300000:  (32768,     32768),
400000:  (32768,     32768),
500000:  (32768,     32768),
600000:  (32768,     32768),
800000:  (32768,     32768),
1000000: (32768,     32768),
2000000: (32768,     32768)
}

mag1_ol_standard_focus = {
2500:    1510565,
3000:    1510565,
4000:    1510565,
5000:    1510565,
6000:    1510565,
8000:    1510565,
10000:   1510565,
12000:   1513093,
15000:   1513093,
20000:   1513093,
25000:   1513093,
30000:   1513093,
40000:   1513093,
50000:   1513093,
60000:   1513093,
80000:   1513093,
100000:  1513093,
120000:  1513093,
150000:  1513093,
200000:  1513093,
250000:  1513093,
300000:  1513093,
400000:  1513093,
500000:  1513093,
600000:  1513093,
800000:  1513093,
1000000: 1511258,
2000000: 1511258
}

mag1_neutral_beamshift = {
2500:    (33872,     33360),
3000:    (33872,     33360),
4000:    (33872,     33360),
5000:    (33872,     33360),
6000:    (33872,     33360),
8000:    (33872,     33360),
10000:   (33872,     33360),
12000:   (33872,     33360),
15000:   (33872,     33360),
20000:   (33872,     33360),
25000:   (33872,     33360),
30000:   (33872,     33360),
40000:   (33872,     33360),
50000:   (33872,     33360),
60000:   (33872,     33360),
80000:   (33872,     33360),
100000:  (33872,     33360),
120000:  (33872,     33360),
150000:  (33872,     33360),
200000:  (33872,     33360),
250000:  (33872,     33360),
300000:  (33872,     33360),
400000:  (33872,     33360),
500000:  (33872,     33360),
600000:  (33872,     33360),
800000:  (33872,     33360),
1000000: (33872,     33360),
2000000: (33872,     33360)
}
