from installclass import BaseInstallClass
from installclass import FSEDIT_CLEAR_ALL
from translate import N_
import os
import iutil

# custom installs are easy :-)
class InstallClass(BaseInstallClass):

    name = N_("Custom System")
    pixmap = "custom.png"
    
    sortPriority = 10000

    def __init__(self, expert):
	BaseInstallClass.__init__(self)
	self.setClearParts(None)



