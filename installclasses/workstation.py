from installclass import BaseInstallClass
from installclass import FSEDIT_CLEAR_ALL
from translate import N_
import os
import iutil

class InstallClass(BaseInstallClass):
    name = N_("Workstation")
    pixmap = "workstation.png"

    sortPriority = 1

    def __init__(self, expert):
	BaseInstallClass.__init__(self)
	self.setGroups(["Workstation Common"])
	self.setHostname("localhost.localdomain")
	if not expert:
	    self.addToSkipList("lilo")
	self.addToSkipList("authentication")
	self.setMakeBootdisk(1)

        self.showgroups = [ "KDE",
                            (1, "GNOME"),
                            "Games" ]
	self.setClearParts(None)
