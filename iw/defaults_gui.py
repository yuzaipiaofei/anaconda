#
# mouse_gui.py: gui mouse configuration.
#
# Copyright 2000-2002 Red Hat, Inc.
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
import keyboard_gui
import mouse_gui

class DefaultsWindow(InstallWindow):
    windowTitle = N_("Defaults")
    htmlTag = "mouse"
#    kbd = rhpl.keyboard.Keyboard()

    def getNext(self):
##         self.mouse.set(self.currentMouse, self.emulate3.get_active())

##         mouse = self.availableMice[self.currentMouse]
##         gpm, xdev, device, emulate, shortname = mouse

##         if device == "ttyS":
##             self.mouse.setDevice(self.serialDevice)
##         else:
##             self.mouse.setDevice(device)

## 	if self.flags.setupFilesystems:
## 	    self.mouse.setXProtocol()

        return None
    
        
    # MouseWindow tag="mouse"
    def getScreen(self, defaultKeyboard, defaultLang, keyboard, mouse):
        print "in defaults getScreen", defaultKeyboard, keyboard
#        print dir(defaultLang)
#        print defaultLang.getCurrent()
#        print defaultLang.current
#        print defaultLang.getDefaultTimeZone()
#        print mouse
#        print dir(timezone)
#        print timezone.getTimezoneInfo()
        
        self.defaultKeyboard = defaultKeyboard
        self.keyboard = keyboard
	self.mouse = mouse

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

        icon = self.ics.readPixmap("gnome-keyboard.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Keyboard"))
        label.set_alignment(0.0, 0.5)
        self.keyboardLabel = gtk.Label(self.keyboard.modelDict[self.defaultKeyboard][0])
        self.keyboardLabel.set_alignment(0.0, 0.5)
        keyboardButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>'
                                    '%s</u></span>' % (_('Change'),))
        keyboardButton.add(buttonLabel)
        keyboardButton.set_relief(gtk.RELIEF_NONE)
        keyboardButton.connect("clicked", self.keyboardClicked)

        self.defaultsTable.attach(icon, 0, 1, 0, 1, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 0, 1, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.keyboardLabel, 2, 3, 0, 1, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(keyboardButton, 3, 4, 0, 1, gtk.SHRINK, gtk.SHRINK)
        
        icon = self.ics.readPixmap("gnome-mouse.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Mouse"))
        label.set_alignment(0.0, 0.5)
        self.mouseLabel = gtk.Label(self.mouse.info["FULLNAME"])
        self.mouseLabel.set_alignment(0.0, 0.5)
        mouseButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>'
                                    '%s</u></span>' % (_('Change'),))
        mouseButton.add(buttonLabel)
        mouseButton.set_relief(gtk.RELIEF_NONE)
        mouseButton.connect("clicked", self.mouseClicked)

        self.defaultsTable.attach(icon, 0, 1, 1, 2, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 1, 2, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.mouseLabel, 2, 3, 1, 2, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(mouseButton, 3, 4, 1, 2,  gtk.SHRINK, gtk.SHRINK)    

        icon = self.ics.readPixmap("timezone.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Timezone"))
        label.set_alignment(0.0, 0.5)
        self.timezoneLabel = gtk.Label(defaultLang.getDefaultTimeZone())
        self.timezoneLabel.set_alignment(0.0, 0.5)
        timezoneButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>'
                                    '%s</u></span>' % (_('Change'),))
        timezoneButton.add(buttonLabel)
        timezoneButton.set_relief(gtk.RELIEF_NONE)
#        mouseButton.connect("clicked", self.keyboardClicked)

        self.defaultsTable.attach(icon, 0, 1, 2, 3, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 2, 3, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.timezoneLabel, 2, 3, 2, 3, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(timezoneButton, 3, 4, 2, 3,  gtk.SHRINK, gtk.SHRINK)    

        icon = self.ics.readPixmap("timezone.png")
        label = gtk.Label("")
        label.set_markup("<span foreground='#000000' size='large' font_family='Helvetica'><b>%s:</b></span>" % _("Timezone"))
        label.set_alignment(0.0, 0.5)
        self.timezoneLabel = gtk.Label(defaultLang.getDefaultTimeZone())
        self.timezoneLabel.set_alignment(0.0, 0.5)
        timezoneButton = gtk.Button()
        buttonLabel = gtk.Label("")
        buttonLabel.set_markup('<span foreground="#3030c0"><u>'
                                    '%s</u></span>' % (_('Change'),))
        timezoneButton.add(buttonLabel)
        timezoneButton.set_relief(gtk.RELIEF_NONE)
#        mouseButton.connect("clicked", self.keyboardClicked)

        self.defaultsTable.attach(icon, 0, 1, 2, 3, gtk.SHRINK)
        self.defaultsTable.attach(label, 1, 2, 2, 3, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(self.timezoneLabel, 2, 3, 2, 3, gtk.SHRINK|gtk.FILL)
        self.defaultsTable.attach(timezoneButton, 3, 4, 2, 3,  gtk.SHRINK, gtk.SHRINK)    



        lowerVBox = gtk.VBox()
        lowerVBox.set_border_width(10)
        lowerVBox.pack_start(self.defaultsTable, gtk.FALSE)

#        mainBox.pack_start(titleBox, gtk.FALSE)
        mainBox.pack_start(infoLabel, gtk.FALSE)
        mainBox.pack_start(lowerVBox, gtk.FALSE)
        return mainBox

    def keyboardClicked(self, *args):
        print "keyboard clicked", keyboard_gui
        print dir(keyboard_gui)
        app = keyboard_gui.childWindow()
        app.anacondaScreen(self.defaultKeyboard, self.keyboardLabel, self.keyboard, self.keyboard)

    def mouseClicked(self, *args):
        print "mouse clicked", mouse_gui, self.mouse
        
#        print dir(self.mouse)
        app = mouse_gui.childWindow()
        app.anacondaScreen(self.mouse, self.mouseLabel)

