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
import ipwidget
import checklist

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
    iconPixbuf = self.ics.readPixmap("gnome-globe.png")
except:
    pass


class LangSupportWindow(FirstbootGuiWindow):
    windowTitle = N_("Language Support")
    htmlTag = "langsupport"
    shortMessage = N_("Need some text to go here.")

    def __init__(self, ics):
        self.ics = ics

    def getNext(self):
        print "in getNext"

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
            p = gtk.gdk.pixbuf_new_from_file("pixmaps/gnome-globe.png")            
        except:
            pass

        if p:
            self.icon = gtk.Image()
            self.icon.set_from_pixbuf(p)


        self.myVbox = gtk.VBox()
        self.myVbox.set_spacing(5)
        hbox = gtk.HBox (gtk.FALSE)
        
	# create option menu of default langs
        label = gui.MnemonicLabel(_("Select the _default language for the system:   "))
	self.deflang_optionmenu = None
	self.deflang_menu = None
	self.deflang_values = None
	self.createDefaultLangMenu(self.supportedLangs)
        label.set_mnemonic_widget(self.deflang_optionmenu)

        hbox.pack_start (label, gtk.FALSE, 20)
        hbox.pack_start (self.deflang_optionmenu, gtk.TRUE, 20)
        self.myVbox.pack_start (hbox, gtk.FALSE, 50)

        sep = gtk.HSeparator ()
        self.myVbox.pack_start (sep, gtk.FALSE, 15)


        self.installAllRadio = gtk.RadioButton(None, (_("Install _all available languages")))
        self.installSomeRadio = gtk.RadioButton(self.installAllRadio, (_("Select _addition languages "
                                                                         "to install on the system")))
        self.installSomeRadio.connect("toggled", self.toggleList)

        self.myVbox.pack_start(self.installAllRadio, gtk.FALSE)
        self.myVbox.pack_start(self.installSomeRadio, gtk.FALSE)

##        hbox = gtk.HBox (gtk.FALSE, 5)


        # langs we want to support
        self.languageList = checklist.CheckList(1)
        label.set_mnemonic_widget(self.languageList)


        self.maxrows = 0
        list = []

        for locale in self.languages:
	    if locale == self.defaultLang or (locale in self.supportedLangs):
		self.languageList.append_row((locale, ""), gtk.TRUE)
		list.append(locale)
	    else:
		self.languageList.append_row((locale, ""), gtk.FALSE)

            self.maxrows = self.maxrows + 1

        self.setCurrent(self.defaultLang)
            
        self.sw = gtk.ScrolledWindow ()
        self.sw.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.sw.add (self.languageList)
        self.sw.set_shadow_type(gtk.SHADOW_IN)
        self.sw.set_sensitive(gtk.FALSE)

        align = gtk.Alignment()
        align.set(1.0, 0.5, 0.9, 1.0)
        align.add(self.sw)

        self.myVbox.pack_start (align, gtk.TRUE)
        

        print "in apply"
        self.getNext()

        try:
            #If we're in reconfig mode, this will fail because there is no self.mainWindow
            self.mainWindow.destroy()
        except:
            pass
        return 0

    def anacondaScreen(self, langSupportLabel, lang):
        print "okAnacondaClicked", langSupportLabel
        self.langs = lang
        self.langSupportLabel = langSupportLabel
        self.languages = self.langs.getAllSupported()
        self.supportedLangs = self.langs.getSupported()
        self.origLangs = []

        for i in self.supportedLangs:
            self.origLangs.append(i)
            
	self.defaultLang = self.langs.getDefault()
	self.oldDefaultLang = self.defaultLang

        print langSupportLabel
        self.doDebug = None
        self.setupScreen()
        return FirstbootGuiWindow.anacondaScreen(self, LangSupportWindow.windowTitle, iconPixbuf, 550, 500)

    def okAnacondaClicked(self, *args):
        self.getNext()
        self.mainWindow.destroy()

    def rebuild_optionmenu(self):
        list = []

	for row in range(self.maxrows):
	    if self.languageList.get_active(row) == 1:
		selected = self.languageList.get_text (row, 1)
		list.append (selected)
	
	if len(list) == 0:
	    list = [""]
	    self.ics.setNextEnabled (gtk.FALSE)
	else:
	    self.ics.setNextEnabled (gtk.TRUE)

	curidx = self.deflang_optionmenu.get_history()
	if curidx >= 0:
	    self.defaultLang = self.deflang_values[curidx]
	else:
	    self.defaultLang = None

	if self.defaultLang is not None and self.defaultLang in list:
	    index = list.index(self.defaultLang)
	else:
	    index = 0
	    self.defaultLang = list[0]

	self.createDefaultLangMenu(list)
	self.deflang_optionmenu.set_history(index)

    def setCurrent(self, currentDefault, recenter=1):
        parent = None

        store = self.languageList.get_model()
        row = 0

        # iterate over the list looking for the default locale
        while (row < self.languageList.num_rows):
            if self.languageList.get_text(row, 1) == currentDefault:
                path = store.get_path(store.get_iter((row,)))
                col = self.languageList.get_column(0)
                self.languageList.set_cursor(path, col, gtk.FALSE)
                self.languageList.scroll_to_cell(path, col, gtk.TRUE, 0.5, 0.5)
                break
            row = row + 1

    def createDefaultLangMenu(self, supported):
	if self.deflang_optionmenu is None:
	    self.deflang_optionmenu = gtk.OptionMenu()

	if self.deflang_menu is not None:
	    self.deflang_optionmenu.remove_menu()
	    
	self.deflang_menu = gtk.Menu()

	sel = None
        curidx = 0
	values = []
        for locale in self.languages:
	    if locale == self.defaultLang or (locale in supported):
		item = gtk.MenuItem(locale)
		item.show()
		self.deflang_menu.add(item)

		if locale == self.defaultLang:
		    sel = curidx
		else:
		    curidx = curidx + 1

		values.append(locale)

	self.deflang_optionmenu.set_menu(self.deflang_menu)

	if sel is not None:
	    self.deflang_optionmenu.set_history(sel)

	self.deflang_values = values

    def toggleList(self, *args):
        self.sw.set_sensitive(self.installSomeRadio.get_active())


childWindow = LangSupportWindow

