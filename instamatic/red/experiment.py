import os
import datetime
import logging
import numpy as np
import glob
import time
from instamatic.TEMController import config
from instamatic.formats import write_hdf5, read_hdf5
import tqdm
import numpy as np
from instamatic.tools import find_beam_center
from instamatic.processing.stretch_correction import apply_stretch_correction


mrc_header = b'\x04\x02\x00\x00\x04\x02\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x02\x00\x00\x04\x02\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb4B\x00\x00\xb4B\x00\x00\xb4B\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x888Fx\x06sA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00MAP DA\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00aaaaaaaaaaaaaaaaaaaaaa,aaaaaaaaaaa\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


def write_mrc(fn, img):
    with open(fn, "wb") as mrcf:
        # flip up/down because RED reads images from the bottom left corner
        img = np.flipud(img.astype(np.int16))

        mrcf.write(mrc_header)
        mrcf.write(img.tobytes())


def write_ED3D(path, fns, **kwargs):
    rotation_angle = kwargs.get("rotation_angle")
    wavelength = kwargs.get("wavelength")
    pixelsize = kwargs.get("pixelsize")
    osangle = kwargs.get("osangle")
    startangle = kwargs.get("startangle")
    endangle = kwargs.get("endangle")

    ed3d = open(os.path.join(path, "1.ed3d"), 'w')

    rotation_angle = np.degrees(rotation_angle)

    if startangle > endangle:
        sign = -1
    else:
        sign = 1

    ed3d.write("WAVELENGTH    {}\n".format(wavelength))
    ed3d.write("ROTATIONAXIS    {:.2f}\n".format(rotation_angle))
    ed3d.write("CCDPIXELSIZE    {}\n".format(pixelsize))
    ed3d.write("GONIOTILTSTEP    {}\n".format(osangle))
    ed3d.write("BEAMTILTSTEP    0\n")
    ed3d.write("BEAMTILTRANGE    0.000\n")
    ed3d.write("STRETCHINGMP    0.0\n")
    ed3d.write("STRETCHINGAZIMUTH    0.0\n")
    ed3d.write("\n")
    ed3d.write("FILELIST\n")
    
    for i, fn in enumerate(fns):
        ed3d.write("FILE {fn}    {ang:.2f}    0    {ang:.2f}\n".format(fn=fn, ang=startangle+sign*osangle*i))
    
    ed3d.write("ENDFILELIST")
    ed3d.close()


class Experiment(object):
    def __init__(self, ctrl, path=None, log=None, flatfield=None):
        super(Experiment,self).__init__()
        self.ctrl = ctrl
        self.path = path

        self.path_h5 = os.path.join(path, "hdf5")
        self.path_mrc = os.path.join(path, "mrc")

        if not os.path.exists(self.path_h5):
            os.makedirs(self.path_h5)
        if not os.path.exists(self.path_mrc):
            os.makedirs(self.path_mrc)

        self.logger = log
        self.camtype = ctrl.cam.name
        self.flatfield = flatfield
        self.offset = 0
        self.current_angle = None
        self.data_files = []
        
    def start_collection(self, expt, tilt_range, stepsize):
        path = self.path_h5

        if not os.path.exists(path):
            os.makedirs(path)
        
        self.logger.info("Data recording started at: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.logger.info("Data saving path: {}".format(path))
        self.logger.info("Data collection exposure time: {} s".format(expt))
        self.logger.info("Data collection spot size: {}".format(self.ctrl.spotsize))
        self.logger.info("Tilt range: {}".format(tilt_range))
        self.logger.info("Data collection step size: {}".format(stepsize))

        ctrl = self.ctrl

        if not self.current_angle:
            self.startangle = startangle = ctrl.stageposition.a
        else:
            startangle = self.current_angle + stepsize

        tilt_positions = np.arange(startangle, startangle+tilt_range, stepsize)
        print "\nStartangle", startangle
        # print "Angles:", tilt_positions

        data, headers = [], []

        image_mode = ctrl.mode
        if image_mode != "diff":
            fn = os.path.join(path, "image_{}.h5".format(self.offset))
            img, h = self.ctrl.getImage(expt)
            write_hdf5(fn, img, header=h)
            ctrl.mode_diffraction()

        ctrl.cam.block()
        # for i, a in enumerate(tilt_positions):
        for i, angle in enumerate(tqdm.tqdm(tilt_positions)):
            ctrl.stageposition.a = angle

            j = i + self.offset

            img, h = self.ctrl.getImage(expt)

            fn = os.path.join(path, "{:05d}.h5".format(j))

            write_hdf5(fn, img, header=h)

            self.data_files.append(fn)
            # print fn

        self.offset += len(tilt_positions)

        endangle = ctrl.stageposition.a

        ctrl.cam.unblock()

        self.camera_length = camera_length = int(self.ctrl.magnification.get())
        self.stepsize = stepsize

        with open(os.path.join(self.path, "summary.txt"), "a") as f:
            print >> f, "Data collected from {:.2f} degree to {:.2f} degree in {} frames.".format(startangle, endangle, len(tilt_positions))
            print "Data collected from {:.2f} degree to {:.2f} degree in {} frames.".format(startangle, endangle, len(tilt_positions))

        self.logger.info("Data collection camera length: {} mm".format(camera_length))
        self.logger.info("Data collected from {:.2f} degree to {:.2f} degree.".format(startangle, endangle))
        
        self.current_angle = angle
        print "Done, current angle = {:.2f} degrees".format(self.current_angle)

        if image_mode != "diff":
            ctrl.mode = image_mode

    def finalize(self):
        path = self.path_mrc
        fns = []

        azimuth   = -6.61
        amplitude =  2.43

        print "\nWriting MRC files"
        for fn in tqdm.tqdm(self.data_files):
            img, h = read_hdf5(fn)

            center = find_beam_center(img, sigma=10)
            new_img = apply_stretch_correction(img, center=center, azimuth=azimuth, amplitude=amplitude)

            basename = os.path.basename(fn)
            root, ext = os.path.splitext(basename)
            fn_mrc = basename.replace(ext, ".mrc")
            fns.append(fn_mrc)
            
            fp_mrc = os.path.join(path, fn_mrc)
            write_mrc(fp_mrc, new_img)

        rotation_angle = config.camera_rotation_vs_stage_xy
        pixelsize = config.diffraction_pixeldimensions[self.camera_length]

        write_ED3D(path, fns, rotation_angle=rotation_angle,
                            wavelength=0.0251,
                            pixelsize=pixelsize,
                            osangle=self.stepsize,
                            startangle=self.startangle,
                            endangle=self.current_angle)

        print "Writing ED3D file"
        print "RED data collection finalized"
