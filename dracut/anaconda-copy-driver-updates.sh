#!/bin/sh
# copy dup runtime files and downloaded DUPs
cp -ar /tmp/dud* /tmp/DD-* /sysroot/tmp

# copy all modules and firmwares
for dud in /tmp/duds/DD-*; do
    # copy modules and firmwares to the proper directories
    # modules are in <kernel version>/{kernel,updates,extra}/* structure so
    # strip the kernel version and the first directory name of it
    mkdir -p "/sysroot/lib/modules/$(uname -r)/updates" "/sysroot/lib/firmware/updates"
    cp -r $dud/lib/modules/*/*/* "/sysroot/lib/modules/$(uname -r)/updates/"
    cp -r $dud/lib/firmware/* /sysroot/lib/firmware/
done

# regenerate modules.* files
depmod -b /sysroot
