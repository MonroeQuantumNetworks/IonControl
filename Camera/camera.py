# *****************************************************************
# IonControl:  Copyright 2016 Sandia Corporation
# This Software is released under the GPL license detailed
# in the file "license.txt" in the top-level IonControl directory
# *****************************************************************
"""
Camera.py acquire images live or subjected to an external trigger and displays them.
"""

import os
import os.path
import queue
from multiprocessing import Queue
import threading
import time
from contextlib import closing

import PyQt5
import numpy
from PyQt5 import QtCore, QtGui
from pyqtgraph import ImageView, ColorMap

from Camera import AndorShutdown
from Camera import CameraSettings
from Camera import TemperatureMonitor
from Camera import fileSettings
from Camera import readImage
from Camera import IonDetect
from modules import enum
import logging

uipath = os.path.join(os.path.dirname(__file__), '..', 'ui/Camera.ui')
CameraForm, CameraBase = PyQt5.uic.loadUiType(uipath)

# try:
#     import ANDOR
#     camandor = ANDOR.Cam()
#     useAndor = not camandor.error
# except ImportError:
#     useAndor = False
#     print ("Andor not available.")

from Camera.ANDOR import Cam, CamTimeoutError

camandor = Cam()
useAndor = True
lock = threading.Lock()


class AndorTemperatureThread(threading.Thread):  # Class added
    """This Thread monitor the Andor Temperature and displays it in the Status Bar"""

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app
        self.app.temperUi.setInitTemp(camandor.gettemperature(), -60)
        # self.currTemp = camandor.gettemperature()
        # self.prevTemp = camandor.gettemperature()
        # self.tempRate = 0
        self.refreshRate = 0.5
        self.running = True

    def run(self):
        global andortemp
        andortemp = True
        self.app.statusBar().showMessage("Cooling")
        while andortemp and self.running:
            time.sleep(self.refreshRate)
            self.app.temperUi.updateTemp(camandor.gettemperature())
        self.stop()
        # self.prevTemp = self.currTemp
        # self.currTemp = camandor.gettemperature()
        # self.tempRate = 60 * (self.currTemp - self.prevTemp)/self.refreshRate
        # self.app.temperatureValue.setText("Temp = %.1f °C" % self.currTemp)
        # self.app.temperatureRate.setText("TempRate = %.1f °C/min" % self.tempRate)
        # self.app.statusBar().showMessage("Temp = %.1f °C" % camandor.gettemperature())
        # self.app.statusBar().showMessage("T = %.1f °C" %time.time())
        # print(self.camandor.gettemperature())

    def stop(self):
        global andortemp
        andortemp = False
        self.app.statusBar().showMessage("Not Cooling")
        while camandor.gettemperature() < 0:
            time.sleep(self.refreshRate)
            self.app.temperUi.updateTemp(camandor.gettemperature())
            # self.prevTemp = self.currTemp
            # self.currTemp = camandor.gettemperature()
            # self.tempRate = 60 * (self.currTemp - self.prevTemp) / self.refreshRate
            # self.app.temperatureValue.setText("Temp = %.1f °C" % self.currTemp)
            # self.app.temperatureRate.setText("TempRate = %.1f °C/min" % self.tempRate)
            # self.app.statusBar().showMessage("Temp = %.1f °C" % camandor.gettemperature())
            # self.app.statusBar().showMessage("T = %.1f °C" %time.time())
            # print(self.camandor.gettemperature())


class AndorProperties(object):
    def __init__(self, ampgain = 0, emgain = 0):
        self._ampgain = ampgain
        self._emgain = emgain

    def get_ampgain(self):
        return self._ampgain

    def set_ampgain(self, value):
        self._ampgain = value

    ampgain = property(get_ampgain, set_ampgain)

    def get_emgain(self):
        return self._emgain

    def set_emgain(self, value):
        self._emgain = value


class CamTiming(object):
    def __init__(self, exposure, repetition = None, live = True):
        self._exposure = exposure
        self._repetition = repetition
        self._live = live

    def get_exposure(self):
        if self._live:
            return self._exposure
        else:
            if useAndor:  # change this when you test it
                return self._exposure
            else:
                return 0

    def set_exposure(self, value):
        self._exposure = value

    exposure = property(get_exposure, set_exposure)

    def get_repetition(self):
        if self._live:
            return self._repetition
        else:
            if useAndor:
                return self._exposure
            else:
                return 0

    def set_repetition(self, value):
        self._repetition = value

    repetition = property(get_repetition, set_repetition)

    def get_live(self):
        return self._live

    def set_live(self, value = True):
        self._live = bool(value)

    live = property(get_live, set_live)

    def get_external(self):
        return not self.live

    def set_external(self, value):
        self.live = not value

    external = property(get_external, set_external)


# ACQUIRE THREADS

class AcquireThread(threading.Thread):
    """Base class for image acquisition threads."""

    def __init__(self, app, cam, queue):
        threading.Thread.__init__(self, name = "ImageProducerThread")
        self.app = app
        self.cam = cam
        self.queue = queue

        self.running = False
        self.nr = 0
        # self.scanx = None

    def run(self):
        pass

    def message(self, msg):
        # wx.PostEvent(self.app, StatusMessageEvent(data=msg))
        self.app.statusBar().showMessage(str(msg))

    def stop(self):
        global andortemp
        andortemp = True  # understand what the Temperature dependence has to do here
        self.running = False
        # try:
        self.cam.stop()
        # if not andortemp:
        #     AndorTemperatureThread(self.app).start()

    def adjust_timing(self):
        """Adjust camera timing based on current parameters."""
        # set exposure times
        # if str(self.app.CameraParameters['Exposure time'].value.u) == 'us':
        #     exp = self.app.CameraParameters['Exposure time'].value.magnitude * 0.001
        # elif str(self.app.CameraParameters['Exposure time'].value.u) == 'ms':
        #     exp = self.app.CameraParameters['Exposure time'].value.magnitude
        # else:
        #     exp = self.app.CameraParameters['Exposure time'].value.magnitude * 1000

        exp = self.app.parHand.getParam('Exposure time')
        self.app.timing_andor.set_exposure(exp)

        # set timing settings
        if not self.app.timing_andor.get_external():
            self.cam.set_timing(integration = exp, repetition = 0, ampgain = self.app.properties_andor.get_ampgain(),
                                emgain = int(self.app.CameraParameters['EMGain'].value),
                                numExp = int(self.app.CameraParameters['experiments'].value),
                                numScan = len(self.app.ScanList))
        else:
            # AndorTemperatureThread(self.app).stop()
            self.cam.set_timing(integration = exp, repetition = self.app.timing_andor.repetition,
                                ampgain = self.app.properties_andor.get_ampgain(),
                                emgain = int(self.app.CameraParameters['EMGain'].value),
                                numExp = int(self.app.CameraParameters['experiments'].value),
                                numScan = len(self.app.ScanList))

    def check_overexposure(self, img, threshold = 10000):
        avgCounts = numpy.average(img)
        if avgCounts > threshold:
            self.stop()
            print('Camera Overexposed! Acquisition Aborted!')




class AcquireThreadAndorLive(AcquireThread):
    # TODO: Acquire Thread for live mode, check that everything is working.
    def run(self):
        self.running = True
        print(self.name, 'Mode: ', camandor.andormode)
        with closing(self.cam.open()):
            self.adjust_timing()
            exp = 0.2
            self.cam.start_acquisition()  # let's comment this out, we will introduce the live afterwards

            while self.running:
                try:
                    self.cam.wait(exp)
                    # time.sleep(0.1)
                    # time.sleep(exp)
                    # print('Status:', self.cam.get_status())
                    self.message('Live Running')
                except CamTimeoutError:
                    # print("Timeout!")
                    self.message('No Images')
                else:
                    lock.acquire()
                    try:
                        img = self.cam.roidata()
                        print(img)
                        # img = img.astype(numpy.float32)
                    finally:
                        lock.release()
                    self.app.displayImage(img)
                    # self.queue.put((self.nr, img))  # TODO: ????
                    # print(self.name, "Enqueue")

            # put empty image to queue
            # self.queue.put((- 1, None))

        # print('NumNewImg:', self.cam.get_num_newImgs())
        self.nr = 0
        self.message('')
        print(self.name, "Exiting")


class AcquireThreadAndor(AcquireThread):

    def run(self):
        self.running = True
        self.nr = 0
        # self.scanx = None
        print(self.name, 'Mode: ', camandor.andormode)
        with closing(self.cam.open()):
            self.adjust_timing()
            # exp = self.app.timing_andor.get_exposure()
            exp = 0.5
            self.cam.start_acquisition()
            imgAcq = 0
            timeoutCount = 0
            # self.cam.start_live_acquisition()# let's comment this out, we will introduce the live afterwards

            while self.running:
                img = None
                if timeoutCount/exp > 10:
                    break
                try:
                    # self.cam.wait(exp)
                    # time.sleep(0.1)
                    img = self.cam.roidata()
                except CamTimeoutError:
                    time.sleep(exp)
                    # print("Timeout!")
                    timeoutCount += 1
                else:
                    timeoutCount = 0
                    print(img)
                    self.nr += 1
                    if self.nr > self.app.CameraParameters['experiments'].value:
                        self.nr = 1
                    self.queue.put((self.nr, img.astype(numpy.float32)))  # TODO: ????
                    # print(self.name, "Enqueue")
                    # print("--------Acquiringthread--------")
                    # print("Current x Scan value = ", self.scanx)
                    # print("Just Acquired an img and put it in the queue:")
                    # print(img)


            # put empty image to queue
            self.queue.put((- 1, None))

        self.nr = 0
        print(self.name, "Exiting")


class AcquireThreadAndorCalibrate(AcquireThread):

    def run(self):
        self.running = True
        print(self.name, 'Mode: ', camandor.andormode)
        with closing(self.cam.open()):
            self.adjust_timing()
            exp = 0.5
            self.cam.start_acquisition()

            while self.running:
                try:
                    img = self.cam.roidata()
                except CamTimeoutError:
                    time.sleep(exp)
                else:
                    print(img)
                    self.nr += 1
                    self.queue.put((self.nr, img.astype(numpy.float32)))  # TODO: ????
                    if self.nr == 3:
                        self.running = False

            # put empty image to queue
            self.queue.put((- 1, None))

        self.nr = 0
        print(self.name, "Exiting")


class AcquireThreadAndorAutoLoad(AcquireThread):

    def run(self):
        self.curNumOfIons = 0
        self.detector = IonDetect.IonDetection(None, numIons = self.curNumOfIons)
        self.running = True
        print(self.name, 'Mode: ', camandor.andormode)
        with closing(self.cam.open()):
            self.adjust_timing()
            exp = 0.5
            self.cam.start_acquisition()

            while self.running:
                try:
                    img = self.cam.roidata()
                except CamTimeoutError:
                    time.sleep(exp)
                else:
                    print(img)
                    self.detector.set_arr(img)
                    self.curNumOfIons = self.detector.countIons(minSig = 1, maxSig = 6)

            # put empty image to queue

        print(self.name, "Exiting")


# CONSUMER THREADS

class ConsumerThread(threading.Thread):
    def __init__(self, app, queue):
        threading.Thread.__init__(self, name = "ImageConsumerThread")
        self.queue = queue
        self.app = app
        self.running = False
        self.scanList = None

    def run(self):
        pass

    def get_image(self, timeout = 1):
        """get image from queue, skip empty images (nr<0)"""
        nr = - 1
        while nr < 0:
            nr, img = self.queue.get(block = True, timeout = timeout)
        return nr, img

    def message(self, msg):
        """Displays message on status bar."""
        # wx.PostEvent(self.app, StatusMessageEvent(data=msg))
        self.app.statusBar().showMessage(str(msg))

    def save_abs_img(self, filename, img):
        """Saves absorption images"""
        rawimg = (1000 * (img + 1)).astype(numpy.uint16)
        readImage.write_raw_image(filename, rawimg, False)
        self.message('Saving Image')

    def save_raw_img(self, filename, img):
        """Saves Raw images"""
        rawimg = img.astype(numpy.uint16)
        readImage.write_raw_image(filename, rawimg, True)
        self.message('S')

    def saveimage(self, dir, img):
        imagesavedir = dir
        imagesavefilename = "%s%s%s.sis" % (time.strftime("%Y%m%d%H%M%S"), "-ScanName", "-Image-number")
        imagesavefilenamefull = os.path.normpath(os.path.join(imagesavedir, imagesavefilename))
        rawimg = img.astype(numpy.uint16)
        readImage.write_raw_image(imagesavefilenamefull, rawimg, False)

    def saveimage_nr(self, dir, img, nr, scanx, text, scanName = 'untitledScan'):
        imagesavesubdir = '%s/%s/%s/%s' % (time.strftime("%Y"), time.strftime("%Y_%m"), time.strftime("%Y_%m_%d"), scanName)
        imagesavedir = os.path.join(dir, imagesavesubdir)
        imagesavefilename = "%s%s%s%s.sis" % (time.strftime("%Y%m%d%H%M%S"), '-'+str(scanx), "-NExperiments", str(nr))
        imagesavefilenamefull = os.path.normpath(os.path.join(imagesavedir, imagesavefilename))
        # print('Path Exists?', os.path.exists(imagesavedir))
        if not os.path.exists(imagesavedir):
            os.makedirs(imagesavedir)
            # print('Path Exists?', os.path.exists(imagesavedir))
        # rawimg = img.astype(numpy.uint16)
        s = str(text)
        readImage.write_raw_imagearrays(imagesavefilenamefull, img, nr, s)
        print(imagesavedir, imagesavefilenamefull)

    def getImageROICounts(self, img):
        if self.app.calibratedROI is not None:
            roicounts = []
            for ion in self.app.calibratedROI.IonDict:
                roi = self.app.calibratedROI.IonDict[ion]
                curIonCount = []
                for x in range(roi.leftBound + 1, roi.rightBound):
                    for y in range(roi.upBound + 1, roi.lowBound):
                        curIonCount.append(img[x][y])
                count = numpy.average(curIonCount)
                roicounts.append(count)
            return roicounts
        raise Exception('No ROI Calibrated')
        # roicounts = []
        # for i in range(0, 10):
        #     roicounts.append(numpy.random._rand_int16)
        # return roicounts

    def stop(self):
        self.running = False

        # TODO: empty queue


class ConsumerThreadAndorLive(ConsumerThread):

    def run(self):
        pass
    #     self.running = True
    #     print(self.name, "Started")
    #     while self.running:
    #         try:
    #             nr, img = self.queue.get(timeout = 10)
    #             print(self.name, "Dequeue")
    #             # self.message('ok')
    #             # print camandor.gettemperature()
    #
    #         except queue.Empty:
    #             self.message('No Images')
    #
    #         else:
    #             self.app.displayImage(img)
    #             print(self.name, "ImageDisplayed")
    #             self.message('Live Running')
    #             # if nr > 0:
    #             # wx.PostEvent(self.app, AndorSingleImageAcquiredEvent(imgnr=nr, img=img))"find a new function"
    #             # self.message('I')
    #
    #     self.message('')
    #     print(self.name, "Exiting")


class ConsumerThreadAndorFast(ConsumerThread):
    """Acquire three images, calculate absorption image, save to file, display"""

    def run(self):
        self.running = True
        # print "-----------------------"
        while self.running:
            try:
                nr1, img1 = self.get_image(timeout = 5)
                self.message('1')
                if not self.running: break
                print("image ok")
                nr2, img2 = self.get_image(timeout = 5)
                self.message('2')
                if not self.running: break
                print("image ok")

            except queue.Empty:
                self.message(None)
                self.message('W')

            else:
                # calculate absorption image
                # img = - (np.log(img1 - img3) - np.log(img2 - img3))
                h, w = img1.shape
                img = + (numpy.log(img1[h / 2:] - img2[h / 2:]) - numpy.log(img1[:h / 2] - img2[:h / 2]))

                # if self.app.imaging_andor_remove_background:
                #    ma, sa = find_background(img2)
                #    img[img2<ma+4*sa] = np.NaN

                if self.app.imaging_andor_useROI:
                    # set all pixels in absorption image outside roi to NaN
                    r = self.app.marker_roi_andor.roi.ROI

                    imgR = numpy.empty_like(imga)
                    # for timg in [imga, imgb]:
                    for timg in [imga]:
                        imgR[:] = numpy.NaN
                        imgR[r] = timg[r]
                        timg[:] = imgR[:]

                data = {'image1'          : img1, 'image2': img2, 'image3': img1, 'image_numbers': (nr1, nr2, nr1),
                        'absorption_image': img}
                wx.PostEvent(self.app, AndorTripleImageAcquiredEvent(data = data))

                self.save_abs_img(settings.imagefile, img)
                self.save_raw_img(settings.rawimage1file, img1)
                self.save_raw_img(settings.rawimage2file, img2)

        self.message('E')
        print("Exiting ImageConsumerThread")


class ConsumerThreadSingle(ConsumerThread):
    # TODO: Consumer Thread for live mode, check that everything is working and replace the
    # saveimage function with a display event
    """Consume images, calculate absorption image, save to file, display"""

    def run(self):
        self.running = True

        while self.running:

            try:
                nr, img = self.get_image(timeout = 10)

                print("--------Consumerthread--------")
                print("Taken image from Queue")
                print(img)
                self.message('Consuming')
                if not self.running: break
                print("image ok")
            # self.save_abs_img(fileSettings.imagefile, img)
            # self.saveimage(fileSettings.imagesavepath,'Cane.sis',img)

            except queue.Empty:
                print("---------The queue is Empty---------")
                self.message('Waiting for Images')

            else:
                # self.save_abs_img(fileSettings.imagefile, img)
                # self.saveimage_nr(fileSettings.imagesavepath, img, nr)
                self.app.displayImage(img)
                print("--------Just saved an image array--------")


class ConsumerThreadIons(ConsumerThread):
    """Consume images, calculate absorption image, save to file, display"""

    def run(self):
        self.running = True
        imagearrays = []
        scanDataArray = []
        scanIdx = 0
        scanPoints = 0
        acquiredScan = False
        lcl_ScanxList = []

        while self.running:

            if not acquiredScan:
                time.sleep(1)
                while not self.app.ScanExperiment.progressUi.is_running:
                    self.scanList = self.app.ScanList
                    time.sleep(0.1)
                scanPoints = len(self.scanList)
                for i in range(scanPoints):
                    lcl_ScanxList.append(self.scanList[i])
                print('  scanPoints =', scanPoints)
                acquiredScan = True

            try:
                nr, img = self.get_image(timeout = 0)
                # print(self.name, "Dequeue")
                self.message('Consuming')
                if not self.running: break
                # print(self.name, "Image OK")
                # print(img)
                # self.save_abs_img(fileSettings.imagefile, img)
                # self.saveimage(fileSettings.imagesavepath,'Cane.sis',img)

            except queue.Empty:
                # print(self.name, "Queue Empty")
                self.message('Waiting for Images')

            else:
                # self.save_abs_img(fileSettings.imagefile, img)
                lock.acquire()
                try:
                    print("  nr =", nr)
                    img = img.astype(numpy.uint16)
                    if (nr != self.app.CameraParameters['experiments'].value):
                        imagearrays.append(img)
                        print(self.name, "Image Appended to Array")
                        counts = self.getImageROICounts(img)
                        scanDataArray.append(counts)
                        # print("    imagesarrays=", imagearrays)
                    else:
                        imagearrays.append(img)
                        print(self.name, "Image Appended to Array")
                        counts = self.getImageROICounts(img)
                        scanDataArray.append(counts)
                        scanx = lcl_ScanxList[scanIdx]
                        print('  scanIdx =', scanIdx)
                        val, spc, unt = str(scanx).partition(' ')
                        # print(val,'\n', unt)
                        val = '%.3f' % float(val)
                        scanx = ''.join((val, spc, unt))
                        print('  scanx =', scanx)

                        text = str(scanx) + '  GlobalVar  {'
                        for key in self.app.globalVariables:
                            text = text + ' ' + str(key) + ' = ' + str(self.app.globalVariables[key]) + ' ; '
                        text = text + '}  ScanVar  {'
                        for key in self.app.pulserParameters:
                            curParm = self.app.pulserParameters[key]
                            # wst1, wst2, curParm = str(curParm).partition("'_strvalue': '")
                            # curParm, wst3, wst4 = str(curParm).partition("', 'enabled':")
                            # print(curParm.strvalue)
                            v, s, u = str(curParm.strvalue).partition(' ')
                            try:
                                v = float(v)
                            except ValueError:
                                pass
                            if v != 0.0:
                                text = text + ' ' + str(key) + ' = ' + str(curParm.strvalue) + ' ; '
                        text = text + '}'

                        print('  Header:', text)

                        # print("    imagesarrays=", imagearrays, "\n    with scanx = ", scanx)
                        self.saveimage_nr(fileSettings.imagesavepath, imagearrays, nr, scanx, text,
                                          self.app.ScanExperiment.scanControlWidget.settingsName)
                        self.app.scanDataQueue.put(scanDataArray)
                        imagearrays = []
                        scanDataArray = []
                        # print(self.app.ScanExperiment.scanControlWidget.settingsName)
                        print(self.name, "Image Array Saved")
                        scanIdx += 1
                        # time.sleep(1)
                finally:
                    lock.release()

            if scanIdx == scanPoints:
                pass
                # self.app.toggleAcquire()
                lcl_ScanxList = []
                acquiredScan = False
                scanIdx = 0

        # self.app.displayImage(dispArray)
        self.message('Exit Consumer Thread')
        print(self.name, "Exiting")


class ConsumerThreadCalibrate(ConsumerThread):

    def run(self):
        self.running = True
        # self.IonDetectArray = []
        self.imageArray = []

        while self.running:
            try:
                nr, img = self.get_image(timeout = 0)
                self.message('Consuming')
                if not self.running: break
            except queue.Empty:
                self.message('Waiting for Images')
            else:
                lock.acquire()
                try:
                    print("  nr =", nr)
                    img = img.astype(numpy.uint16)
                    print(img.shape)
                    # detector = IonDetect.IonDetection(img, int(self.app.CameraParameters['ionNumber'].value))
                    # self.IonDetectArray.append(detector)
                    self.imageArray.append(img)
                    if nr == 3:
                        self.running = False
                finally:
                    lock.release()

        # for detector in self.IonDetectArray:
        #     detector.idIons()
        # analysisDict = {}

        # for i in range(len(self.IonDetectArray)):
        #     for j in (i + 1, len(self.IonDetectArray)):
        #         dict_i = detector[i].IonDict
        #         dict_j = detector[j].IonDict
        #         matchingArray = []
        #         for key_i in dict_i:
        #             iCenter = dict_i[key_i].center
        #             minDist = detector[i].arr.shape(0)
        #             minDistKey = None
        #             for key_j in dict_j:
        #                 jCenter = dict_j[key_j].center
        #                 distSqr = (iCenter[0] - jCenter[0])**2 + (iCenter[1] - jCenter[1])**2
        #                 if distSqr < minDist:
        #                     minDist = distSqr
        #                     minDistKey = key_j
        #             matchingArray.append((key_i, minDistKey, minDist))
        #         analysisDict[str(i + '_' + j)] = matchingArray

        # print(analysisDict)
        for i in range(1, len(self.imageArray)):
            self.imageArray[0] = numpy.add(self.imageArray[0], self.imageArray[i])
        self.imageArray[0] = numpy.divide(self.imageArray[0], 3)

        detector = IonDetect.IonDetection(self.imageArray[0], int(self.app.CameraParameters['ionNumber'].value))
        detector.idIons()

        self.app.calibratedROI = detector
        # for key in self.IonDetectArray[0].IonDict:
        #     print(key, self.IonDetectArray[0].IonDict[key])
        self.app.displayImage(detector.showIonROIs())
        self.message('Exit Calibrate Thread')
        print(self.name, "Exiting")



# CAMERA CLASS

class Camera(CameraForm, CameraBase):
    dataAvailable = QtCore.pyqtSignal(object)
    OpStates = enum.enum('idle', 'running', 'paused')
    liveCount = 0

    class ParamDictHandler:

        def __init__(self, parameterDict):
            self.dict = parameterDict

        def getParam(self, param):
            paramVal = self.dict[param].value
            ret = None

            if str(paramVal.u) == 'us':
                ret = paramVal.magnitude * 0.001
            elif str(paramVal.u) == 'ms':
                ret = paramVal.magnitude
            else:
                ret = paramVal.magnitude * 1000 if param != 'experiments' else paramVal.magnitude

            return ret


    def __init__(self, config, dbConnection, pulserHardware, globalVariablesUi, shutterUi, ScanExperiment, pulserProgram,
                 parent = None):
        CameraForm.__init__(self)
        CameraBase.__init__(self, parent)

        # Properties to integrate with other components of the code
        self.config = config
        self.configName = 'Camera'
        self.dbConnection = dbConnection
        self.pulserHardware = pulserHardware
        self.pulserProgram = pulserProgram
        self.pulserParameters = pulserProgram.pulseProgramSet['ScanExperiment'].currentContext.parameters
        self.globalVariables = globalVariablesUi.globalDict
        self.globalVariablesChanged = globalVariablesUi.valueChanged
        self.globalVariablesUi = globalVariablesUi
        self.shutterUi = shutterUi
        self.ScanExperiment = ScanExperiment
        self.ScanList = self.ScanExperiment.scanControlWidget.getScan().list
        self.calibratedROI = None

        # Timing and acquisition settings
        self.imaging_mode_andor = "Live"

        self.view = ImageView(self, name = "MainDisplay")
        self.colorMap = ColorMap([0, 0.25, 0.5, 0.75, 1],
                                 [[0, 0, .4], [.55, .55, 1], [1, 1, 1], [1, 1, 0], [1, 0, 0]], ColorMap.RGB)
        print(self.colorMap.getColors())
        self.view.setColorMap(self.colorMap)
        # self.view.setPredefinedGradient("bipolar")
        self.settingsUi = None
        self.temperUi = None

        self.imgproducer_andor = None
        self.imgconsumer_andor = None
        self.tempThrd = None

        self.acquiring_andor = False
        self.currentfolder = None
        self.imaging_andor_useROI = None
        self.busy = None

        self.CameraParameters = None
        self.parHand = None
        self.timing_andor = None
        self.imagequeue_andor = None
        self.scanDataQueue = None
        self.properties_andor = None
        self.imageDisp = None

    @property
    def settings(self):
        return self.settingsUi.settings

    def setupUi(self, parent):
        CameraForm.setupUi(self, parent)

        self.setWindowTitle("Andor Camera")

        # Settings
        self.settingsUi = CameraSettings.CameraSettings(self.config, self.globalVariablesUi)
        self.settingsUi.setupUi(self.settingsUi)
        self.settingsDock.setWidget(self.settingsUi)
        self.settingsUi.valueChanged.connect(self.onSettingsChanged)
        self.CameraParameters = self.settingsUi.ParameterTableModel.parameterDict
        self.parHand = self.ParamDictHandler(self.CameraParameters)
        # print(self.parHand.getParam('Exposure time'), self.parHand.getParam('experiments'))

        # Temperature
        self.temperUi = TemperatureMonitor.TemperatureMonitor(self)
        self.temperUi.setupUi()
        self.temperatureDock.setWidget(self.temperUi)

        self.setCentralWidget(self.view)

        # Arrange the dock widgets
        # self.tabifyDockWidget(self.view, self.settingsDock)

        # Queues for image acquisition
        self.currentfolder = ' '
        self.imagequeue_andor = queue.Queue(self.CameraParameters['experiments'].value * len(self.ScanList))
        self.scanDataQueue = queue.Queue(self.CameraParameters['experiments'].value)
        self.timing_andor = CamTiming(exposure = 100, repetition = 1, live = True)
        self.properties_andor = AndorProperties(ampgain = 0, emgain = 0)
        self.imaging_andor_useROI = False

        # Actions
        self.actionSave.triggered.connect(self.onSave)
        self.actionAcquire.triggered.connect(self.onAcquire)
        self.actionCoolCCD.triggered.connect(self.onCoolCCD)
        self.actionLive.triggered.connect(self.onLive)
        self.actionReset.triggered.connect(self.onResetView)
        self.actionClearQueue.triggered.connect(self.onClearQueue)
        self.actionCalibrate_ROI.triggered.connect(self.onCalibrate)

        # statusbar
        # self.statusBar().showMessage('T = ')
        self.tempThrd = AndorTemperatureThread(self)
        self.tempThrd.start()

        if self.configName + '.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self, self.config[self.configName + '.MainWindow.State'])
        self.onSettingsChanged()

    def toggleAcquire(self):
        if self.actionAcquire.isChecked():
            self.actionAcquire.setChecked(False)
            self.onAcquire()
        else:
            self.actionAcquire.setChecked(True)
            self.onAcquire()

    def updateTemp(self, temp):
        """Update temperature UI"""
        self.temperUi.update(temp)

    def displayImage(self, img):
        """Displays a new image in the camera window."""
        lock.acquire()
        try:
            img = numpy.asanyarray(img)
            self.view.setImage(img, autoRange = False, autoLevels = False)
        finally:
            lock.release()
        # print(img, img.shape)
        # height = img.shape[0]
        # width = img.shape[1]
        # height = 10
        # width = 10
        # imglog = []
        # for x in range(height):
        #     imglog.append([])
        #     for y in range(width):
        #         imglog[x].append(0)

        # self.imageDisp = QtGui.QImage(height, width, QtGui.QImage.Format_RGB32)
        # for x in range(height):
        #     for y in range(width):
        #         pixBrt = img[x][y]
        #         pixBrt = numpy.random.randint(0, 255)
        #         imglog[x][y] = pixBrt = numpy.random.randint(0, 255)
        #         imglog[x][y] = pixBrt
        #         if pixBrt > 255:
        #             self.imageDisp.setPixel(x, y, QtGui.QColor(255, 0, 0, 255).rgb())
        #         else:
        #             self.imageDisp.setPixel(x, y, QtGui.QColor(pixBrt, pixBrt, pixBrt, 255).rgb())

        # print(imglog)

        # self.pixmap = QtGui.QPixmap.fromImage(self.imageDisp.scaledToWidth(570))
        # scene = QtWidgets.QGraphicsScene()
        # scene.addPixmap(self.pixmap)
        # self.CameraView.setScene(scene)
        # self.CameraView.setCacheMode(QtWidgets.QGraphicsView.CacheNone)

    def saveConfig(self):
        self.settings.state = self.saveState()
        self.settings.isVisible = self.isVisible()
        self.config[self.configName] = self.settings
        self.settingsUi.saveConfig()

    def onSave(self):
        print("save image")

        print(self.ScanExperiment.scanControlWidget.getScan().list)
        print(self.ScanExperiment.scanControlWidget.getScan().list[0])
        print(self.ScanExperiment.scanControlWidget.getScan().list[-1])
        self.settingsUi.saveConfig()
        # needs astropy
        # image_file = os.path.join(os.path.dirname(__file__), '..', 'ui/icons/80up_1.fits')
        # image_data = fits.getdata(image_file)
        # image_f = image_data[[0], :, range(0, 256)]
        # image(image_f, title="Ions")
        return

    def onSettingsChanged(self):
        if self.acquiring_andor:
            if self.imaging_mode_andor == 'Live':
                self.onLive()
            elif self.imaging_mode_andor == 'TriggeredAcquisition':
                self.onAcquire()
            else:
                self.stop_acquisition_andor()

        print("Camera Settings Changed")

    def onCoolCCD(self):
        if self.actionCoolCCD.isChecked():
            camandor.start_cooling()
            # AndorTemperatureThread(self).start()
        else:
            camandor.stop_cooling()
            # AndorTemperatureThread(self).stop()

    def onResetView(self):
        # data = self.view.getImageItem()
        if self.imaging_mode_andor == 'Live':
            self.stop_acquisition_andor()
            self.view.close()
            self.view = ImageView(self, name = "MainDisplay")
            self.setCentralWidget(self.view)
            self.view.setColorMap(self.colorMap)
            self.start_acquisition_andor()

        # self.view.setImage(data)

    def onClearQueue(self):
        self.imagequeue_andor = queue.Queue(self.CameraParameters['experiments'].value * len(self.ScanList))

    def close(self):
        self.view.close()
        self.actionCoolCCD.setChecked(False)
        self.onCoolCCD()
        self.stop_acquisition_andor()
        self.stop_acquisition_andor()
        self.tempThrd.running = False
        progWind = AndorShutdown.AndorShutDown()
        progWind.setProgress(camandor.gettemperature() - 5, 0)

        while self.tempThrd.is_alive():
            progWind.updateTemp(camandor.gettemperature())
            print('temp =', camandor.gettemperature())
            time.sleep(1)

        progWind.setShutdown()
        camandor.shutdown()
        progWind.close()
        self.temperUi.close()
        self.hide()

    def OnIdle(self, event):
        self.busy = 0

    def OnSingleImageAcquiredAndor(self):

        if event.img is not None:
            # cut image into halves
            img1 = event.img[:, :]

            # avoid deadlock if too many images to process
            if self.Pending():
                self.busy += 1
            else:
                self.busy = 0

            if self.busy > 3:
                print("I am busy, skip displaying")
                self.show_status_message('.')
            else:
                self.image1a.show_image(img1, description = "image #%d" % event.imgnr)

    def onLive(self):

        if self.actionLive.isChecked():
            # print("Live ON")
            self.stop_acquisition_andor()
            # self.timing_andor.set_live(True)
            self.imaging_mode_andor = "Live"
            camandor.andormode = self.imaging_mode_andor
            self.start_acquisition_andor()
            time.sleep(1)
            # self.view.autoLevels()
            # self.view.autoRange()
        else:
            # print("Live OFF")
            self.stop_acquisition_andor()
            # self.timing_andor.set_live(False)
            # if self.actionLive.isChecked():
            #     self.displayImage(None)

    def onAcquire(self):

        if self.actionAcquire.isChecked():
            # print("Acquire ON")
            self.stop_acquisition_andor()
            self.actionLive.setChecked(False)
            self.actionLive.setEnabled(False)
            # self.timing_andor.set_live(False)
            self.imaging_mode_andor = "TriggeredAcquisition"
            print('============== Number of experiments = ', self.parHand.getParam('experiments'),
                  '==============')
            camandor.andormode = self.imaging_mode_andor
            self.start_acquisition_andor()

        else:
            # print("Acquire OFF")
            self.stop_acquisition_andor()
            self.actionLive.setEnabled(True)
            # self.do_toggle_button(event.Checked(), self.ID_AcquireAndorButton)

    def onCalibrate(self):
        self.stop_acquisition_andor()
        self.actionLive.setChecked(False)
        self.actionLive.setEnabled(False)
        # self.timing_andor.set_live(False)
        self.imaging_mode_andor = "Calibrate"
        print('Calibrating ROIs...')
        camandor.andormode = self.imaging_mode_andor
        self.start_acquisition_andor()

    def onCounter(self):
        self.stop_acquisition_andor()
        self.actionLive.setChecked(False)
        self.actionLive.setEnabled(False)
        # self.timing_andor.set_live(False)
        self.imaging_mode_andor = "AutoLoad"
        print('Loading...')
        camandor.andormode = self.imaging_mode_andor
        self.start_acquisition_andor()

    def offCounter(self):
        self.stop_acquisition_andor()
        self.actionLive.setEnabled(True)

    def startThresholdCalibrator(self):
        self.stop_acquisition_andor()
        self.actionLive.setChecked(False)
        self.actionLive.setEnabled(False)
        # self.timing_andor.set_live(False)
        self.imaging_mode_andor = "Threshold"
        print('Calibrating Thresholds...')
        camandor.andormode = self.imaging_mode_andor
        self.imagequeue_andor = queue.Queue(5000 * len(self.ScanList))
        self.start_acquisition_andor()

    def stopThresholdCalibrator(self):
        self.stop_acquisition_andor()
        self.actionLive.setEnabled(True)

    def start_acquisition_andor(self):
        self.acquiring_andor = True
        print('Start Acquisition')
        # self.menu.EnableTop(self.ID_TimingAndor, False)

        if self.imaging_mode_andor == "Live":
            # print("In LIVE Mode")
            self.timing_andor.set_live(True)
            self.imgproducer_andor = AcquireThreadAndorLive(self, camandor, self.imagequeue_andor)
            self.imgconsumer_andor = ConsumerThreadAndorLive(self, self.imagequeue_andor)
        elif self.imaging_mode_andor == "TriggeredAcquisition" or self.imaging_mode_andor == 'Threshold':
            # print("In TRIGGERED ACQUISITION Mode")
            self.timing_andor.set_live(False)
            self.imgproducer_andor = AcquireThreadAndor(self, camandor, self.imagequeue_andor)
            self.imgconsumer_andor = ConsumerThreadIons(self, self.imagequeue_andor)
            # print("ConsumerThreadIons called but not started")
        elif self.imaging_mode_andor == 'Calibrate':
            self.timing_andor.set_live(False)
            self.imgproducer_andor = AcquireThreadAndorCalibrate(self, camandor, self.imagequeue_andor)
            self.imgconsumer_andor = ConsumerThreadCalibrate(self, self.imagequeue_andor)
        elif self.imaging_mode_andor == 'AutoLoad':
            self.timing_andor.set_live(True)
            self.imgproducer_andor = AcquireThreadAndorAutoLoad(self, camandor, self.imagequeue_andor)

        self.imgproducer_andor.start()
        self.imgconsumer_andor.start()

    def stop_acquisition_andor(self):
        if self.acquiring_andor:
            print('Stop Acquisition')
            print("The Imaging queue size is :", self.imagequeue_andor.qsize())
            self.imgproducer_andor.stop()
            # self.imgproducer_andor.running = False # unnecessary...
            # time.sleep(0.5)

            exitCount = 0
            exitConParam = (0, self.imagequeue_andor.qsize())
            while self.imagequeue_andor.qsize() > 0:  # finish to save the images
                print("The Imaging queue is blocked and the size is :", self.imagequeue_andor.qsize())
                time.sleep(1)
                exitConParam = (exitConParam[1], self.imagequeue_andor.qsize())
                if exitConParam[0]-exitConParam[1] == 0:
                    exitCount += 1
                if exitCount >= 5:
                    self.imagequeue_andor = queue.Queue(self.CameraParameters['experiments'].value * len(self.ScanList))

            if self.imgconsumer_andor is not None:
                self.imgconsumer_andor.stop()
            # self.imgconsumer_andor.running = False # unnecessary...

            # self.imgconsumer_andor.join(2)  # 2
            # self.imgproducer_andor.join(6)  # 6
            # if self.imgproducer_andor.isAlive() or self.imgconsumer_andor.isAlive():
            #    print("could not stop Andor acquisition threads!", threading.enumerate())
            self.acquiring_andor = False
            self.imgconsumer_andor = None
            self.imgproducer_andor = None
            self.imagequeue_andor = queue.Queue(self.CameraParameters['experiments'].value * len(self.ScanList))
            # self.menu.EnableTop(self.ID_TimingAndor, True)

    # def OnSaveImageAndor(self):
    #     print("save image")
    #     #imgA = self.image1a.imgview.get_camimage()
    #     #readsis.write_raw_image(settings.imagefile, imgA, True)
    #     #wx.PostEvent(self, StatusMessageEvent(data='s')

# if __name__ == '__main__':
#
#     camandor = Cam()
#     camandor.open()
#     camandor.set_timing(integration=100, repetition=0, ampgain=0, emgain=0)
#     camandor.start_cooling()
#
#     #CameraGui = Camera('config', 'dbConnection', 'pulserHardware', 'globalVariablesUi', 'shutterUi',
# 'externalInstrumentObservable')
#     #Tthread = AndorTemperatureThread(CameraGui,camandor)
#     #Tthread.start()
#
#     #camandor.wait()
#     img = camandor.roidata()
#
#     print(img)
#     #camandor.close()
