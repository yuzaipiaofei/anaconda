import rpm
import os
rpm.addMacro("_i18ndomains", "redhat-dist")

import iutil, isys
from lilo import LiloConfiguration
arch = iutil.getArch ()
if arch == "sparc":
    from silo import SiloInstall
elif arch == "alpha":
    from milo import MiloInstall, onMILO
elif arch == "ia64":
    from eli import EliConfiguration
import string
import socket
import crypt
import sys
import whrandom
import _balkan
import kudzu
from simpleconfig import SimpleConfigFile
from mouse import Mouse
from xf86config import XF86Config
import errno
import raid
from translate import cat
import fstab
import time
import re
import gettext_rh
import os.path
import upgrade
from translate import _
from log import log

class ToDo:
    def __init__(self, intf, method, rootPath, setupFilesystems = 1,
		 installSystem = 1, instClass = None, x = None,
		 expert = 0, serial = 0, reconfigOnly = 0, test = 0,
		 extraModules = []):
	self.intf = intf
	self.method = method
	self.hdList = None
	self.comps = None
	self.instPath = rootPath
	self.setupFilesystems = setupFilesystems
	self.installSystem = installSystem
	self.serial = serial
        self.reconfigOnly = reconfigOnly
        self.extraModules = extraModules
        self.verifiedState = None

        self.ddruidReadOnly = 0
        self.bootdisk = 1
        self.bdstate = ""

        log.open (serial, reconfigOnly, test, setupFilesystems)

        self.fstab = None

	# liloDevice, liloLinear, liloAppend are initialized form the
	# default install class
        arch = iutil.getArch ()
        self.lilo = LiloConfiguration()
	if arch == "sparc":
	    self.silo = SiloInstall (self.serial)
        elif arch == "alpha":
            self.milo = MiloInstall (self)
        elif arch == "ia64":
            self.eli = EliConfiguration ()
        self.upgrade = 0
	self.ddruidAlreadySaved = 0
        self.initlevel = 3
	self.expert = expert
        self.progressWindow = None
	self.fdDevice = None
        self.lilostate = ""
        self.videoCardOriginalName = ""
        self.videoCardOriginalNode = ""
        self.isDDC = ""
        self.videoCardStateName = ""
        self.videoCardStateNode = ""
        self.videoRamState = ""
        self.videoRamOriginal = ""
        self.monitorOriginalName = ""
        self.monitorOriginalNode = ""
        self.monitorHsync = ""
        self.monitorVsync = ""
        self.monitorHsyncState = ""
        self.monitorVsyncState = ""        
        self.probedFlag = ""
        self.resState = ""
        self.depthState = ""
        self.initState = 0
        self.dhcpState = ""
        self.rebuildTime = None

        # If reconfig mode, don't probe floppy
        if self.reconfigOnly != 1:
            self.setFdDevice()

	if (not instClass):
	    raise TypeError, "installation class expected"

	# XXX
        if x:
            self.x = x
            #self.x.setMouse (self.mouse)
        #else:
            #self.x = XF86Config (mouse = self.mouse)

	# This absolutely, positively MUST BE LAST
	self.setClass(instClass)

    def setFdDevice(self):
	if self.fdDevice:
	    return

	self.fdDevice = "fd0"
	if iutil.getArch() == "sparc":
	    try:
		f = open(self.fdDevice, "r")
	    except IOError, (errnum, msg):
		if errno.errorcode[errnum] == 'ENXIO':
		    self.fdDevice = "fd1"
	    else:
		f.close()
	elif iutil.getArch() == "alpha":
	    pass
	elif iutil.getArch() == "i386" or iutil.getArch() == "ia64":
	    # Look for the first IDE floppy device
	    drives = isys.floppyDriveDict()
	    if not drives:
		log("no IDE floppy devices found")
		return 0

            floppyDrive = drives.keys()[0]
            # need to go through and find if there is an LS-120
            for dev in drives.keys():
                if re.compile(".*[Ll][Ss]-120.*").search(drives[dev]):
                    floppyDrive = dev

	    # No IDE floppy's -- we're fine w/ /dev/fd0
	    if not floppyDrive: return

	    if iutil.getArch() == "ia64":
		self.fdDevice = floppyDrive
		log("anaconda floppy device is %s", self.fdDevice)
		return

	    # Look in syslog for a real fd0 (which would take precedence)
            try:
                f = open("/tmp/syslog", "r")
            except IOError:
                return
	    for line in f.readlines():
		# chop off the loglevel (which init's syslog leaves behind)
		line = line[3:]
		match = "Floppy drive(s): "
		if match == line[:len(match)]:
		    # Good enough
		    floppyDrive = "fd0"
		    break

	    self.fdDevice = floppyDrive
	else:
	    raise SystemError, "cannot determine floppy device for this arch"

	log("anaconda floppy device is %s", self.fdDevice)

    def writeMouse(self):
	if self.serial: return
	# XXX
	#self.mouse.writeConfig(self.instPath)

    def needBootdisk (self):
	if self.bootdisk or self.fstab.rootOnLoop(): return 1

    def makeBootdisk (self):
	# this is faster then waiting on mkbootdisk to fail
	device = self.fdDevice
	file = "/tmp/floppy"
	isys.makeDevInode(device, file)
	try:
	    fd = os.open(file, os.O_RDONLY)
	except:
            raise RuntimeError, "boot disk creation failed"
	os.close(fd)

	kernel = self.hdList['kernel']
        kernelTag = "-%s-%s" % (kernel[rpm.RPMTAG_VERSION],
                                kernel[rpm.RPMTAG_RELEASE])

        w = self.intf.waitWindow (_("Creating"), _("Creating boot disk..."))
        rc = iutil.execWithRedirect("/sbin/mkbootdisk",
                                    [ "/sbin/mkbootdisk",
                                      "--noprompt",
                                      "--device",
                                      "/dev/" + self.fdDevice,
                                      kernelTag[1:] ],
                                    stdout = '/dev/tty5', stderr = '/dev/tty5',
				    searchPath = 1, root = self.instPath)
        w.pop()
        if rc:
            raise RuntimeError, "boot disk creation failed"

    def freeHeaderList(self):
	if (self.hdList):
	    self.hdList = None

    def selectPackage(self, package):
	if not self.hdList.packages.has_key(package):
	    str = "package %s is not available" % (package,)
	    raise ValueError, str
	self.hdList.packages[package].selected = 1

    def upgradeFindRoot(self):
	if not self.setupFilesystems: return [ (self.instPath, 'ext2') ]
	return upgrade.findExistingRoots(self.intf, self.fstab)

    def upgradeMountFilesystems(self, rootInfo):
	# mount everything and turn on swap

        if self.setupFilesystems:
	    try:
		upgrade.mountRootPartition(self.intf,rootInfo,
                                           self.fstab, self.instPath,
					   allowDirty = 0)
	    except SystemError, msg:
		self.intf.messageWindow(_("Dirty Filesystems"),
		    _("One or more of the filesystems listed in the "
		      "/etc/fstab on your Linux system cannot be mounted. "
		      "Please fix this problem and try to upgrade again."))
		sys.exit(0)

	    checkLinks = [ '/etc', '/var', '/var/lib', '/var/lib/rpm',
			   '/boot', '/tmp', '/var/tmp' ]
	    badLinks = []
	    for n in checkLinks:
		if not os.path.islink(self.instPath + n): continue
		l = os.readlink(self.instPath + n)
		if l[0] == '/':
		    badLinks.append(n)

	    if badLinks:
		message = _("The following files are absolute symbolic " 
			    "links, which we do not support during an " 
			    "upgrade. Please change them to relative "
			    "symbolic links and restart the upgrade.\n\n")
		for n in badLinks:
		    message = message + '\t' + n + '\n'
		self.intf.messageWindow(("Absolute Symlinks"), message)
		sys.exit(0)
        else:
            fstab.readFstab(self.instPath + '/etc/fstab', self.fstab)
            

	self.fstab.turnOnSwap(self.instPath, formatSwap = 0)
                    
    def upgradeFindPackages (self):
        if not self.rebuildTime:
            self.rebuildTime = str(int(time.time()))
        self.getCompsList ()
	self.getHeaderList ()
	self.method.mergeFullHeaders(self.hdList)

        win = self.intf.waitWindow (_("Finding"),
                                    _("Finding packages to upgrade..."))

        self.dbpath = "/var/lib/anaconda-rebuilddb" + self.rebuildTime
        rpm.addMacro("_dbpath_rebuild", self.dbpath)
        rpm.addMacro("_dbapi", "-1")

        # now, set the system clock so the timestamps will be right:
        iutil.setClock (self.instPath)
        
        # and rebuild the database so we can run the dependency problem
        # sets against the on disk db
        rc = rpm.rebuilddb (self.instPath)
        if rc:
            iutil.rmrf (self.instPath + "/var/lib/anaconda-rebuilddb"
                        + self.rebuildTime)
            win.pop()
            self.intf.messageWindow(_("Error"),
                                    _("Rebuild of RPM database failed. "
                                      "You may be out of disk space?"))
	    if self.setupFilesystems:
		self.fstab.umountFilesystems (self.instPath)
	    sys.exit(0)

        rpm.addMacro("_dbpath", self.dbpath)
        rpm.addMacro("_dbapi", "3")
        try:
            packages = rpm.findUpgradeSet (self.hdList.hdlist, self.instPath)
        except rpm.error:
            iutil.rmrf (self.instPath + "/var/lib/anaconda-rebuilddb"
                        + self.rebuildTime)
            win.pop()
            self.intf.messageWindow(_("Error"),
                                    _("An error occured when finding the packages to "
                                      "upgrade."))
	    if self.setupFilesystems:
		self.fstab.umountFilesystems (self.instPath)
	    sys.exit(0)
                
        # Turn off all comps
        for comp in self.comps:
            comp.unselect()

        # unselect all packages
        for package in self.hdList.packages.values ():
            package.selected = 0

        hasX = 0
        hasFileManager = 0
        # turn on the packages in the upgrade set
        for package in packages:
            self.hdList[package[rpm.RPMTAG_NAME]].select()
            if package[rpm.RPMTAG_NAME] == "XFree86":
                hasX = 1
            if package[rpm.RPMTAG_NAME] == "gmc":
                hasFileManager = 1
            if package[rpm.RPMTAG_NAME] == "kdebase":
                hasFileManager = 1

        # open up the database to check dependencies
        db = rpm.opendb (0, self.instPath)

        # if we have X but not gmc, we need to turn on GNOME.  We only
        # want to turn on packages we don't have installed already, though.
        if hasX and not hasFileManager:
            log ("Has X but no desktop -- Installing GNOME")
            for package in self.comps['GNOME'].pkgs:
                try:
                    rec = db.findbyname (package.name)
                except rpm.error:
                    rec = None
                if not rec:
                    log ("GNOME: Adding %s", package)
                    package.select()
            
        del db

        # new package dependency fixup
        deps = self.verifyDeps ()
        loops = 0
        while deps and self.canResolveDeps (deps) and loops < 10:
            for (name, suggest) in deps:
                if name != _("no suggestion"):
                    log ("Upgrade Dependency: %s needs %s, "
                         "automatically added.", name, suggest)
            self.selectDeps (deps)
            deps = self.verifyDeps ()
            loops = loops + 1

        win.pop ()

    def setClass(todo, instClass):
	# XXX
	return 

	todo.instClass = instClass
	todo.updateInstClassComps()
	( enable, policy, trusts, ports, dhcp, ssh,
	  telnet, smtp, http, ftp ) = todo.instClass.getFirewall()
	  
	
	todo.bootdisk = todo.instClass.getMakeBootdisk()
	todo.zeroMbr = todo.instClass.zeroMbr
	(where, linear, append) = todo.instClass.getLiloInformation()

        arch = iutil.getArch ()
	if arch == "i386":	
	    todo.lilo.setDevice(where)
	    todo.lilo.setLinear(linear)
	    if append: todo.lilo.setAppend(append)
 	elif arch == "sparc":
	    todo.silo.setDevice(where)
	    todo.silo.setAppend(append)

	if (todo.instClass.x):
	    todo.x = todo.instClass.x

	# XXX
	#if (todo.instClass.mouse):
	    #(type, device, emulateThreeButtons) = todo.instClass.mouse
	    #todo.mouse.set(type, emulateThreeButtons, thedev = device)
            #todo.x.setMouse(todo.mouse)
            
        # this is messy, needed for upgradeonly install class
        if todo.instClass.installType == "upgrade":
            todo.upgrade = 1

    def getPartitionWarningText(self):
	return self.instClass.clearPartText

    def setDefaultRunlevel (self):
        try:
            inittab = open (self.instPath + '/etc/inittab', 'r')
        except IOError:
            log ("WARNING, there is no inittab, bad things will happen!")
            return
        lines = inittab.readlines ()
        inittab.close ()
        inittab = open (self.instPath + '/etc/inittab', 'w')        
        for line in lines:
            if len (line) > 3 and line[:3] == "id:":
                fields = string.split (line, ':')
                fields[1] = str (self.initlevel)
                line = string.join (fields, ':')
            inittab.write (line)
        inittab.close ()

    def kernelVersionList(self):
	kernelVersions = []

	for ktag in [ 'kernel-smp', 'kernel-enterprise' ]:
	    tag = string.split(ktag, '-')[1]
	    if (self.hdList.has_key(ktag) and 
		self.hdList[ktag].selected):
		version = (self.hdList[ktag][rpm.RPMTAG_VERSION] + "-" +
			   self.hdList[ktag][rpm.RPMTAG_RELEASE] + tag)
		kernelVersions.append(version)
 
 	version = (self.hdList['kernel'][rpm.RPMTAG_VERSION] + "-" +
 		   self.hdList['kernel'][rpm.RPMTAG_RELEASE])
 	kernelVersions.append(version)
 
	return kernelVersions

    def copyExtraModules(self):
	kernelVersions = self.kernelVersionList()

        for (path, subdir, name) in self.extraModules:
	    pattern = ""
	    names = ""
	    for n in kernelVersions:
		pattern = pattern + " " + n + "/" + name + ".o"
		names = names + " " + name + ".o"
	    command = ("cd %s/lib/modules; gunzip < %s/modules.cgz | " +
			"%s/bin/cpio  --quiet -iumd %s") % \
		(self.instPath, path, self.instPath, pattern)
	    log("running: '%s'" % (command, ))
	    os.system(command)

	    for n in kernelVersions:
		fromFile = "%s/lib/modules/%s/%s.o" % (self.instPath, n, name)
		toDir = "%s/lib/modules/%s/kernel/drivers/%s" % \
			(self.instPath, n, subdir)
		to = "%s/%s.o" % (toDir, name)

		if (os.access(fromFile, os.R_OK) and 
			os.access(toDir, os.X_OK)):
		    log("moving %s to %s" % (fromFile, to))
		    os.rename(fromFile, to)

		    # the file might not have been owned by root in the cgz
		    os.chown(to, 0, 0)
		else:
		    log("missing DD module %s (this may be okay)" % 
				fromFile)

    def depmodModules(self):
	kernelVersions = self.kernelVersionList()

        for version in kernelVersions:
	    iutil.execWithRedirect ("/sbin/depmod",
                                    [ "/sbin/depmod", "-a", version ],
                                    root = self.instPath, stderr = '/dev/null')

