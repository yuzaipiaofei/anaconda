from installclass import BaseInstallClass
from rhpl.translate import N_, _

import os
import iutil

class InstallClass(BaseInstallClass):
    name = N_("Migrate Existing System")
    pixmap = "upgrade.png"
    sortPriority = 999998

    parentClass = ( _("Migrate"), "upgrade.png" )

    def requiredDisplayMode(self):
        return 't'

    def setSteps(self, dispatch):
        dispatch.setStepList(
            "language",
            "keyboard",
            "welcome",
            "installtype",
            "findrootparts",
            "findinstall",
            "partitionobjinit",
            "findconfig",
            "upgrademount",
            "upgrademigfind",
            "upgrademigratefs",
            "upgradecontinue",
            "readcomps",
            "findpackages",
            "upgbootloader",
            "checkdeps",
            "dependencies",
            "confirmupgrade",
            "install",
            "migratefilesystems",
            "preinstallconfig",
            "installpackages",
            "postinstallconfig",
            "instbootloader",
            "dopostaction",
            "methodcomplete",
            "complete"
        )

        if iutil.getArch() != "i386" and iutil.getArch() != "x86_64":
            dispatch.skipStep("bootloader")
            dispatch.skipStep("bootloaderadvanced")

        if iutil.getArch() != "i386" and iutil.getArch() != "x86_64":
            dispatch.skipStep("upgbootloader")            

    def setInstallData(self, id):
        BaseInstallClass.setInstallData(self, id)
        id.upgrade.set(1)
    
    def __init__(self, expert):
        BaseInstallClass.__init__(self, expert)
