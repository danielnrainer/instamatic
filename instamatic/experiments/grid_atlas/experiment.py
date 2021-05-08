import datetime
import os
import time
from pathlib import Path

import numpy as np
from tqdm.auto import tqdm
from tkinter import messagebox

from instamatic import config
from instamatic.formats import write_tiff, read_tiff_header
from instamatic.experiments import TOMO

class Experiment:
    """Initialize data acquisition workflows for grid atlas.

    ctrl:
        Instance of instamatic.TEMController.TEMController
    path:
        `str` or `pathlib.Path` object giving the path to save data at
    log:
        Instance of `logging.Logger`
    flatfield:
        Path to flatfield correction image
    """
    def __init__(self, ctrl, path: str = None, log=None, flatfield=None):
        super().__init__()
        self.ctrl = ctrl

        try:
            self.path = Path(path)
        except:
            self.path = Path('.')
        self.logger = log
        self.flatfield = flatfield

        self.binsize = ctrl.cam.default_binsize
        self.software_binsize = config.settings.software_binsize

    def obtain_image(self, exposure_time, align, align_roi, roi):
        if align_roi:
            img, h = self.ctrl.get_image(exposure_time, align=align, roi=roi)
        else:
            img, h = self.ctrl.get_image(exposure_time, align=align)
        return img, h

    def collect_montage(self, exposure_time: float, align: bool, align_roi: bool, roi: list, blank_beam: bool, num_img: int, 
                        filepath: str, mag: int, image_scale: float, save_origin=True):
        gm = self.ctrl.grid_montage()
        current_pos = self.ctrl.stage.xy
        pos, px_center, stage_center = gm.setup(nx=num_img, ny=num_img, stage_shift=current_pos)
        gm.start(exposure_time=exposure_time, align=align, align_roi=align_roi, roi=roi, save=save_origin, blank_beam=blank_beam)
        m = gm.to_montage()
        m.calculate_montage_coords()
        #m.optimize_montage_coords()
        stitched = m.stitch()
        h = {}
        h['is_montage'] = True
        h['center_pos'] = current_pos
        h['mode'] = self.ctrl.mode.state
        h['magnification'] = mag
        h['ImageResolution'] = stitched.shape
        h['stage_matrix'] = self.ctrl.get_stagematrix() # normalized need to multiple pixelsize
        h['ImagePixelsize'] = image_scale
        write_tiff(filepath, stitched, header=h)
        self.ctrl.stage.xy = current_pos

    def from_whole_grid_list(self, whole_grid, grid_dir, sample_name: str, exposure_time: float, wait_interval: float, 
                        blank_beam: bool, num_img: int, align: bool, align_roi: bool, roi: list, defocus: int, stage_tilt: float):
        # go to the position at grid square level, find the eucentric height, take a montage
        no_square_img_df = whole_grid[whole_grid['img_location'].isna()]
        num = len(whole_grid) - len(no_square_img_df)
        state = self.ctrl.mode.state
        mag = self.ctrl.magnification.get()
        if self.software_binsize is None:
            image_scale = config.calibration[state]['pixelsize'][mag] * self.binsize #nm->um
        else:
            image_scale = config.calibration[state]['pixelsize'][mag] * self.binsize * self.software_binsize

        for index, point in no_square_img_df.iterrows():
            self.ctrl.stage.xy = point['pos_x'], point['pos_y']
            tomo_exp = TOMO.Experiment(ctrl=self.ctrl, log=self.logger, flatfield=self.flatfield)
            tomo_exp.start_auto_eucentric_height(exposure_time=exposure_time, wait_interval=wait_interval, align=align, 
                                    align_roi=align_roi, roi=roi, defocus=defocus, stage_tilt=stage_tilt, blank_beam=blank_beam, ask=False)
            square_dir = grid_dir / f"Sqaure_{num+1}"
            square_dir.mkdir(exist_ok=True, parents=True)
            filepath = square_dir / f'square_{sample_name}.tiff'
            self.collect_montage(exposure_time, align, align_roi, roi, blank_beam, num_img, filepath, mag, image_scale, save_origin=False)
            whole_grid.loc[index, 'pos_z'] = self.ctrl.stage.z
            whole_grid.loc[index, 'img_location'] = Path(square_dir.name) / f'square_{sample_name}.tiff'
            num += 1

    def from_grid_square_list(self, whole_grid, grid_square, grid_dir, pred_z, magnify: int, sample_name: str, blank_beam: bool,
                        exposure_time: float, wait_interval: float,  align: bool, align_roi: bool, roi: list, defocus: int):
        # go to the position at target level, predict the eucentric height, take an image
        square_img_df = whole_grid[whole_grid['img_location'].notna()]
        for index1, grid in square_img_df.iterrows():
            grid_num = grid['grid']
            square_img = grid['img_location']
            no_target_img_df = grid_square[(grid_square['grid']==grid_num) & (grid_square['img_location'].isna())]
            num = len(grid_square[grid_square['grid']==grid_num]) - len(no_target_img_df)

            header = read_tiff_header(grid_dir/square_img)
            square_img_shape = np.array(header['ImageResolution'])
            stage_matrix = np.array(header['stage_matrix'])
            square_img_pixel = header['ImagePixelsize']
            square_stage_center = np.array(header['center_pos'])
            square_pixel_center = square_img_shape / 2
            target_pixelsize = square_img_pixel / magnify
            state = self.ctrl.mode.state
            mag = self.ctrl.magnification.get()
            rec = None
            for magnification, pixelsize in config.calibration[state]['pixelsize'].items():
                difference = abs(pixelsize - target_pixelsize)
                if rec is None:
                    rec = difference
                    continue
                if difference < rec:
                    rec = difference
                else:
                    target_magnification = magnification
                    target_pixelsize = pixelsize
                    print(f'Target mag: {target_magnification}')
                    break

            for index2, point in no_target_img_df.iterrows(): 
                self.ctrl.stage.xy = point['pos_x'], point['pos_y']
                time.sleep(wait_interval)
                current_pos = self.ctrl.stage.xy
                arr, h = self.obtain_image(exposure_time, align, align_roi, roi)
                h['is_montage'] = False
                h['center_pos'] = current_pos
                h['mode'] = state
                h['magnification'] = mag
                h['stage_matrix'] = self.ctrl.get_stagematrix() # normalized need to multiple pixelsize
                target_dir = grid_dir / Path(grid['img_location']).parent / f"Target_{num+1}"
                target_dir.mkdir(exist_ok=True, parents=True)
                filepath = target_dir / f'target_{sample_name}.tiff'
                write_tiff(filepath, arr, header=h)
                if pred_z is None:
                    grid_square.loc[index2, 'pos_z'] = self.ctrl.stage.z
                else:
                    grid_square.loc[index2, 'pos_z'] = pred_z(current_pos)
                grid_square.loc[index2, 'img_location'] = Path(target_dir.parent.name) / Path(target_dir.name) / f'target_{sample_name}.tiff'
                num += 1

    def from_target_list(self, target, exposure_time: float, wait_interval: float, align: bool, align_roi: bool, roi: list):
        # In diffraction mode, use beam shift to each crystal location and collection diffraction pattern.
        for index, point in target.iterrows(): 
            pass 