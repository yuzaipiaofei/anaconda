#
# langauge_gui.py: installtime language selection.
#
# Copyright 2001 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import gtk
from iw_gui import *
from translate import _, N_

class LanguageWindow (InstallWindow):

    windowTitle = N_("Language Selection")
    htmlTag = "lang"

    def __init__ (self, ics):
	InstallWindow.__init__ (self, ics)

    def getNext (self):
	self.instLang.setRuntimeLanguage(self.lang)
	self.ics.getICW().setLanguage (self.instLang.getLangNick(self.lang))

        return None

    def select_row (self, clist, row, col, event):
        if self.running:
            self.lang = clist.get_row_data (clist.selection[0])

    # LanguageWindow tag="lang"
    def getScreen (self, intf, instLang):
        self.running = 0
        mainBox = gtk.VBox (gtk.FALSE, 10)

        hbox = gtk.HBox(gtk.FALSE, 5)
        pix = self.ics.readPixmap ("gnome-globe.png")
        if pix:
            a = gtk.Alignment ()
            a.add (pix)
            hbox.pack_start (a, gtk.FALSE)
            
        label = gtk.Label (_("What language would you like to use during the "
                         "installation process?"))
        label.set_line_wrap (gtk.TRUE)
        label.set_usize(350, -1)
        hbox.pack_start(label, gtk.FALSE)
        
        self.language = gtk.CList (1)
        self.language.set_selection_mode (gtk.SELECTION_BROWSE)
        self.language.connect ("select_row", self.select_row)
	self.instLang = instLang

        default = -1
        n = 0
        for locale in instLang.available():
            row = self.language.append ((_(locale),))
            self.language.set_row_data (row, locale)

            if locale == instLang.getCurrent():
                self.lang = locale
                default = n
            n = n + 1

        if default > 0:
            self.language.select_row (default, 0)

        sw = gtk.ScrolledWindow ()
        sw.set_border_width (5)
        sw.set_policy (gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        sw.add (self.language)
        
        mainBox.pack_start (hbox, gtk.FALSE, gtk.FALSE, 10)
        mainBox.pack_start (sw, gtk.TRUE, gtk.TRUE)

        self.running = 1
        
        return mainBox
