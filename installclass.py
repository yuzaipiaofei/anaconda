# this is the prototypical class for workstation, server, and kickstart 
# installs
#
# The interface to InstallClass is *public* -- ISVs/OEMs can customize the
# install by creating a new derived type of this class.

# putting these here is a bit of a hack, but we can't switch between
# newtfsedit and gnomefsedit right now, so we have to put up with this
FSEDIT_CLEAR_LINUX  = (1 << 1)
FSEDIT_CLEAR_ALL    = (1 << 2)
FSEDIT_USE_EXISTING = (1 << 3)

import gettext_rh, os, iutil
from xf86config import XF86Config
from translate import _

class InstallClass:

    # look in mouse.py for a list of valid mouse names -- use the LONG names
    def setMouseType(self, name, device = None, emulateThreeButtons = 0):
	self.mouse = (name, device, emulateThreeButtons)

    def setLiloInformation(self, location, linear = 1, appendLine = None):
	# this throws an exception if there is a problem
	["mbr", "partition", None].index(location)

	self.lilo = (location, linear, appendLine)

    def setClearParts(self, clear, warningText = None):
	self.clearParts = clear
        # XXX hack for install help text in GUI mode
        if clear == FSEDIT_CLEAR_LINUX:
            self.clearType = "wkst"
        if clear == FSEDIT_CLEAR_ALL:
            self.clearType = "svr"        
	self.clearPartText = warningText

    def getLiloInformation(self):
	return self.lilo

    def getFstab(self):
	return self.fstab

    def addRaidEntry(self, mntPoint, raidDev, level, devices):
	# throw an exception for bad raid levels
	[ 0, 1, 5 ].index(level)
	for device in devices:
	    found = 0
	    for (otherMountPoint, size, maxSize, grow, forceDevice) in \
			self.partitions:
		if otherMountPoint == device:
		    found = 1
	    if not found:
		raise ValueError, "unknown raid device %s" % (device,)
	if mntPoint[0] != '/' and mntPoint != 'swap':
	    raise ValueError, "bad raid mount point %s" % (mntPoint,)
	if raidDev[0:2] != "md":
	    raise ValueError, "bad raid device point %s" % (raidDev,)
	if level == 5 and len(devices) < 3:
	    raise ValueError, "raid 5 arrays require at least 3 devices"
	if len(devices) < 2:
	    raise ValueError, "raid arrays require at least 2 devices"

	self.raidList.append(mntPoint, raidDev, level, devices)	

    def addNewPartition(self, mntPoint, size, maxSize, grow, device):
	if not device: device = ""

	if mntPoint[0] != '/' and mntPoint != 'swap' and \
		mntPoint[0:5] != "raid.":
	    raise TypeError, "bad mount point for partitioning: %s" % \
		    (mntPoint,)
	self.partitions.append((mntPoint, size, maxSize, grow, device))

    def addToFstab(self, mntpoint, dev, fstype = "ext2" , reformat = 1):
	self.fstab.append((mntpoint, (dev, fstype, reformat)))

    def setTimezoneInfo(self, timezone, asUtc = 0, asArc = 0):
	self.timezone = (timezone, asUtc, asArc)

    def getTimezoneInfo(self):
	return self.timezone

    def removeFromSkipList(self, type):
	if self.skipSteps.has_key(type):
	    del self.skipSteps[type]

    def addToSkipList(self, type):
	# this throws an exception if there is a problem
	[ "lilo", "mouse", "network", "authentication", "complete", "complete",
	  "package-selection", "bootdisk", "partition", "format", "timezone",
	  "accounts", "dependencies", "language", "keyboard", "xconfig",
	  "welcome", "custom-upgrade", "installtype", "mouse", 
	  "confirm-install" ].index(type)
	self.skipSteps[type] = 1

    def setHostname(self, hostname):
	self.hostname = hostname

    def getHostname(self):
	return self.hostname

    def setAuthentication(self, useShadow, useMd5, useNIS = 0, nisDomain = "",
			  nisBroadcast = 0, nisServer = ""):
	self.auth = ( useShadow, useMd5, useNIS, nisDomain, nisBroadcast,
		      nisServer)

    def getAuthentication(self):
	return self.auth

    def skipStep(self, step):
	return self.skipSteps.has_key(step)

    def configureX(self, server, card, monitor, hsync, vsync, noProbe, startX):
	self.x = XF86Config(mouse = None)
	if (not noProbe):
	    self.x.probe()

	if not self.x.server:
	    self.x.setVidcard (card)

	if not self.x.monID and monitor:
	    self.x.setMonitor((monitor, (None, None)))
	elif hsync and vsync:
	    self.x.setMonitor((None, (hsync, vsync)))

	if startX:
	    self.defaultRunlevel = 5

    # Groups is a list of group names -- the full list can be found in 
    # ths comps file for each release
    def setGroups(self, groups):
	self.groups = groups

    def getGroups(self):
	return self.groups

    # This is a list of packages -- it is combined with the group list
    def setPackages(self, packages):
	self.packages = packages

    def getPackages(self):
	return self.packages

    def doRootPw(self, pw, isCrypted = 0):
	self.rootPassword = pw
	self.rootPasswordCrypted = isCrypted

    def getMakeBootdisk(self):
	return self.makeBootdisk

    def setMakeBootdisk(self, state):
	self.makeBootdisk = state 

    def setNetwork(self, bootproto, ip, netmask, gateway, nameserver):
	self.bootProto = bootproto
	self.ip = ip
	self.netmask = netmask
	self.gateway = gateway
	self.nameserver = nameserver

    def setZeroMbr(self, state):
	self.zeroMbr = state

    def getNetwork(self):
	return (self.bootProto, self.ip, self.netmask, self.gateway, 
		self.nameserver)

    def setEarlySwapOn(self, state = 0):
	self.earlySwapOn = state

    def setLanguage(self, lang):
	self.language = lang

    def setKeyboard(self, kb):
	self.keyboard = kb

    def setPostScript(self, postScript, inChroot = 1):
	self.postScript = postScript
	self.postInChroot = inChroot

    def __init__(self):
	self.skipSteps = {}
	self.hostname = None
	self.lilo = ("mbr", 1, "")
	self.groups = None
	self.packages = None
	self.makeBootdisk = 0
	self.timezone = None
	self.setAuthentication(1, 1, 0)
	self.rootPassword = None
	self.rootPasswordCrypted = 0
	self.installType = None
	self.bootProto = None
	self.ip = ""
	self.netmask = ""
	self.gateway = ""
	self.nameserver = ""
	self.partitions = []
	self.clearParts = 0
        self.clearType = None
	self.clearText = None
	self.clearPartText = None
	self.zeroMbr = 0
	self.language = None
	self.keyboard = None
	self.mouse = None
	self.x = None
	self.defaultRunlevel = None
	self.postScript = None
	self.postInChroot = 0
	self.fstab = []
	self.earlySwapOn = 0
        self.desktop = ""
	self.raidList = []

        if iutil.getArch () == "alpha":
            self.addToSkipList("bootdisk")
            self.addToSkipList("lilo")

# we need to be able to differentiate between this and custom
class DefaultInstall(InstallClass):

    def __init__(self, expert):
	InstallClass.__init__(self)

# custom installs are easy :-)
class CustomInstall(InstallClass):

    def __init__(self, expert):
	InstallClass.__init__(self)

# GNOME and KDE installs are derived from this
class Workstation(InstallClass):

    def __init__(self, expert):
	InstallClass.__init__(self)
	self.setHostname("localhost.localdomain")
	if not expert:
	    self.addToSkipList("lilo")
	self.addToSkipList("authentication")
	self.addToSkipList("package-selection")
	self.setMakeBootdisk(1)

	if os.uname ()[4] != 'sparc64':
	    self.addNewPartition('/boot', 16, -1, 0, None)
	self.addNewPartition('/', 700, -1, 1, None)
	self.addNewPartition('swap', 64, -1, 0, None)
	self.setClearParts(FSEDIT_CLEAR_LINUX, 
	    warningText = _("You are about to erase any preexisting Linux "
			    "installations on your system."))
class ClusterServer(InstallClass):

    def __init__(self, expert):
	InstallClass.__init__(self)
	self.setGroups(["Cluster Server"])
	self.setHostname("localhost.localdomain")
	if not expert:
	    self.addToSkipList("lilo")
	self.addToSkipList("package-selection")
	self.addToSkipList("authentication")
	self.setMakeBootdisk(1)
	self.setPostScript(
"""
echo "* Security script for HA started" >&2

# The purpose of this script is to turn off any and all non
# essential services. As we are flagging security as an issue
# we will turn off almost all network services. The LVS routers
# themselves should not provide services but masqarade those
# services through to the second layer of hosts.
# Consequently it is now the responsibility of the system administrator
# to enable services on the LVS boxes that he/she deems fit and proper.

# For LVS use, the following services should be turned off
# They should not be automatically started
# the output from this is directed to null for services that may not
# be installed
# 
/sbin/chkconfig --del netfs	 > /dev/null 2>&1
/sbin/chkconfig --del xfs	 > /dev/null 2>&1
/sbin/chkconfig --del named	 > /dev/null 2>&1
/sbin/chkconfig --del identd	 > /dev/null 2>&1
/sbin/chkconfig --del innd	 > /dev/null 2>&1
/sbin/chkconfig --del linuxconf	 > /dev/null 2>&1
/sbin/chkconfig --del lpd	 > /dev/null 2>&1
/sbin/chkconfig --del nfs	 > /dev/null 2>&1
/sbin/chkconfig --del nfslock	 > /dev/null 2>&1
/sbin/chkconfig --del pulse	 > /dev/null 2>&1
/sbin/chkconfig --del pvmd	 > /dev/null 2>&1
/sbin/chkconfig --del rusersd	 > /dev/null 2>&1
/sbin/chkconfig --del rwalld	 > /dev/null 2>&1
/sbin/chkconfig --del smb	 > /dev/null 2>&1
/sbin/chkconfig --del sendmail	 > /dev/null 2>&1
/sbin/chkconfig --del snmpd	 > /dev/null 2>&1
/sbin/chkconfig --del ypbind	 > /dev/null 2>&1
/sbin/chkconfig --del yppasswdd	 > /dev/null 2>&1
/sbin/chkconfig --del ypserv	 > /dev/null 2>&1
/sbin/chkconfig --del ldap	 > /dev/null 2>&1
/sbin/chkconfig --del autofs	 > /dev/null 2>&1
/sbin/chkconfig --del pcmcia	 > /dev/null 2>&1
/sbin/chkconfig --del mars-nwe	 > /dev/null 2>&1

# I honestly can't see a reason to let any service run
# even telnet. As such, comment out ALL services
# but leave it in such a manner that the inetd.conf entries can
# be easily reenabled
#
#/bin/mv /etc/inetd.conf /etc/inetd.conf.orig
#/bin/cat /etc/inetd.conf.orig | /bin/sed -e 's,^[a-z],#\\0,' > /etc/inetd.conf
#/bin/sed -e 's/#shell/shell/' < /etc/inetd.conf > /etc/inetd.conf.orig
#/bin/sed -e 's/#login/login/' < /etc/inetd.conf.orig > /etc/inetd.conf

# TCP Wrappers
# Even if services are turned on, we should deny EVERYTHING by default
# A Few example lines are added to /etc/hosts.allow for referance
# This is an extra safeguard that should be enabled in a secure enviroment
#
echo "# you could extend this file beyond the basic ALL:ALL" >> /etc/hosts.deny
echo "# See man hosts.deny for more details" >> /etc/hosts.deny
echo "ALL: ALL" >> /etc/hosts.deny

echo "# Please replace 'myhost.mydomain.org' and IP address with your" >> /etc/hosts.allow 
echo "# other participating cluster node." >> /etc/hosts.allow
echo "# Don't forget to remove the leading # to enable!" >> /etc/hosts.allow
echo "# See man hosts.allow for more details" >> /etc/hosts.allow

echo "# in.telnetd: myhost.mydomain.org 127.0.0.1" >> /etc/hosts.allow
echo "# in.ftp:     myhost.mydomain.org 127.0.0.1" >> /etc/hosts.allow
echo "# in.rshd:    myhost.mydomain.org 127.0.0.1" >> /etc/hosts.allow
echo "# in.rlogind: myhost.mydomain.org 127.0.0.1" >> /etc/hosts.allow

# Example rhost file for root
#
echo "# Replace the <hostname> with your other participating cluster node name" > /root/.rhosts
echo "# <hostname> root" > /root/.rhosts

# Passwords by default should rotate on a regular basis
# /etc/login.defs offers a mechanism to tweek the defaults
# 30 day rotation
#
/bin/mv /etc/login.defs /etc/login.defs.orig
/bin/sed -e 's/99999/30/' < /etc/login.defs.orig > /etc/login.defs

# System logging
# System logs should he held minimally for 60 days to cover legal
# requirements for most contries.
# There are other places this should be implemented however those services
# are not enabled by default (eg squid)
#
/bin/mv /etc/logrotate.conf /etc/logrotate.conf.orig
/bin/sed -e 's/rotate 4/rotate 9/' < /etc/logrotate.conf.orig > /etc/logrotate.conf

echo "* Security script for HA completed, Altering the MOTD" >&2
echo "" > /etc/motd
echo "Red Hat Highly Available Server 1.0" >> /etc/motd
echo "" >> /etc/motd 
echo "" >> /etc/motd

""")


# reconfig machine w/o reinstall
class ReconfigStation(InstallClass):

    def __init__(self, expert):
	InstallClass.__init__(self)
	self.setHostname("localhost.localdomain")
	self.addToSkipList("lilo")
	self.addToSkipList("bootdisk")
	self.addToSkipList("partition")
	self.addToSkipList("package-selection")
	self.addToSkipList("format")
        self.addToSkipList("mouse")
        self.addToSkipList("xconfig")
