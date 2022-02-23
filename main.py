from PySide2 import QtCore
from PySide2.QtCore import Qt, QThread, Signal, Slot, QObject, QByteArray
from PySide2.QtGui import QImage, QKeySequence, QPixmap
from PySide2.QtWidgets import (QMainWindow, QAction, QApplication,
                                QHBoxLayout, QLabel, QGroupBox, 
                                QPushButton, QSizePolicy,
                                QWidget, QVBoxLayout)

import qimage2ndarray


import cv2, sys, time
import numpy as np
from PIL import Image

import logging
logging.basicConfig(level=logging.INFO)
loggy = logging.info



def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

class CsiCaptureDev(QObject):
    finished0 = Signal()
    finished1 = Signal()
    image0Ready = Signal(QImage)
    image1Ready = Signal(QImage)
    def __init__(self, device_no=0, dev_access="gstr", inputResolution="3264x2464", 
                        inputFlip=0, inputFps=21, outputResolution="820x616", outputType="RGB"):
        super().__init__()
        self.dev_id = device_no
        self.dev_acces_type = dev_access
        self.dev_input_width = int(inputResolution.split("x")[0])
        self.dev_input_height = int(inputResolution.split("x")[1])
        self.dev_input_fps = inputFps
        self.dev_input_flip_mode = inputFlip
        self.dev_output_width = int(outputResolution.split("x")[0])
        self.dev_output_height = int(outputResolution.split("x")[1])
        self.output_color_coding = outputType
        self.continue_to_run = True 
    
    def gstreamer_pipeline(self, sensor_id=0, capture_width=1920, capture_height=1080, display_width=960,
                            display_height=540, framerate=30, flip_method=0):
        return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
        )

    def run(self):
        if self.dev_acces_type == "gstr":
            self.gstr_pipe = self.gstreamer_pipeline(sensor_id=self.dev_id, 
                                                        flip_method=self.dev_input_flip_mode,
                                                        capture_width=self.dev_input_width,
                                                        capture_height=self.dev_input_height,
                                                        display_width=self.dev_input_width,
                                                        display_height=self.dev_input_height,
                                                        framerate=self.dev_input_fps)
            self.cv_vid_capture = cv2.VideoCapture(self.gstr_pipe, cv2.CAP_GSTREAMER)
        while self.continue_to_run:
            retval, frameOfnp = self.cv_vid_capture.read()
            if retval:
                # Creating and scaling QImage
                h, w, ch = frameOfnp.shape #dtype uint8
                rgbFrame = cv2.cvtColor(frameOfnp, cv2.COLOR_BGR2RGB)
                self.rgbImage = rgbFrame.copy()
                smallRgbFrame = cv2.resize(rgbFrame, (self.dev_output_width, self.dev_output_height))
                img = qimage2ndarray.array2qimage(data)
                scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)

                # Emit signal
                if self.dev_id == 0:
                    pass
                    self.image0Ready.emit(scaled_img)
                else:
                    pass
                    self.image1Ready.emit(scaled_img)
                data.clear()
                del data

            else:
                print("Error: csi"+str(self.dev_id)+" is unable to retrieve frame")
                self.cv_vid_capture.release()
                time.sleep(3)
                if self.dev_id == 0:
                    self.finished0.emit()
                else:
                    self.finished1.emit()

        
        print("csi"+str(self.dev_id)+" is stopped")   
        self.cv_vid_capture.release()
        time.sleep(3)
        if self.dev_id == 0:
            self.finished0.emit()
        else:
            self.finished1.emit()
        




class ThreadCapture(QThread):
    
    updateFrame = Signal(QImage)

    def __init__(self, sensor_id=0, parent=None):
        super(QThread, self).__init__()
        self.sensor_id = sensor_id
        self.status = True
        self.cap = cv2.VideoCapture(gstreamer_pipeline(sensor_id=self.sensor_id, 
                                                        flip_method=0,
                                                        capture_width=3264,
                                                        capture_height=2464,
                                                        display_width=3264,
                                                        display_height=2464,
                                                        framerate=21), cv2.CAP_GSTREAMER)

    def run(self):
        if self.cap.isOpened():
            while self.status:
                retval, frameOfnp = self.cap.read()
                if retval:
                    # Creating and scaling QImage
                    h, w, ch = frameOfnp.shape
                    rgbFrame = cv2.cvtColor(frameOfnp, cv2.COLOR_BGR2RGB)
                    self.rgbImage = rgbFrame
                    smallRgbFrame = cv2.resize(rgbFrame, (820, 616))
                    img = QImage(smallRgbFrame, w, h, ch * w, QImage.Format_RGB888)
                    
                    scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)

                    # Emit signal
                    self.updateFrame.emit(scaled_img)
            self.cap.release()
            time.sleep(3)
            sys.exit(-1)
        else:
            print("Error: csi"+str(self.sensor_id)+" is unable to be opened")
        self.cap.release()
        time.sleep(3)
        sys.exit(-1)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("VEOS I")
        self.setGeometry(0, 0, 1280, 720)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=QApplication.quit)
        self.menu_file.addAction(exit)

        self.menu_about = self.menu.addMenu("&About")
        about = QAction("About Qt", self, shortcut=QKeySequence(QKeySequence.HelpContents),
                        triggered=QApplication.aboutQt)
        self.menu_about.addAction(about)

        # Create a label for the display camera
        labels_layout = QHBoxLayout()
        self.label0 = QLabel(self)
        self.label0.setFixedSize(640, 480)
        self.label1 = QLabel(self)
        self.label1.setFixedSize(640, 480)
        labels_layout.addWidget(self.label0)
        labels_layout.addWidget(self.label1)
        
        # Thread in charge of updating the image
        ##self.th0 = ThreadCapture(self, 0)
        ##self.th0.finished.connect(self.close)
        ##self.th0.updateFrame.connect(self.setImage0)
        self.thread_of_csi0 = QThread()
        self.cap_csi0 = CsiCaptureDev(0,"gstr", "820x616", 0, 30, "820x616", "RGB")
        self.cap_csi0.moveToThread(self.thread_of_csi0)
        self.thread_of_csi0.started.connect(self.cap_csi0.run)
        self.cap_csi0.finished0.connect(self.thread_of_csi0.quit)
        self.cap_csi0.finished0.connect(self.cap_csi0.deleteLater)
        self.thread_of_csi0.finished.connect(self.thread_of_csi0.deleteLater)
        self.cap_csi0.image0Ready.connect(self.setImage0)
        
        # Thread in charge of updating the image
        ##self.th1 = ThreadCapture(self, 1)
        ##self.th1.finished.connect(self.close)
        ##self.th1.updateFrame.connect(self.setImage1)
        self.thread_of_csi1 = QThread()
        self.cap_csi1 = CsiCaptureDev(1,"gstr", "820x616", 0, 30, "820x616", "RGB") # QObject
        self.cap_csi1.moveToThread(self.thread_of_csi1)
        self.thread_of_csi1.started.connect(self.cap_csi1.run)
        self.cap_csi1.finished1.connect(self.thread_of_csi1.quit)
        self.cap_csi1.finished1.connect(self.cap_csi1.deleteLater)
        self.thread_of_csi1.finished.connect(self.thread_of_csi1.deleteLater)
        self.cap_csi1.image1Ready.connect(self.setImage1)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.buttonCsi0 = QPushButton("Start CSI 0")
        self.buttonCsi1 = QPushButton("Start CSI 1")
        self.buttonStop = QPushButton("Stop & Shutdown")
        self.buttonCsi0.setSizePolicy(QSizePolicy.Preferred, 
                                        QSizePolicy.Expanding)
        self.buttonCsi1.setSizePolicy(QSizePolicy.Preferred, 
                                        QSizePolicy.Expanding)
        self.buttonStop.setSizePolicy(QSizePolicy.Preferred, 
                                        QSizePolicy.Expanding)
        buttons_layout.addWidget(self.buttonCsi0)
        buttons_layout.addWidget(self.buttonCsi1)
        buttons_layout.addWidget(self.buttonStop)

        bottom_layout = QHBoxLayout()
        bottom_layout.addLayout(buttons_layout, 1)

        bbottom_layout = QHBoxLayout()
        self.buttonCaptureCsi0 = QPushButton("Save From Left I")
        self.buttonCaptureCsi1 = QPushButton("Save From Right I")
        self.buttonCaptureCsi0.setSizePolicy(QSizePolicy.Preferred,
                                            QSizePolicy.Expanding)
        self.buttonCaptureCsi1.setSizePolicy(QSizePolicy.Preferred,
                                            QSizePolicy.Expanding)
        bbottom_layout.addWidget(self.buttonCaptureCsi0)
        bbottom_layout.addWidget(self.buttonCaptureCsi1)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(labels_layout)
        layout.addLayout(bottom_layout)
        layout.addLayout(bbottom_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connections
        self.buttonCsi0.clicked.connect(self.start0)
        self.buttonCsi1.clicked.connect(self.start1)
        self.buttonStop.clicked.connect(self.kill_thread)
        self.buttonCaptureCsi0.clicked.connect(self.saveFig0)
        self.buttonCaptureCsi1.clicked.connect(self.saveFig1)

    @Slot()
    def saveFig0(self):
        print("saving from left I")
        postList = str(time.time()).split(".")
        filename = "left_"+postList[0]+postList[1]+".png"
        Image.fromarray(self.leftImg).save(filename)

    def saveFig1(self):
        print("saving from right I")
        postList = str(time.time()).split(".")
        filename = "right_"+postList[0]+postList[1]+".png"
        Image.fromarray(self.rightImg).save(filename)

    @Slot()
    def kill_thread(self):
        print("Finishing...")
        #self.th0.status = False
        #self.th1.status = False
        #self.th.cap0.Close()
        #self.th.cap1.Close()
        self.cap_csi0.continue_to_run = False
        self.cap_csi1.continue_to_run = False
        #time.sleep(4)       
        #self.th0.terminate()
        #self.th1.terminate()
        # Give time for the thread to finish
        time.sleep(4) 

    @Slot()
    def start0(self):
        print("Starting...0")
        #self.th0.start()
        self.thread_of_csi0.start()

    @Slot()
    def start1(self):
        print("Starting...1")
        #self.th1.start()
        self.thread_of_csi1.start()

    @Slot(QImage)
    def setImage0(self, image):
        self.rightImg = self.cap_csi0.rgbImage
        self.label1.setPixmap(QPixmap.fromImage(image))
    
    @Slot(QImage)
    def setImage1(self, image):
        self.leftImg = self.cap_csi1.rgbImage
        self.label0.setPixmap(QPixmap.fromImage(image))




if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec_())