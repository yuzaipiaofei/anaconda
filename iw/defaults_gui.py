#
# defaults_gui.py: screen for the default values for anaconda
#
# Brent Fox <bfox@redhat.com>
#
# Copyright 2003 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
import string
import gobject
import gui
from iw_gui import *
from re import *
from rhpl.translate import _, N_
import rhpl.keyboard 
from flags import flags

import sys
import installclass
import installpath_dialog_gui
import keyboard_gui
import mouse_gui
import network_dialog_gui
import language_support_dialog_gui

class DefaultsWindow(InstallWindow):
    windowTitle = N_("Defaults")
    htmlTag = "defaults"
    installTypes = installclass.availableClasses()

    def __init__(self, ics):
        self.ics = ics

    def getNext(self):
        self.dispatch.skipStep("keyboard")
        self.dispatch.skipStep("mouse")
        self.dispatch.skipStep("network")
        self.dispatch.skipStep("languagesupport")
        return None
    
        
    # MouseWindow tag="mouse"
    def getScreen(self, dispatch, id):
        self.dispatch = dispatch
        self.id = id
        self.keyboard = id.keyboard
	self.mouse = id.mouse
        self.network = id.network
        self.langSupport = id.langSupport

        if "name" in dir(id.instClass):
            #If the installClass has been selected before, restore the setting
            #when re-entering this screen
            installTypeName = id.instClass.name
        else:
            #This is the first time we've entered this screen.  Set a default
            installTypeName, object, pixmap = self.installTypes[0]
            c = object(flags.expert)
            c.setSteps(self.dispatch)
            c.setInstallData(self.id)

	self.flags = flags

        mainBox = gtk.VBox (gtk.FALSE)

##         titleBox = gtk.HBox(gtk.FALSE)
##         titleBox.set_spacing(5)
##         pix = self.ics.readPixmap ("workstation.png")
##         if pix:
##             titleBox.pack_start (pix, gtk.FALSE)

##         titleLabel = gtk.Label("")
##         titleLabel.set_alignment(0.0, 0.5)
##         titleLabel.set_markup("<span foreground='#000000' size='30000' font_family='Helvetica'><b>%s</b></span>" % self.windowTitle)

        infoLabel = gtk.Label (_("Some filler text about probed defaults here"))

        infoLabel.set_line_wrap (gtk.TRUE)
        infoLabel.set_alignment(0.0, 0.5)
        infoLabel.set_size_request(450, -1)
##         titleBox.pack_start(titleLabel, gtk.TRUE)

        self.defaultsTable = gtk.Table(3, 5)
        self.defaultsTable.set_border_width(15)
        self.defaultsTable.set_col_spacings(10)
        self.defaultsTable.set_row_spacings(10)

        icon = self.ics.readPixmap("install.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Installation \nType"))
        label.set_alignment(0.0, 0.5)
        self.installTypeLabel = gtk.Label(installTypeName)
        self.installTypeLabel.set_alignment(0.0, 0.5)
        installTypeButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>%s</u></span>' % (_('Change'),))
        installTypeButton.add(buttonLabel)
        installTypeButton.set_relief(gtk.RELIEF_NONE)
        installTypeButton.connect("clicked", self.installTypeClicked)

        self.defaultsTable.attach(icon, 0, 1, 0, 1, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 0, 1, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.installTypeLabel, 2, 3, 0, 1, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(installTypeButton, 3, 4, 0, 1, gtk.SHRINK, gtk.SHRINK)

        icon = self.ics.readPixmap("gnome-keyboard.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Keyboard"))
        label.set_alignment(0.0, 0.5)
        self.keyboardLabel = gtk.Label(self.keyboard.modelDict[self.keyboard.get()][0])
        self.keyboardLabel.set_alignment(0.0, 0.5)
        keyboardButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>%s</u></span>' % (_('Change'),))
        keyboardButton.add(buttonLabel)
        keyboardButton.set_relief(gtk.RELIEF_NONE)
        keyboardButton.connect("clicked", self.keyboardClicked)

        self.defaultsTable.attach(icon, 0, 1, 1, 2, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 1, 2, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.keyboardLabel, 2, 3, 1, 2, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(keyboardButton, 3, 4, 1, 2, gtk.SHRINK, gtk.SHRINK)

        icon = self.ics.readPixmap("gnome-mouse.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Mouse"))
        label.set_alignment(0.0, 0.5)
        self.mouseLabel = gtk.Label(self.mouse.info["FULLNAME"])
        self.mouseLabel.set_alignment(0.0, 0.5)
        mouseButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>%s</u></span>' % (_('Change'),))
        mouseButton.add(buttonLabel)
        mouseButton.set_relief(gtk.RELIEF_NONE)
        mouseButton.connect("clicked", self.mouseClicked)

        self.defaultsTable.attach(icon, 0, 1, 2, 3, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 2, 3, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.mouseLabel, 2, 3, 2, 3, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(mouseButton, 3, 4, 2, 3,  gtk.SHRINK, gtk.SHRINK)    

        icon = self.ics.readPixmap("network.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Network"))
        label.set_alignment(0.0, 0.5)

        self.networkLabel = gtk.Label(_("Automatically configured"))
        self.networkLabel.set_alignment(0.0, 0.5)
        networkButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>%s</u></span>' % (_('Change'),))
        networkButton.add(buttonLabel)
        networkButton.set_relief(gtk.RELIEF_NONE)
        networkButton.connect("clicked", self.networkClicked)

        self.defaultsTable.attach(icon, 0, 1, 3, 4, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 3, 4, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.networkLabel, 2, 3, 3, 4, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(networkButton, 3, 4, 3, 4,  gtk.SHRINK, gtk.SHRINK)    

        icon = self.ics.readPixmap("gnome-globe.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Language \nSupport"))
        label.set_alignment(0.0, 0.5)

        self.langSupportLabel = gtk.Label(self.langSupport.getDefault())
        self.langSupportLabel.set_alignment(0.0, 0.5)
        langSupportButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>%s</u></span>' % (_('Change'),))
        langSupportButton.add(buttonLabel)
        langSupportButton.set_relief(gtk.RELIEF_NONE)
        langSupportButton.connect("clicked", self.langSupportClicked)

        self.defaultsTable.attach(icon, 0, 1, 4, 5, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 4, 5, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.langSupportLabel, 2, 3, 4, 5, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(langSupportButton, 3, 4, 4, 5,  gtk.SHRINK, gtk.SHRINK)    




        lowerVBox = gtk.VBox()
        lowerVBox.set_border_width(10)
        lowerVBox.pack_start(self.defaultsTable, gtk.FALSE)

#        mainBox.pack_start(titleBox, gtk.FALSE)
        mainBox.pack_start(infoLabel, gtk.FALSE)
        mainBox.pack_start(lowerVBox, gtk.FALSE)
        return mainBox

    def installTypeClicked(self, *args):
        app = installpath_dialog_gui.childWindow(self.installTypeLabel, self.dispatch, self.ics, self.id)
        app.anacondaScreen()

    def keyboardClicked(self, *args):
        app = keyboard_gui.childWindow()
        app.anacondaScreen(self.keyboardLabel, self.keyboard, self.keyboard)

    def mouseClicked(self, *args):
        app = mouse_gui.childWindow()
        app.anacondaScreen(self.mouse, self.mouseLabel)

    def networkClicked(self, *args):
        app = network_dialog_gui.childWindow(self.ics)
        app.anacondaScreen(self.networkLabel, self.network)

    def langSupportClicked(self, *args):
        app = language_support_dialog_gui.childWindow(self.ics)
        app.anacondaScreen(self.langSupportLabel, self.langSupport)
