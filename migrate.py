#
# migrate.py - Anaconda config migration procedure
#
# Copyright 2004 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import os
import os.path
import md5
import rpm
import shutil

from flags import flags
from product import *

from rhpl.log import log
from rhpl.translate import _

def findConfig(intf, id, instPath, dir):
    rpm.addMacro("_dbPath",instPath + "/var/lib/rpm")
    ts=rpm.ts()
    mi=ts.dbMatch()
    configs=[]

    win = intf.waitWindow(_("Finding"), _("Finding existing config files..."))

    for h in mi:
        names=h['filenames']
        fileflags=h['fileflags']
        md5sums=h['filemd5s']
        total=len(names)

        for i in xrange(total):
            if (fileflags[i] & rpm.RPMFILE_CONFIG) and not (fileflags[i] & rpm.RPMFILE_GHOST) \
                and isModified(names[i],md5sums[i],instPath):
                    configs.append(names[i])
    win.pop()
    config_full=addWhiteListed(instPath,configs)
    backupConfig(instPath,config_full)

def backupConfig(instPath,configs):
    backupDir="%s/var/backup/%s-%s" %( instPath,productPath,productVersion)
#TODO: exception handling
    os.makedirs(backupDir)
    for config in configs:
        d=os.path.dirname(config)
        if not os.path.exists(backupDir+d):
            os.makedirs(backupDir+d)
        shutil.copy(instPath+config,backupDir+d)
        
def addWhiteListed(instPath,configs):
#TODO: whitelist/blacklist and do something meaningful
    whitelist = ("/etc/hosts",
                "/etc/sysconfig/clock",
                "/etc/sysconfig/desktop",
                "/etc/sysconfig/grub",
                "/etc/sysconfig/hwconf",
                "/etc/sysconfig/i18n",
                "/etc/sysconfig/installinfo",
                "/etc/sysconfig/iptables",
                "/etc/sysconfig/keyboard",
                "/etc/sysconfig/mouse",
                "/etc/sysconfig/netdump_id_dsa",
                "/etc/sysconfig/netdump_id_dsa.pub",
                "/etc/sysconfig/network",
                "/etc/sysconfig/selinux",
                "/etc/ssh/ssh_host_dsa_key.pub",
                "/etc/ssh/ssh_host_key.pub",
                "/etc/ssh/ssh_host_dsa_key",
                "/etc/ssh/ssh_host_key",
                "/etc/ssh/ssh_host_rsa_key",
                "/etc/ssh/ssh_host_rsa_key.pub",
                "/etc/httpd/conf/ssl.key/server.key",
                "/etc/httpd/conf/ssl.crt/server.crt")

    for file in whitelist:
        if os.path.exists(instPath + file):
            configs.append(file)
    return configs

def isModified(fileName, fileMD5, root="/"):
    m = md5.new()
    try:
        f = open (root+fileName, "r")
    except:
        return 0
    data = f.read()
    f.close()
    m.update(data)
    if fileMD5 != m.hexdigest():
        return 1
    else: 
        return 0
