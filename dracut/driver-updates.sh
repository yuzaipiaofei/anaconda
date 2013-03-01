#!/bin/sh

# load the dracut libs
command -v getarg >/dev/null || . /lib/dracut-lib.sh
. /lib/url-lib.sh

# load the anaconda lib
. /lib/anaconda-lib.sh

# check if the DUD has the proper signature file
# and contains rpms for the given architecture
function dud_check()
{
    localdud=$1
    arch=$2

    [ -e "$localdud/rhdd3" -a -e "$localdud/rpms/$arch" ];
}

# copy the rpm repository to RAM so we can eject the media
function dud_copy()
{
    localdud=$1
    arch=$2
    dest=$3

    cp -ar "$localdud/rpms/$arch" "$dest"
}

#dud_contents <driverdisc> <arch> <kernel> <anaconda>
function dud_contents()
{
    KERNEL=${3:-`uname -r`}
    ANACONDA=${4:-"master"}
    ARCH=${2:-`uname -m`}
    localdud=$1

    "/bin/dud_list" -k "$KERNEL" -a "$ANACONDA" -d "$localdud"
}

# filter the driver update list so only the modules
# meant for instalation are in it
# TODO 7.1 there is no implementation of the rule mechanism atm.
function dud_rules()
{
    cat
}

# extract driver update rpms selected for installation
# the list is passed using standard input
function dud_extract()
{
    repo=$1
    dest=$2

    read rpm args
    while [ "x$rpm" != "x" ]; do
        echo "Extracting driver update rpm $rpm"

        pushd $dest
        "/bin/dud_extract" $args --rpm=$rpm --directory=.
        popd

        read rpm args
    done
}

# stdin -> input data
# dud_parse x|. (default value)
function dud_parse()
{
    default=$1

    read L
    while [ "x$L" != "x" ]; do
        SELECTED+=("$default")
        FILES+=("$L")
        read L
        MODULES+=("$L")
        read L
        FLAGS+=("$L")
        read L
        DESCTMP=""
        while [ "x$L" != "x---" ]; do
            DESCTMP="$DESCTMP\n$L"
            read L
        done
        DESCRIPTIONS+=("$DESCTMP")
        read L
    done
}

# dud_select <title line> <input data> [<default value> [noninteractive]]
# This is the (non)interactive part of module selection,
# the user can select drivers to install using simple text interface
# The list of selected modules gets printed out to the 3rd filedes
function dud_select()
{
    MODULES=()
    FILES=()
    DESCRIPTIONS=()
    FLAGS=()
    SELECTED=()

    DEFAULT=${3:-"."}
    MODE=${4:-"interactive"}

    dud_parse $DEFAULT <$2

    if [ $MODE == "interactive" ]; then
        L="x"
    else
        L=""
    fi

    # TUI
    while [ "x$L" != "x" -a ${#MODULES[*]} -gt 0 ]; do
        # header
        clear
        echo $1
        echo

        for i in "${!FLAGS[@]}"; do
            echo $i ${SELECTED[$i]} ${MODULES[$i]} #${FLAGS[$i]}
        done

        echo
        echo -n "Please type a number of the package you want to select or unselect: "

        read L

        if [[ "$L" =~ ^[0-9]+$ ]]; then
            if [ ${SELECTED["$L"]} == "x" ]; then
                SELECTED[$L]="."
            elif [ ${SELECTED["$L"]} == "." ]; then
                SELECTED[$L]="x"
            fi
        fi
    done

    # print all selected drivers to the result descriptor (3)
    for i in "${!FLAGS[@]}"; do
        if [ ${SELECTED[$i]} == "x" ]; then
            echo ${FILES[$i]} ${FLAGS[$i]} 1>&3
        fi
    done
}

# process potential DUD for a given architecture
function driverupdatedisc()
{
    device=$1
    arch=$2
    num=$3

    echo "Checking Driver Update Disc $device..."
    DUD="/media/dud"

    mkdir -p "$DUD"
    mount $device "$DUD" || return
    dud_check "$DUD" $arch || umount /media/dud || return

    dud_copy "$DUD" $arch /tmp/DD-$num
    dud_contents /tmp/DD-$num >/tmp/dud_list.txt

    if [ -e "$DUD/rhdd3.rules" ]; then
        MODE="interactive"
        DEFAULT="."
    else
        MODE="noninteractive"
        DEFAULT="x"
    fi

    dud_select "Select DUP RPMs to install" /tmp/dud_list.txt $DEFAULT $MODE 3>/tmp/dud_extract.txt

    dud_extract /tmp/DD-$num "/lib/modules/$(uname -r)/updates" </tmp/dud_extract.txt
    
    # save the list of extracted modules for later use in anaconda
    cat /tmp/dud_extract.txt >>/tmp/dud_extracted.txt

    # TODO add DD-X as a Yum repository

    # release the DUD
    umount "$DUD"

    # regenerate module lists
    depmod -a

    # get a list of modules that weren't loaded when this script started
    cut -f1 -d " " /proc/modules | sort >/tmp/dud_state_current
    cat /tmp/dud_state /tmp/dud_state_current | uniq -u >/tmp/dud_rmmod

    # iterative removal of package dependencies
    REMOVING=1

    # remove all modules that were added by driver updates and can be removed
    while [ $REMOVING -gt 0 ]; do
        # this might be the last iteration
        REMOVING=0

        for mod in $(cat /tmp/dud_rmmod); do
            rmmod $mod
            if [ $? -eq 0 ]; then
                # is something was removed, there needs to be another iteration
                # to remove the modules that depended on this one
                REMOVING=1
            fi
        done
    done

    # wait a bit to let the kernel and udev stabilize
    sleep 1

    # load modules (in their new version incarnation) again
    # XXX it freezes here for an unknown reason..
    udevadm trigger
}

#
# The main flow of execution starts below this point
#


# save module state
cut -f1 -d " " /proc/modules | sort >/tmp/dud_state

# get hw architecture
ARCH=$(uname -i)

# load all modules
udevadm trigger

# check all devices for the "oemdrv" label
DUDS=$(blkid -t LABEL=OEMDRV | cut -d: -f1)
NUM=0

# go through the detected devices
for dud in $DUDS; do
    driverupdatedisc $dud $ARCH $NUM
    NUM=$(expr $NUM + 1)
done

# manual driver selection
DD=$(getarg dd)

# TODO what if there are multiple dd= arguments?
if [ $? -eq 0 ]; then
    # if dd or dd=<nonsense>, show UI
    # else if dd=url, skip now, we will process it when network is ready
    # else skip UI steps and use the argument as path to the image

    # UI select device
    # UI select partition (if there are any)
    # UI browse directories (if rhdd3 file is present, skip following steps)
    # UI select driver update disc image
    driverupdatedisc $dud $ARCH $NUM # TODO skip mounting for directory based DUDs
    NUM=$(expr $NUM + 1)
fi


