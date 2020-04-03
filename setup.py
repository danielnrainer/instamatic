# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'readme.rst')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')


setup(
    long_description=readme,
    name='instamatic',
    version='1.1.0',
    description='Python program for automated electron diffraction data collection',
    python_requires='>=3.6',
    project_urls={
        'documentation': 'http://github.com/stefsmeets/instamatic',
        'homepage': 'http://github.com/stefsmeets/instamatic',
        'repository': 'http://github.com/stefsmeets/instamatic'},
    author='Stef Smeets',
    author_email='s.smeets@tudelft.nl',
    license='GPL-3.0-only',
    keywords='electron-crystallography electron-microscopy electron-diffraction serial-crystallography 3D-electron-diffraction micro-ed data-collection automation',
    classifiers=[
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Operating System :: Microsoft :: Windows',
            'Topic :: Scientific/Engineering :: Human Machine Interfaces',
            'Topic :: Scientific/Engineering :: Chemistry',
            'Topic :: Software Development :: Libraries'],
    entry_points={
        'console_scripts': [
            'instamatic = instamatic.main:main',
            'instamatic.controller = instamatic.TEMController.TEMController:main_entry',
            'instamatic.serialed = instamatic.experiments.serialed.experiment:main',
            'instamatic.camera = instamatic.camera.camera:main_entry',
            'instamatic.calibrate_stage_lowmag = instamatic.calibrate.calibrate_stage_lowmag:main_entry',
            'instamatic.calibrate_stage_mag1 = instamatic.calibrate.calibrate_stage_mag1:main_entry',
            'instamatic.calibrate_beamshift = instamatic.calibrate.calibrate_beamshift:main_entry',
            'instamatic.calibrate_directbeam = instamatic.calibrate.calibrate_directbeam:main_entry',
            'instamatic.flatfield = instamatic.processing.flatfield:main_entry',
            'instamatic.stretch_correction = instamatic.processing.stretch_correction:main_entry',
            'instamatic.browser = scripts.browser:main',
            'instamatic.viewer = scripts.viewer:main',
            'instamatic.defocus_helper = instamatic.gui.defocus_button:main',
            'instamatic.find_crystals = instamatic.processing.find_crystals:main_entry',
            'instamatic.learn = scripts.learn:main_entry',
            'instamatic.temserver = instamatic.server.tem_server:main',
            'instamatic.camserver = instamatic.server.cam_server:main',
            'instamatic.dialsserver = instamatic.server.dials_server:main',
            'instamatic.VMserver = instamatic.server.vm_ubuntu_server:main',
            'instamatic.xdsserver = instamatic.server.xds_server:main',
            'instamatic.temserver_fei = instamatic.server.TEMServer_FEI:main',
            'instamatic.goniotoolserver = instamatic.server.goniotool_server:main',
            'instamatic.autoconfig = instamatic.config.autoconfig:main']},
    packages=[
        'instamatic',
        'instamatic.TEMController',
        'instamatic.calibrate',
        'instamatic.camera',
        'instamatic.config',
        'instamatic.experiments',
        'instamatic.experiments.autocred',
        'instamatic.experiments.cred',
        'instamatic.experiments.cred_gatan',
        'instamatic.experiments.cred_tvips',
        'instamatic.experiments.red',
        'instamatic.experiments.serialed',
        'instamatic.formats',
        'instamatic.gui',
        'instamatic.neural_network',
        'instamatic.processing',
        'instamatic.server',
        'instamatic.utils'],
    package_dir={
        '': '.'},
    package_data={
        'instamatic.camera': [
            '*.dll',
            '*.h',
            '*.lockfile',
            'tpx/*.bpc',
            'tpx/*.dacs',
            'tpx/*.txt'],
        'instamatic.config': [
            '*.yaml',
            'alignments/*.yaml',
            'calibration/*.yaml',
            'camera/*.yaml',
            'microscope/*.yaml',
            'scripts/*.md'],
        'instamatic.neural_network': ['*.p']},
    install_requires=[
        'comtypes>=1.1.7',
        'h5py>=2.10.0',
        'ipython>=7.11.1',
        'lmfit>=1.0.0',
        'matplotlib>=3.1.2',
        'mrcfile>=1.1.2',
        'numpy>=1.17.3',
        'pandas>=0.25.3',
        'pillow>=7.0.0',
        'pywinauto>=0.6.8',
        'pyyaml>=5.3',
        'scikit-image>=0.16.2',
        'scipy>=1.3.2',
        'tifffile>=2019.7.26.2',
        'tqdm>=4.41.1',
        'virtualbox>=2.0.0'],
    extras_require={
        'dev': [
            'check-manifest',
            'pre-commit']},
)
