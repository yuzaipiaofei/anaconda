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
import pcmcia
import _balkan
import kudzu
from simpleconfig import SimpleConfigFile
from mouse import Mouse
from xf86config import XF86Config
import errno
import raid
from translate import cat
import timer
import fstab
import time
import re
import gettext_rh
import os.path
import upgrade
from translate import _
from log import log

class Desktop (SimpleConfigFile):
    def __init__ (self):
        SimpleConfigFile.__init__ (self)

    def set (self, desktop):
        self.info ['DESKTOP'] = desktop

class InstSyslog:
    def __init__ (self, root, log):
        self.pid = os.fork ()
        if not self.pid:
            if os.access ("./anaconda", os.X_OK):
                path = "./anaconda"
            elif os.access ("/usr/bin/anaconda.real", os.X_OK):
                path = "/usr/bin/anaconda.real"
            else:
                path = "/usr/bin/anaconda"
            os.execv (path, ("syslogd", "--syslogd", root, log))

    def __del__ (self):
        os.kill (self.pid, 15)
	os.wait (self.pid)
        
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

    def writeDesktop(self):
        desktop = Desktop ()
        desktop.set (self.instClass.getDesktop())
	f = open(self.instPath + "/etc/sysconfig/desktop", "w")
	f.write(str (desktop))
	f.close()

    # XXX
    #def writeKeyboard(self):
	#if self.serial: return
	#f = open(self.instPath + "/etc/sysconfig/keyboard", "w")
	#f.write(str (self.keyboard))
	#f.close()

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

    def copyConfModules (self):
        try:
            inf = open ("/tmp/modules.conf", "r")
        except:
            pass
        else:
            out = open (self.instPath + "/etc/modules.conf", "a")
            out.write (inf.read ())

    def verifyDeps (self):
        def formatRequire (name, version, flags):
            string = name
            
            if flags:
                if flags & (rpm.RPMSENSE_LESS | rpm.RPMSENSE_GREATER | 
                            rpm.RPMSENSE_EQUAL):
                    string = string + " "
                    if flags & rpm.RPMSENSE_LESS:
                        string = string + "<"
                    if flags & rpm.RPMSENSE_GREATER:
                        string = string + ">"
                    if flags & rpm.RPMSENSE_EQUAL:
                        string = string + "="
                    string = string + " %s" % version
            return string

        # if we still have the same packages selected, bail - we don't need to
        # do this again.
        if self.verifiedState == self.comps.getSelectionState()[1]:
            return

        self.verifiedState = None
        
	win = self.intf.waitWindow(_("Dependency Check"),
	  _("Checking dependencies in packages selected for installation..."))
	self.getCompsList()
        if self.upgrade:
	    # the partitions are already mounted
            db = rpm.opendb (0, self.instPath)
            ts = rpm.TransactionSet(self.instPath, db)
        else:
            ts = rpm.TransactionSet()
            
        if self.upgrade:
            how = 'u'
        else:
            how = 'i'
	for p in self.hdList.packages.values ():
            if p.selected:
                ts.add(p.h, (p.h, p.h[rpm.RPMTAG_NAME]), how)
            else:
                ts.add(p.h, (p.h, p.h[rpm.RPMTAG_NAME]), "a")

        deps = ts.depcheck()
        rc = []
        if deps:
            for ((name, version, release),
                 (reqname, reqversion),
                 flags, suggest, sense) in deps:
                if sense == rpm.RPMDEP_SENSE_REQUIRES:
                    if suggest:
                        (header, sugname) = suggest
                        log ("depcheck: package %s needs %s (provided by %s)",
                             name, formatRequire(reqname, reqversion, flags),
                             sugname)
                    else:
                        log ("depcheck: package %s needs %s (not provided)",
                             name, formatRequire(reqname, reqversion, flags))
                        sugname = _("no suggestion")
                    if not (name, sugname) in rc:
                        rc.append ((name, sugname))
                elif sense == rpm.RPMDEP_SENSE_CONFLICTS:
		    # We need to check if the one we are going to
		    # install is ok.
		    conflicts = 1
		    if reqversion:
			fields = string.split(reqversion, '-')
			if (len (fields) == 2):
			    needed = ("", fields [0], fields [1])
			else:
			    needed = ("", fields [0], "")
                        try:
                            h = self.hdList[reqname].h
                        except KeyError:
                            conflicts = 0
			installed = ("", h[rpm.RPMTAG_VERSION],
				     h [rpm.RPMTAG_RELEASE])
			if rpm.labelCompare (installed, needed) >= 0:
			    conflicts = 0

		    if conflicts:
			log ("%s-%s-%s conflicts with to-be-installed "
                             "package %s-%s, removing from set",
                             name, version, release, reqname, reqversion)
			if self.hdList.packages.has_key (reqname):
			    self.hdList.packages[reqname].selected = 0
			    log ("... removed")

        del ts
        if self.upgrade:
            del db

	win.pop()

        if not rc: 
            self.verifiedState = self.comps.getSelectionState()[1]

        return rc

    def selectDeps (self, deps):
        if deps:
            for (who, dep) in deps:
                if dep != _("no suggestion"):
                    try:
                        self.hdList[dep].select ()
                    except KeyError:
                        pass

    def unselectDeps (self, deps):
        if deps:
            for (who, dep) in deps:
                if dep != _("no suggestion"):
                    try:
                        self.hdList[dep].unselect ()
                    except KeyError:
                        pass

    def selectDepCause (self, deps):
        if deps:
            for (who, dep) in deps:
                try:
                    self.hdList[who].select ()
                except KeyError:
                    pass

    def unselectDepCause (self, deps):
        if deps:
            for (who, dep) in deps:
                try:
                    self.hdList[who].unselect ()
                except KeyError:
                    pass

    def canResolveDeps (self, deps):
        canresolve = 0
        if deps:
            for (who, dep) in deps:
                if dep != _("no suggestion"):
                    canresolve = 1
        return canresolve

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

    def rpmError (todo):
        todo.instLog.write (rpm.errorString () + "\n")

    def setClass(todo, instClass):
	# XXX
	return 

	todo.instClass = instClass
	todo.hostname = todo.instClass.getHostname()
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

    def migrateXinetd(self):
        if not os.access (self.instPath + "/usr/sbin/inetdconvert", os.X_OK):
            log("did not find %s" % self.instPath + "/usr/sbin/inetdconvert")
            return

        if not os.access (self.instPath + "/etc/inetd.conf.rpmsave", os.R_OK):
            log("did not run inetdconvert because no inetd.conf.rpmsave found")
            return

        argv = [ "/usr/sbin/inetdconvert", "--convertremaining",
                 "--inetdfile", "/etc/inetd.conf.rpmsave" ]
        
        log("found inetdconvert, executing %s" % argv)

        logfile = os.open (self.instLogName, os.O_APPEND)
        iutil.execWithRedirect(argv[0], argv, root = self.instPath,
                               stdout = logfile, stderr = logfile)
        os.close(logfile)
        
    def instCallback(self, what, amount, total, h, (param)):
	(intf, messageWindow, pkgTimer) = param
        if (what == rpm.RPMCALLBACK_TRANS_START):
            # step 6 is the bulk of the transaction set
            # processing time
            if amount == 6:
                self.progressWindow = \
                   self.intf.progressWindow (_("Processing"),
                                             _("Preparing to install..."),
                                             total)
        if (what == rpm.RPMCALLBACK_TRANS_PROGRESS):
            if self.progressWindow:
                self.progressWindow.set (amount)
                
        if (what == rpm.RPMCALLBACK_TRANS_STOP and self.progressWindow):
            self.progressWindow.pop ()

        if (what == rpm.RPMCALLBACK_INST_OPEN_FILE):
	    # We don't want to start the timer until we get to the first
	    # file.
	    pkgTimer.start()

            intf.setPackage(h)
            intf.setPackageScale(0, 1)
            self.instLog.write (self.modeText % (h[rpm.RPMTAG_NAME],))
            self.instLog.flush ()
            fn = self.method.getFilename(h, pkgTimer)

	    self.rpmFD = -1
	    while self.rpmFD < 0:
		try:
		    self.rpmFD = os.open(fn, os.O_RDONLY)
		    # Make sure this package seems valid
		    try:
			(h, isSource) = rpm.headerFromPackage(self.rpmFD)
			os.lseek(self.rpmFD, 0, 0)
		    except:
			self.rpmFD = -1
			os.close(self.rpmFD)
			raise SystemError
		except:
		    messageWindow(_("Error"),
			_("The file %s cannot be opened. This is due to "
			  "a missing file, a bad package, or bad media. "
			  "Press <return> to try again.") % fn)

            fn = self.method.unlinkFilename(fn)
            return self.rpmFD
        elif (what == rpm.RPMCALLBACK_INST_PROGRESS):
            if total:
                intf.setPackageScale(amount, total)
        elif (what == rpm.RPMCALLBACK_INST_CLOSE_FILE):
            os.close (self.rpmFD)
            intf.completePackage(h, pkgTimer)
        else:
            pass

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

    def writeConfiguration(self):
        self.writeLanguage ()
        self.writeMouse ()
        self.writeKeyboard ()
        self.writeNetworkConfig ()
        self.setupAuthentication ()
	self.setupFirewall ()
        self.writeRootPassword ()
        self.createAccounts ()

        self.writeTimezone()

    def sortPackages(self, first, second):
        # install packages in cd order (cd tag is 1000002)
	one = None
	two = None

        if first[1000003] != None:
	    one = first[1000003]

        if second[1000003] != None:
	    two = second[1000003]

        if one == None or two == None:
            one = 0
            two = 0
            if first[1000002] != None:
                one = first[1000002]

            if second[1000002] != None:
                two = second[1000002]

	if one < two:
	    return -1
	elif one > two:
	    return 1
	elif string.lower(first[rpm.RPMTAG_NAME]) < string.lower(second[rpm.RPMTAG_NAME]):
	    return -1
	elif string.lower(first[rpm.RPMTAG_NAME]) > string.lower(second[rpm.RPMTAG_NAME]):
	    return 1

	return 0

    def doInstall(self):
	# make sure we have the header list and comps file
	self.getHeaderList()
	self.getCompsList()

        arch = iutil.getArch ()

        if arch == "alpha":
            # if were're on alpha with ARC console, set the clock
            # so that our installed files won't be in the future
            if onMILO ():
                args = ("clock", "-A", "-s")
                try:
                    iutil.execWithRedirect('/usr/sbin/clock', args)
                except:
                    pass

        if not self.upgrade:
            # this is NICE and LATE. It lets kickstart/server/workstation
            # installs detect this properly
            if (self.hdList.has_key('kernel-smp') and isys.smpAvailable()):
                self.hdList['kernel-smp'].selected = 1

            if (self.hdList.has_key('kernel-enterprise')):
                import lilo

                if lilo.needsEnterpriseKernel():
                    self.hdList['kernel-enterprise'].selected = 1

            # we *always* need a kernel installed
            if (self.hdList.has_key('kernel')):
                self.hdList['kernel'].selected = 1

            # if NIS is configured, install ypbind and dependencies:
            if self.auth.useNIS:
                self.hdList['ypbind'].selected = 1
                self.hdList['yp-tools'].selected = 1
                self.hdList['portmap'].selected = 1

            if self.auth.useLdap:
                self.hdList['nss_ldap'].selected = 1
                self.hdList['openldap'].selected = 1
                self.hdList['perl'].selected = 1

            if self.auth.useKrb5:
                self.hdList['pam_krb5'].selected = 1
                self.hdList['krb5-workstation'].selected = 1
                self.hdList['krbafs'].selected = 1
                self.hdList['krb5-libs'].selected = 1

            if (self.x.server
                and self.hdList.packages.has_key('XFree86')
                and self.hdList.packages['XFree86'].selected
                and self.x.server != "XFree86"):
                # trim off the XF86_
                try:
                    self.selectPackage ('XFree86-' + self.x.server[5:])
                except ValueError, message:
                    log ("Error selecting XFree86 server package: %s", message)

        # make sure that all comps that include other comps are
        # selected (i.e. - recurse down the selected comps and turn
        # on the children
        if self.setupFilesystems:
            if not self.upgrade:
		if (self.ddruidAlreadySaved):
		    self.fstab.makeFilesystems ()
		else:
		    self.fstab.savePartitions ()
		    self.fstab.makeFilesystems ()
		    self.fstab.turnOnSwap(self.instPath)

	    # We do this for upgrades, even though everything is already
	    # mounted. While this may seem a bit strange, we reference
	    # count the mounts, which is easier then special casing
	    # the mount/unmounts all the way through
            self.fstab.mountFilesystems (self.instPath)

	self.method.mergeFullHeaders(self.hdList)

        if self.upgrade:
	    # An old mtab can cause confusion (esp if loop devices are
	    # in it)
	    f = open(self.instPath + "/etc/mtab", "w+")
	    f.close()

	if self.method.systemMounted (self.fstab, self.instPath, self.hdList.selected()):
	    self.fstab.umountFilesystems(self.instPath)
	    return 1

	if not self.installSystem: 
	    return

	for i in ( '/var', '/var/lib', '/var/lib/rpm', '/tmp', '/dev', '/etc',
                   '/etc/sysconfig', '/etc/sysconfig/network-scripts',
                   '/etc/X11' ):
	    try:
	        os.mkdir(self.instPath + i)
	    except os.error, (errno, msg):
                # self.intf.messageWindow("Error", "Error making directory %s: %s" % (i, msg))
                pass

	db = rpm.opendb(1, self.instPath)
	ts = rpm.TransactionSet(self.instPath, db)

        total = 0
	totalSize = 0

        if self.upgrade:
            how = "u"
        else:
            how = "i"

	l = []

	for p in self.hdList.selected():
            l.append(p)
	l.sort(self.sortPackages)

	for p in l:
            ts.add(p.h, p.h, how)
            total = total + 1
            totalSize = totalSize + (p[rpm.RPMTAG_SIZE] / 1024 )

        if not self.hdList.preordered():
            log ("WARNING: not all packages in hdlist had order tag")
            ts.order()

        if self.upgrade:
            logname = '/tmp/upgrade.log'
        else:
            logname = '/tmp/install.log'

        self.instLogName = self.instPath + logname
        try:
            os.unlink (self.instLogName)
        except OSError:
            pass
	self.instLog = open(self.instLogName, "w+")
	syslog = InstSyslog (self.instPath, self.instPath + logname)

	ts.scriptFd = self.instLog.fileno ()
	# the transaction set dup()s the file descriptor and will close the
	# dup'd when we go out of scope

	p = self.intf.packageProgressWindow(total, totalSize)

        if self.upgrade:
            self.modeText = _("Upgrading %s.\n")
        else:
            self.modeText = _("Installing %s.\n")

        oldError = rpm.errorSetCallback (self.rpmError)
	pkgTimer = timer.Timer(start = 0)

        problems = ts.run(0, ~rpm.RPMPROB_FILTER_DISKSPACE,
                          self.instCallback, 
			  (p, self.intf.messageWindow, pkgTimer))

#        problems = ts.run(rpm.RPMTRANS_FLAG_TEST, ~0,
#                          self.instCallback, (p, self.intf.messageWindow))

        if problems:
            spaceneeded = {}
            nodeneeded = {}
            size = 12

            # XXX
            nodeprob = -1
            if rpm.__dict__.has_key ("RPMPROB_DISKNODES"):
                nodeprob = rpm.RPMPROB_DISKNODES

            for (descr, (type, mount, need)) in problems:
                idx = string.find (mount, "/mnt/sysimage")
		if mount[0:13] == "/mnt/sysimage":
                    mount = mount[13:]
		    if not mount:
			mount = '/'

                if type == rpm.RPMPROB_DISKSPACE:
                    if spaceneeded.has_key (mount) and spaceneeded[mount] < need:
                        spaceneeded[mount] = need
                    else:
                        spaceneeded[mount] = need
                elif type == nodeprob:
                    if nodeneeded.has_key (mount) and nodeneeded[mount] < need:
                        nodeneeded[mount] = need
                    else:
                        nodeneeded[mount] = need
                else:
                    log ("WARNING: unhandled problem returned from transaction set type %d",
                         type)

            probs = ""
            if spaceneeded:
                probs = probs + _("You don't appear to have enough disk space to install "
                                  "the packages you've selected. You need more space on the "
                                  "following filesystems:\n\n")
                probs = probs + ("%-15s %s\n") % (_("Mount Point"), _("Space Needed"))

                for (mount, need) in spaceneeded.items ():
                    if need > (1024*1024):
                        need = (need + 1024 * 1024 - 1) / (1024 * 1024)
                        suffix = "M"
                    else:
                        need = (need + 1023) / 1024
                        suffix = "k"

                    prob = "%-15s %d %c\n" % (mount, need, suffix)
                    probs = probs + prob
            if nodeneeded:
                if probs:
                    probs = probs + '\n'
                probs = probs + _("You don't appear to have enough file nodes to install "
                                  "the packages you've selected. You need more file nodes on the "
                                  "following filesystems:\n\n")
                probs = probs + ("%-15s %s\n") % (_("Mount Point"), _("Nodes Needed"))

                for (mount, need) in nodeneeded.items ():
                    prob = "%-15s %d\n" % (mount, need)
                    probs = probs + prob

            self.intf.messageWindow (_("Disk Space"), probs)

	    del ts
	    del db
	    self.instLog.close()
	    del syslog

	    self.method.systemUnmounted ()
	    self.fstab.umountFilesystems(self.instPath)
            
            rpm.errorSetCallback (oldError)
            return 1

        # This should close the RPM database so that you can
        # do RPM ops in the chroot in a %post ks script
        del ts
        del db
        rpm.errorSetCallback (oldError)
        
        self.method.filesDone ()
        
        del p

        if self.upgrade:
            self.instLog.write ("\n\nThe following packages were available on the CD but NOT upgraded:\n")
            for p in self.hdList.packages.values ():
                if not p.selected:
                    self.instLog.write("%s-%s-%s.%s.rpm\n" %
                                       (p.h[rpm.RPMTAG_NAME],
                                        p.h[rpm.RPMTAG_VERSION],
                                        p.h[rpm.RPMTAG_RELEASE],
                                        p.h[rpm.RPMTAG_ARCH]))
        self.instLog.close ()

	createWindow = (self.intf.progressWindow,
			(_("Post Install"),
			 _("Performing post install configuration..."), 8))
	w = apply(apply, createWindow)

        try:
            if not self.upgrade:
                if self.fdDevice[0:2] == "fd":
                    self.fstab.addMount(self.fdDevice, "/mnt/floppy", "auto")

		w.set(1)

                self.copyExtraModules()
                self.fstab.write (self.instPath)
                self.writeConfiguration ()
                self.writeDesktop ()
                if (self.instClass.defaultRunlevel):
                    self.initlevel = self.instClass.defaultRunlevel
                    self.setDefaultRunlevel ()

		w.set(2)

                # pcmcia is supported only on i386 at the moment
                if arch == "i386":
                    pcmcia.createPcmciaConfig(
			    self.instPath + "/etc/sysconfig/pcmcia")
			   
                self.copyConfModules ()
                if not self.x.skip and self.x.server:
                    if os.access (self.instPath + "/etc/X11/X", os.R_OK):
                        os.rename (self.instPath + "/etc/X11/X",
                                   self.instPath + "/etc/X11/X.rpmsave")
                    try:
                        os.unlink (self.instPath + "/etc/X11/X")
                    except OSError:
                        pass
                    os.symlink ("../../usr/X11R6/bin/" + self.x.server,
                                self.instPath + "/etc/X11/X")

                    self.x.write (self.instPath + "/etc/X11")
                self.setDefaultRunlevel ()

		w.set(3)

                # blah.  If we're on a serial mouse, and we have X, we need to
                # close the mouse device, then run kudzu, then open it again.

                # turn it off
                mousedev = None

                # XXX currently Bad Things (X async reply) happen when doing
                # Mouse Magic on Sparc (Mach64, specificly)
                if os.environ.has_key ("DISPLAY") and not arch == "sparc":
                    import xmouse
                    try:
                        mousedev = xmouse.get()[0]
                    except RuntimeError:
                        pass

                if mousedev:
                    try:
                        os.rename (mousedev, "/dev/disablemouse")
                    except OSError:
                        pass
                    try:
                        xmouse.reopen()
                    except RuntimeError:
                        pass

                log("Mounting /proc/bus/usb in install path")
                unmountUSB = 0
                try:
                    isys.mount('/usbdevfs', self.instPath+'/proc/bus/usb', 'usbdevfs')
                    log("Mount of USB succeeded")
                    unmountUSB = 1
                except:
                    log("Mount of USB failed")
                    pass

                    
                argv = [ "/usr/sbin/kudzu", "-q" ]
                devnull = os.open("/dev/null", os.O_RDWR)
                iutil.execWithRedirect(argv[0], argv, root = self.instPath,
                                       stdout = devnull)
                # turn it back on            
                if mousedev:
                    try:
                        os.rename ("/dev/disablemouse", mousedev)
                    except OSError:
                        pass
                    try:
                        xmouse.reopen()
                    except RuntimeError:
                        pass
                if unmountUSB:
                    isys.umount(self.instPath + '/proc/bus/usb', removeDir = 0)

	    w.set(4)

            if self.upgrade:
                # move the rebuilt db into place.
                try:
                    iutil.rmrf (self.instPath + "/var/lib/rpm.rpmsave")
                except OSError:
                    pass
                os.rename (self.instPath + "/var/lib/rpm",
                           self.instPath + "/var/lib/rpm.rpmsave")
                os.rename (self.instPath + self.dbpath,
                           self.instPath + "/var/lib/rpm")

                # XXX - rpm 4.0.2 %post braindeadness support
                try:
                    os.unlink (self.instPath + "/etc/rpm/macros.db1")
                except OSError:
                    pass

                # needed for prior systems which were not xinetd based
                self.migrateXinetd()

            # XXX make me "not test mode"
            if self.setupFilesystems:
		errors = None

                if arch == "sparc":
                    errors = self.silo.install (self.fstab, self.instPath, 
					self.hdList, self.upgrade)
                elif arch == "i386":
                    defaultlang = self.language.getLangNickByName(self.language.getDefault())
                    langlist = expandLangs(defaultlang)
                    errors = self.lilo.install (self.fstab, self.instPath, 
					self.hdList, self.upgrade, langlist)
                elif arch == "ia64":
                    errors = self.eli.install (self.fstab, self.instPath, 
					self.hdList, self.upgrade)
                elif arch == "alpha":
                    errors = self.milo.write ()
                else:
                    raise RuntimeError, "What kind of machine is this, anyway?!"

		if errors:
		    w.pop()
		    mess = _("An error occured while installing "
			     "the bootloader.\n\n"
                             "We HIGHLY recommend you make a recovery "
                             "boot floppy when prompted, otherwise you "
                             "may not be able to reboot into Red Hat Linux."
                             "\n\nThe error reported was:\n\n") + errors
		    self.intf.messageWindow(_("Bootloader Errors"), mess)

                    # make sure bootdisk window appears
                    if iutil.getArch () == "i386":
                        self.instClass.removeFromSkipList('bootdisk')
                        self.bootdisk = 1

		    w = apply(apply, createWindow)


		w.set(5)

                # go ahead and depmod modules as modprobe in rc.sysinit
                # will complain loaduly if we don't do it now.
                self.depmodModules()

	    w.set(6)

            self.instClass.postAction(self.instPath, self.serial)

	    w.set(7)

            if self.setupFilesystems:
                f = open("/tmp/cleanup", "w")
                self.method.writeCleanupPath(f)
                self.fstab.writeCleanupPath(f)
                f.close()

	    w.set(8)

            del syslog

        finally:
            w.pop ()
        sys.stdout.flush()
