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
import md5
import rpm

from flags import flags

def findConfig(intf, id, instPath, dir):
    rpm.addMacro("_dbPath",instPath + "/var/lib/rpm")
    ts=rpm.ts()
    mi=ts.dbMatch()
    configs=[]

#TODO: Add progress bar
    for h in mi:
        names=h['filenames']
        fileflags=h['fileflags']
        md5sums=h['filemd5s']
        total=len(names)

        for i in xrange(total):
            if (fileflags[i] & rpm.RPMFILE_CONFIG) and not (fileflags[i] & rpm.RPMFILE_GHOST) \
                and isModified(names[i],md5sums[i],instPath):
                    configs.append(names[i])
#TODO: whitelist/blacklist and do something meaningful
    if flags.test:
        print configs

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
