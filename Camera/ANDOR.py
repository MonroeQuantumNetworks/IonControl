#!/usr/bin/python
# -*- coding: latin-1 -*-
"""High level interface to Andor iXon+ emCCD camera."""

import numpy
from ctypes import *
from time import *
import time
import os

dllpath = os.path.join(os.path.dirname(__file__), '..', 'Camera/atmcd64d')
# print(dllpath)
windll.LoadLibrary(dllpath)


# hack to releas GIL during wait
# MVll = ctypes.windll.mvDeviceManager
# llWait = MVll.DMR_ImageRequestWaitFor
# llWait.argtypes = [ctypes.c_int,
# ctypes.c_int,
# ctypes.c_int,
# ctypes.POINTER(ctypes.c_int)]
# llWait.restype = ctypes.c_int


class CamTimeoutError(Exception):
    def __init__(self):
        super(CamTimeoutError, self).__init__(self, 'Timeout')


class TimeoutError(Exception):
    def __init__(self):
        Exception.__init__(self, 'Timeout')


class Cam(object):

    def __init__(self):
        self.andormode = 'Live'
        self.width = 0
        self.height = 0
        self.numberandorimages = 0
        windll.atmcd64d.Initialize(".")
        camsn = c_long()
        windll.atmcd64d.GetCameraSerialNumber(byref(camsn))
        if camsn.value == 0:
            self.error = True
            print("Andor not available Cam")
        else:
            self.error = False
            print("Andor initialized")
            print('Andor camera s/n:', camsn.value)

    def open(self):
        print('Andor open')
        windll.atmcd64d.SetTriggerMode(1)  # 1=external, 0=internal
        windll.atmcd64d.SetReadMode(4)  # read images
        windll.atmcd64d.SetShutter(1, 1, 1000, 1000)  # Shutter open
        return self

    def close(self):
        print('Andor close')

    def shutdown(self):
        windll.atmcd64d.ShutDown()
        print('Andor shutdown')

    def stop(self):
        print('Andor stop')
        windll.atmcd64d.AbortAcquisition()
        windll.atmcd64d.SetShutter(1, 0, 1000, 1000)

    def gettemperature(self):
        """Get temperature of CCD"""
        temperature = c_float()
        windll.atmcd64d.GetTemperatureF(byref(temperature))
        return temperature.value

    def wait(self, timeout = 10):
        """Check if new image is available, and waits for specified time. Raises CamTimeoutError if no new image
        available."""

        time.sleep(timeout)  # --------------------------------#
        status = c_int()
        currentnumberimages = c_int()
        windll.atmcd64d.GetTotalNumberImagesAcquired(byref(currentnumberimages))
        print("currentnumberimages = ", currentnumberimages.value)

        if self.andormode == 'Live' or self.andormode == 'AutoLoad':
            if currentnumberimages.value != self.numberandorimages:
                print('Image #', currentnumberimages.value)
                self.numberandorimages = currentnumberimages.value
            else:
                raise CamTimeoutError
        if self.andormode == 'TriggeredAcquisition_1':
            windll.atmcd64d.GetStatus(byref(status))
            print("status = ", status.value)
            if status.value == 20073:
                self.numberandorimages = currentnumberimages.value
            else:
                raise CamTimeoutError

    def start_cooling(self, setPoint = -60):
        tmin = c_int()
        tmax = c_int()
        windll.atmcd64d.GetTemperatureRange(byref(tmin), byref(tmax))
        # windll.atmcd64d.SetTemperature(tmin.value)
        windll.atmcd64d.SetTemperature(setPoint)
        windll.atmcd64d.CoolerON()
        print("Andor start cooling")
        # print('  set min temp = ', tmin.value)
        print('  set min temp = ', setPoint)

    def stop_cooling(self):
        windll.atmcd64d.CoolerOFF()
        print("Andor stop cooling")
        print("temp = ", self.gettemperature())

    def frame_height(self):
        xsize = c_long()
        ysize = c_long()
        windll.atmcd64d.GetDetector(byref(xsize), byref(ysize))
        return ysize.value

    def frame_width(self):
        xsize = c_long()
        ysize = c_long()
        windll.atmcd64d.GetDetector(byref(xsize), byref(ysize))
        return xsize.value

    def set_timing(self, integration = 100, repetition = 0, ampgain = 0, emgain = 0, numExp = 1, numScan = 1):
        print('Andor Imaging mode: ', self.andormode)
        fakeim = 0
        # ==============================In normal operation set fakeim=0, just for debugging====================================

        # 0 internal 1 external 7 external exposure 10 software trigger
        self.width = self.frame_width() + fakeim
        self.height = self.frame_height() + fakeim
        triggerMode = None
        acquisitionMode = None

        repetition = 0

        if self.andormode == 'FastKinetics':
            print('Setting camera parameters for fast kinetics.')
            # self.width = self.frame_width() + fakeim
            # self.height = self.frame_height() + fakeim
            # windll.atmcd64d.SetAcquisitionMode(4)  # 1 single mode 2 accumulate mode 5 run till abort
            # windll.atmcd64d.SetFastKinetics(501,2,c_float(3.0e-3),4,1,1)
            acquisitionMode = 4
            triggerMode = 0
            hBin = 1
            vBin = 1
            hTrim = 0
            vTrim = 0
            windll.atmcd64d.SetFastKinetics(501, 2, c_float(integration * 1.0e-3), 4, 1, 1)
        elif self.andormode == 'Live' or self.andormode == 'AutoLoad':
            print('Setting camera parameters for live mode.')
            # self.width = self.frame_width() + fakeim
            # self.height = self.frame_height() + fakeim
            # windll.atmcd64d.SetAcquisitionMode(5)  # 1 single mode 2 accumulate mode 5 run till abort
            acquisitionMode = 5
            triggerMode = 0
            # acquisitionMode = 5
            # triggerMode = 1
            hBin = 1
            vBin = 1
            hTrim = 0
            vTrim = 0
        elif self.andormode == 'TriggeredAcquisition' or self.andormode == 'Calibrate':
            print('Setting camera parameters for Triggered Acquisition mode')
            # self.width = self.frame_width() + fakeim
            # self.height = self.frame_height() + fakeim
            # windll.atmcd64d.SetAcquisitionMode(5)  # 1 single mode 2 accumulate mode 5 run till abort
            if self.andormode == 'TriggeredAcquisition':
                acquisitionMode = 5
                triggerMode = 7
            else:
                acquisitionMode = 3
                triggerMode = 0
                windll.atmcd64d.SetNumberKinetics(3)
            # triggerMode = 7
            hBin = 1
            vBin = 8
            hTrim = 0
            vTrim = 448
            # print('Set FTCCD Code:', windll.atmcd64d.SetFrameTransferMode(1))

            # numVS = c_int()
            # numHS = c_int()
            # windll.atmcd64d.GetNumberVSSpeeds(byref(numVS))
            # windll.atmcd64d.GetNumberHSSpeeds(byref(numHS))
            # print('Speeds:', numVS.value, numHS.value)
            windll.atmcd64d.SetVSSpeed(0)
            # VS = c_int()
            # HS = c_int()
            # windll.atmcd64d.GetNumberVSSpeeds(byref(VS))
            # windll.atmcd64d.GetNumberHSSpeeds(byref(HS))
            # print('  VS:', VS.value, '\n  HS:', HS.value)
            # windll.atmcd64d.SetNumberKinetics(numExp * numScan)
        else:
            acquisitionMode = 5
            triggerMode = 0

        print('Andor set timings:')
        print('  set exposure time =', integration, 'ms')
        print('  set repetition time =', repetition, 'ms')

        # if self.andormode != 'Live':
        #     if repetition != 0:
        #         print("rep = ", repetition, " and Trigger is Internal")
        #         windll.atmcd64d.SetTriggerMode(0)  # 0 internal 1 external 10 software trigger
        #         windll.atmcd64d.SetExposureTime(c_float(integration * 1.0e-3))
        #         windll.atmcd64d.SetKineticCycleTime(c_float(repetition * 1.0e-3))  # check *******
        #     else:
        #         if integration != 0:
        #             windll.atmcd64d.SetTriggerMode(1)  # 0 internal 1 external 7 external exposure 10 software trigger
        #             windll.atmcd64d.SetExposureTime(c_float(integration * 1.0e-3))
        #             windll.atmcd64d.SetKineticCycleTime(0)  # check *******
        #         else:
        #             windll.atmcd64d.SetTriggerMode(7)  # 0 internal 1 external 7 external exposure 10 software trigger
        #             windll.atmcd64d.SetExposureTime(c_float(integration * 1.0e-3))
        #             windll.atmcd64d.SetKineticCycleTime(0)  # check *******
        # else:
        #     triggerMode = ('Internal', 0)

        cExp = c_float(integration * 1.0e-3)
        cKCT = c_float(repetition * 1.0e-3)
        print(cExp, cKCT)

        windll.atmcd64d.SetTriggerMode(triggerMode)
        windll.atmcd64d.SetAcquisitionMode(acquisitionMode)
        windll.atmcd64d.SetExposureTime(cExp)
        windll.atmcd64d.SetKineticCycleTime(cKCT)  # check *******

        # if self.andormode == 'absorptionfast':
        #     windll.atmcd64d.SetAcquisitionMode(4)  # 1 single mode 2 accumulate mode 5 run till abort
        #     windll.atmcd64d.SetTriggerMode(6)  # 0 internal 1 external 10 software trigger

        # windll.atmcd64d.SetNumberAccumulation(repetition)
        # windll.atmcd64d.SetAccumulationCycleTime(1)   # check *******

        print('SetImg Code:', windll.atmcd64d.SetImage(hBin, vBin,
                                                       1 , self.width - hTrim,
                                                       1 , self.height - vTrim))
        self.effWidth = int((self.width - (hTrim))/hBin)
        self.effHeight = int((self.height - (vTrim))/vBin)
        # self.effHeight = 8

        # print('SetCrop Code:', windll.atmcd64d.SetIsolatedCropMode(1, 64, 512, 8, 1))
        # print('SetCrop Code:', windll.atmcd64d.SetIsolatedCropModeEx(1, 64, 496, 8, 1, 224, 8))
        # self.effHeight = int(self.height/64)
        # self.effWidth = 496

        readexposure = c_float()
        readaccumulate = c_float()
        readkinetic = c_float()
        readouttime = c_float()
        windll.atmcd64d.GetAcquisitionTimings(byref(readexposure), byref(readaccumulate), byref(readkinetic))
        print('ReadOut Code:', windll.atmcd64d.GetReadOutTime(byref(readouttime)))

        print('Andor read timings:')
        print('  read exposure time =', readexposure.value * 1000, 'ms')
        print('  read accumulate time =', readaccumulate.value * 1000, 'ms')
        print('  read kinetic time =', readkinetic.value * 1000, 'ms')
        print('  read readoutMax time =', readouttime.value * 1000, 'ms')
        print('Andor image size:', self.effWidth, 'x', self.effHeight)

        gainvalue = c_float()
        windll.atmcd64d.GetPreAmpGain(ampgain, byref(gainvalue))
        print('Andor preamp gain #%d' % ampgain, '=', gainvalue.value)
        windll.atmcd64d.SetPreAmpGain(ampgain)

        print('Andor EM gain =', emgain)
        windll.atmcd64d.SetEMGainMode(0)  # accept values 0-255
        windll.atmcd64d.SetEMCCDGain(emgain)  # accept values 0-255

    def start_acquisition(self):
        windll.atmcd64d.StartAcquisition()
        self.numberandorimages = 0

    def get_status(self):
        numImg = c_long()
        windll.atmcd64d.GetTotalNumberImagesAcquired(byref(numImg))
        return str((windll.atmcd64d.GetStatus(),
                   numImg.value))

    def get_num_newImgs(self):
        startIdx = c_long()
        stopIdx = c_long()
        windll.atmcd64d.GetNumberNewImages(startIdx, stopIdx)
        value = stopIdx.value - startIdx.value
        return value

    def roidata(self):
        starttime = time.time()

        if self.andormode == 'Live' or self.andormode == 'AutoLoad':
            print('Retrieving image: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            windll.atmcd64d.GetMostRecentImage(img, c_long(self.effWidth * self.effHeight))
            # windll.atmcd64d.GetOldestImage(img, c_long(self.effWidth * self.effHeight))
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
        elif self.andormode == 'TriggeredAcquisition':
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            valid = windll.atmcd64d.GetOldestImage(img, c_long(self.effWidth * self.effHeight))
            if valid == 20024: raise CamTimeoutError
            print('Retrieving image: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
        elif self.andormode == 'Calibrate':
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            valid = windll.atmcd64d.GetOldestImage(img, c_long(self.effWidth * self.effHeight))
            if valid == 20024: raise CamTimeoutError
            print('Retrieving image: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
        elif self.andormode == 'FastKinetics':
            print('Retrieving images: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            windll.atmcd64d.GetAcquiredData(img, c_long(self.effWidth * self.effHeight))
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
            windll.atmcd64d.StartAcquisition()

        endtime = time.time()
        print('  readout time = ', endtime - starttime, ' s')
        # self.imgoutRandModifier(imgout) # TODO: Remove when images are produced.
        return imgout

    def imgoutRandModifier(self, imgout):

        effHeight, effWidth = imgout.shape[0], imgout.shape[1]
        for i in range(effHeight):
            for j in range(effWidth):
                imgout[i][j] = imgout[i][j] + numpy.random.randint(0, 2)

                # if __name__ == '__main__':
                # cam = Cam()
                # cam.open()
                # cam.start_cooling()
                # print(cam.gettemperature())
                # time.sleep(5)
                # print(cam.gettemperature())
                # cam.wait()
                # img = cam.roidata()
                # print()
                # cam.close()
