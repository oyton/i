from re import A
import numpy as np
from PySide2.QtGui import QImage
import qimage2ndarray

def createImage():
    a = np.random.rand(500,500,3)
    aa = 255*a 
    aaa = np.floor(aa)
    A = aaa.astype(np.uint8)
    return A


for i in range(1000):
    A = createImage()
#    ASTR = A.tostring()
#    h, w, ch = A.shape
#    QA = QImage(ASTR, w, h, QImage.Format_RGB888)
#    ASTR = b""
#    del ASTR
    QA = qimage2ndarray.array2qimage(A)

