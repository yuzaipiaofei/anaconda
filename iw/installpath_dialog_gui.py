#
# network_dialog_gui.py - GUI front end code for keyboard configuration
#
# Brent Fox <bfox@redhat.com>
#
# Copyright 2003 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#


import string
import gui
import gtk
import gobject
import sys
import os
import installclass
from flags import flags
from pixmapRadioButtonGroup_gui import pixmapRadioButtonGroup

from rhpl.firstboot_gui_window import FirstbootGuiWindow

##
## I18N
## 
from rhpl.translate import _, N_
import rhpl.translate as translate
translate.textdomain ("anaconda")


##
## Icon for windows
##

iconPixbuf = None      
try:
    iconPixbuf = self.ics.readPixmap("install.png")
except:
    pass


class InstallTypeWindow(FirstbootGuiWindow):
    windowTitle = N_("Install Type Window")
    htmlTag = "installtype"
    shortMessage = N_("Need some text to go here.")
    installTypes = installclass.availableClasses()

    def __init__(self, label, dispatch, ics, id):
        self.installTypeLabel = label
        self.dispatch = dispatch
        self.ics = ics
        self.id = id
	self.flags = flags

    def getNext(self):
        print "in getNext"
        selection = None
	for (name, object, pixmap) in self.installTypes:
	    if name == self.currentClassName:
		selection = object
                self.installTypeLabel.set_text(name)
                        
	if not isinstance (self.id.instClass, selection):
	    c = selection(self.flags.expert)
	    c.setSteps(self.dispatch)
	    c.setInstallData(self.id)

    def select_row(self, *args):
        rc = self.modelView.get_selection().get_selected()
        if rc:
            model, iter = rc
            key = self.modelStore.get_value(iter, 0)
            if key:
                self.type = key

    def setupScreen(self):
#        self.mainWindow.set_size_request(-1, -1)

        # XXX set up a test area and do some sort of instant apply ?

        # set up the icon
        p = None
        try:
            p = gtk.gdk.pixbuf_new_from_file("pixmaps/install.png")
        except:
            pass

        if p:
            self.icon = gtk.Image()
            self.icon.set_from_pixbuf(p)


        self.myVbox = gtk.VBox()
        self.myVbox.set_spacing(5)
        

	r = self.createInstallTypeOption()
	b = r.render()

	r.setToggleCallback(self.optionToggled)

	# figure out current class as well as default
	defaultClass = None
	currentClass = None
	firstClass = None
	for (name, object, pixmap) in self.installTypes:
	    if firstClass is None:
		firstClass = object

	    if isinstance(self.id.instClass, object):
		currentClass = object

	    if object.default:
		defaultClass = object

	if currentClass is None:
	    if defaultClass is not None:
		self.currentClassName = defaultClass.name
	    else:
		self.currentClassName = firstClass.name
	else:
	    self.currentClassName = currentClass.name


	r.setCurrent(self.currentClassName)
	
	box = gtk.VBox (gtk.FALSE)
        box.pack_start(b, gtk.FALSE)

        self.myVbox.pack_start (box, gtk.FALSE)



        for (name, object, pixmap) in self.installTypes:
            print name

        print "in apply"
        self.getNext()

        try:
            #If we're in reconfig mode, this will fail because there is no self.mainWindow
            self.mainWindow.destroy()
        except:
            pass
        return 0

    def anacondaScreen(self):
        print "okAnacondaClicked"

        self.doDebug = None
        self.setupScreen()
        return FirstbootGuiWindow.anacondaScreen(self, InstallTypeWindow.windowTitle, iconPixbuf, 500, 400)

    def okAnacondaClicked(self, *args):
        self.getNext()
        self.mainWindow.destroy()

    def optionToggled(self, widget, name):
	if widget.get_active():
	    self.currentClassName = name

    def createInstallTypeOption(self):
	r = pixmapRadioButtonGroup()

	for (name, object, pixmap) in self.installTypes:
	    descr = object.description
	    r.addEntry(name, _(name), pixmap=self.ics.readPixmap(pixmap),
		       descr=_(descr))

	return r


childWindow = InstallTypeWindow

