# livepayload.py
# Live media software payload management.
#
# Copyright (C) 2012  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): David Lehman <dlehman@redhat.com>
#

"""
    TODO
        - error handling!!!
        - document all methods
        - LiveImagePayload
            - register the live image, either via self.data.method or in setup
              using storage

"""
import os
import stat

from . import *

from pyanaconda.constants import *
from pyanaconda.flags import flags

from pyanaconda import iutil

import logging
log = logging.getLogger("anaconda")

from pyanaconda.errors import *
from pyanaconda import progress
from pyanaconda.storage.size import Size

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

class LiveImagePayload(ImagePayload):
    """ A LivePayload copies the source image onto the target system. """
    def setup(self, storage):
        if not os.path.ismount("/run/initramfs/live"):
            exn = PayloadSetupError("live image is not mounted")
            if errorHandler.cb(exn) == ERROR_RAISE:
                raise exn

    def preInstall(self, packages=None, groups=None):
        """ Perform pre-installation tasks. """
        super(LiveImagePayload, self).preInstall(packages=packages, groups=groups)
        progress.send_message(_("Installing software"))

    def install(self):
        """ Install the payload. """
        cmd = "rsync"
        # preserve: permissions, owners, groups, ACL's, xattrs, times,
        #           symlinks, hardlinks
        # go recursively, include devices and special files, don't cross
        # file system boundaries, print processed files
        args = ["-pogAXtlHrDxv", "/", ROOT_PATH]
        try:
            rc = iutil.execWithRedirect(cmd, args,
                                        stderr="/dev/tty5", stdout="/dev/tty5")
        except (OSError, RuntimeError) as e:
            err = str(e)
        else:
            err = None
            if rc != 0:
                err = "%s exited with code %d" % (cmd, rc)

        if err:
            exn = PayloadInstallError(err)
            if errorHandler.cb(exn) == ERROR_RAISE:
                raise exn

    @property
    def spaceRequired(self):
        return Size(bytes=iutil.getDirSize("/")*1024)