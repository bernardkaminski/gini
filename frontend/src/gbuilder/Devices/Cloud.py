from Core.Connection import *
from Core.Interfaceable import *
from Core.globals import environ
from PyQt4.QtCore import QPoint
import Core.util

class Cloud(Interfaceable):
    device_type = "Cloud"

    def __init__(self):
        Interfaceable.__init__(self)
        self.lightPoint = QPoint(-19,-3)
