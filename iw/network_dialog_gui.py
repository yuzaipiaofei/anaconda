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
import gtk
import gobject
import sys
import os
import ipwidget

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
    iconPixbuf = self.ics.readPixmap("network.png")
except:
    pass


global_options = [_("Gateway"), _("Primary DNS"),
                  _("Secondary DNS"), _("Tertiary DNS")]

global_option_labels = [_("_Gateway"), _("_Primary DNS"),
                        _("_Secondary DNS"), _("_Tertiary DNS")]


class NetworkWindow(FirstbootGuiWindow):
    windowTitle = N_("Network Devices")
    htmlTag = "network"
    shortMessage = N_("Need some text to go here.")

    def __init__(self, ics, intf):
        self.ics = ics
        self.intf = intf

    def getNext(self):
        print "in getNext"

        if self.getNumberActiveDevices() == 0:
            rc = self.handleNoActiveDevices()
            if not rc:
                return
            else:
                self.mainWindow.destroy()
                return
        
        if self.hostnameManual.get_active() == gtk.TRUE:
	    hname = string.strip(self.hostnameEntry.get_text())
	    neterrors =  network.sanityCheckHostname(hname)
	    if neterrors is not None:
		self.handleBadHostname(hname, neterrors) 
                return
	    elif len(hname) == 0:
		if self.handleMissingHostname():
                    return
            
	    newHostname = hname
            override = 1
	else:
	    newHostname = "localhost.localdomain"
	    override = 0

	if not self.anyUsingDHCP():
	    tmpvals = {}
	    for t in range(len(global_options)):
		try:
		    tmpvals[t] = self.globals[global_options[t]].dehydrate()
		except ipwidget.IPMissing, msg:
		    if t < 2:
			if self.handleMissingOptionalIP(global_options[t]):
			    return
			else:
			    tmpvals[t] = None
		    else:
			    tmpvals[t] = None
			
		except ipwidget.IPError, msg:
		    self.handleIPError(global_options[t], msg[0])
                    return

	    self.network.gateway = tmpvals[0]
	    self.network.primaryNS = tmpvals[1]
	    self.network.secondaryNS = tmpvals[2]
	    self.network.ternaryNS = tmpvals[3]
	else:
	    self.network.gateway = None
	    self.network.primaryNS = None
	    self.network.secondaryNS = None
	    self.network.ternaryNS = None

        for nicClass in self.nicClassList:
            dev = nicClass.getDeviceName()
            
            if nicClass.getActivateCheckButton().get_active() == gtk.TRUE:
                self.devices[dev].set(("ONBOOT", "yes"))
            else:
                self.devices[dev].set(("ONBOOT", "no"))

            if nicClass.getDhcpRadioButton().get_active() == gtk.TRUE:
                self.devices[dev].set(("bootproto", "dhcp"))
            else:
                self.devices[dev].set(("bootproto", "static"))

	self.network.hostname = newHostname
	self.network.overrideDHCPhostname = override
        
        self.mainWindow.destroy()

    def setupScreen(self):
        # XXX set up a test area and do some sort of instant apply ?

        # set up the icon
        p = None
        try:
            p = gtk.gdk.pixbuf_new_from_file("pixmaps/network.png")            
        except:
            pass

        if p:
            self.icon = gtk.Image()
            self.icon.set_from_pixbuf(p)

        self.myVbox = gtk.VBox()
        self.myVbox.set_spacing(5)

        deviceHBox = gtk.HBox()
        self.myVbox.pack_start(deviceHBox, gtk.FALSE)
        deviceHBox.set_spacing(5)
        self.deviceOptionMenu = gtk.OptionMenu()
        self.deviceOptionMenu.connect("changed", self.menuChanged)
        deviceHBox.pack_start(gtk.Label(_("Network Device:")), gtk.FALSE)
        deviceHBox.pack_start(self.deviceOptionMenu, gtk.TRUE)

        self.notebook = gtk.Notebook()
        self.myVbox.pack_start(self.notebook, gtk.TRUE)

        self.deviceVBox = gtk.VBox()
        self.deviceVBox.set_border_width(10)
        self.advancedVBox = gtk.VBox()
        self.advancedVBox.set_border_width(10)
        label = gtk.Label(_("_Devices"))
        label.set_use_underline(gtk.TRUE)
        self.notebook.append_page(self.deviceVBox, label)
        label = gtk.Label(_("Ad_vanced"))
        label.set_use_underline(gtk.TRUE)
        self.notebook.append_page(self.advancedVBox, label)


        self.deviceMenu = gtk.Menu()
        self.devices = self.network.available()
        self.availableDevices = self.network.available().keys()
        self.availableDevices.sort()

#        #XXX - for testing only
#        self.availableDevices.append('eth1')
#        self.availableDevices.append('eth2')

        self.nicNotebook = gtk.Notebook()
        self.nicNotebook.set_show_tabs(gtk.FALSE)
        self.nicNotebook.set_show_border(gtk.FALSE)
        self.nicClassList = []

        for device in self.availableDevices:
            item = gtk.MenuItem(device)
            self.deviceMenu.append(item)

            nicClass = NicClass(device)
            self.nicClassList.append(nicClass)

            self.nicNotebook.append_page(nicClass.getVBox(), gtk.Label(""))

        self.nicClassList[0].activateCheckButton.set_active(gtk.TRUE)
        
        self.deviceVBox.pack_start(self.nicNotebook, gtk.FALSE)

	# show hostname and dns/misc network info and offer chance to modify
	hostbox = gtk.HBox()
	hostbox=gtk.VBox()
	label=gtk.Label(_("Set the hostname:"))
	label.set_alignment(0.0, 0.0)
	hostbox.pack_start(label, gtk.FALSE, gtk.FALSE)
	tmphbox=gtk.HBox()
        self.hostnameUseDHCP = gtk.RadioButton(label=_("_automatically via DHCP"))
#	self.hostnameUseDHCP.connect("toggled", self.hostnameUseDHCPCB, None)
	
	tmphbox.pack_start(self.hostnameUseDHCP, gtk.FALSE, gtk.FALSE, padding=15)
	hostbox.pack_start(tmphbox, gtk.FALSE, gtk.FALSE, padding=5)

	self.hostnameManual  = gtk.RadioButton(group=self.hostnameUseDHCP, label=_("_manually"))
	tmphbox=gtk.HBox()
	tmphbox.pack_start(self.hostnameManual, gtk.FALSE, gtk.FALSE, padding=15)
	self.hostnameEntry = gtk.Entry()
        self.hostnameEntry.set_sensitive(gtk.FALSE)
	tmphbox.pack_start(self.hostnameEntry, gtk.FALSE, gtk.FALSE, padding=15)
	self.hostnameManual.connect("toggled", self.hostnameManualCB, None)

	hostbox.pack_start(tmphbox, gtk.FALSE, gtk.FALSE, padding=5)

	hostbox.set_border_width(6)
	frame=gtk.Frame(_("Hostname"))
	frame.add(hostbox)
	self.advancedVBox.pack_start(frame, gtk.FALSE, gtk.FALSE)

        #
	# this is the iptable used for DNS, et. al
	self.ipTable = gtk.Table(len(global_options), 2)
#	self.ipTable.set_row_spacing(0, 5)
	options = {}
	for i in range(len(global_options)):
	    label = gtk.Label("%s:" %(global_option_labels[i],))
	    label.set_property("use-underline", gtk.TRUE)
	    label.set_alignment(0.0, 0.0)
	    self.ipTable.attach(label, 0, 1, i, i+1, gtk.FILL, 0)
	    align = gtk.Alignment(0, 0.5)
	    options[i] = ipwidget.IPEditor()
	    align.add(options[i].getWidget())
	    label.set_mnemonic_widget(options[i].getFocusableWidget())

	    self.ipTable.attach(align, 1, 2, i, i+1, gtk.FILL, 0)

	self.ipTable.set_border_width(6)

	frame=gtk.Frame(_("Miscellaneous Settings"))
	frame.add(self.ipTable)
	self.advancedVBox.pack_start(frame, gtk.FALSE, gtk.FALSE)        


	self.globals = {}
	for t in range(len(global_options)):
	    self.globals[global_options[t]] = options[t]

	# bring over the value from the loader
	if self.network.hostname != "localhost.localdomain" and ((self.anyUsingDHCP() and self.network.overrideDHCPhostname) or not self.anyUsingDHCP()):
	    self.hostnameEntry.set_text(self.network.hostname)

#
# for now always put info in the entries, even if we're using DHCP
#
#	if not self.anyUsingDHCP() or 1:
        if 1:
	    if self.network.gateway:
		self.globals[_("Gateway")].hydrate(self.network.gateway)
	    if self.network.primaryNS:
		self.globals[_("Primary DNS")].hydrate(self.network.primaryNS)
	    if self.network.secondaryNS:
		self.globals[_("Secondary DNS")].hydrate(self.network.secondaryNS)
	    if self.network.ternaryNS:
		self.globals[_("Tertiary DNS")].hydrate(self.network.ternaryNS)


        self.deviceOptionMenu.set_menu(self.deviceMenu)
                                  
    def menuChanged(self, *args):
        self.nicNotebook.set_current_page(self.deviceOptionMenu.get_history())
        
    def getNumberActiveDevices(self):
        numactive = 0
        for nicClass in self.nicClassList:
            if nicClass.getActivateCheckButton().get_active() == gtk.TRUE:
                numactive = numactive + 1
        return numactive

    def handleNoActiveDevices(self):
	return self.intf.messageWindow(_("Error With Data"), _("You have no active network devices.  Your system will not be able to communicate over a network by default without at least one device active.\n\nNOTE: If you have a PCMCIA-based network adapter you should leave it inactive at this point. When you reboot your system the adapter will be activated automatically."), type="custom", custom_buttons=["gtk-cancel", _("C_ontinue")])

    def handleBadHostname(self, hostname, error):
	self.intf.messageWindow(_("Error With Data"),
				_("The hostname \"%s\" is not valid for the following reason:\n\n%s") % (hostname, error))

    def handleMissingHostname(self):
	return not self.intf.messageWindow(_("Error With Data"),
				_("You have not specified a hostname.  Depending on your network environment this may cause problems later."), type="custom", custom_buttons=["gtk-cancel", _("C_ontinue")])


    def anyUsingDHCP(self):
	for device in self.devices.keys():
	    bootproto = self.devices[device].get("bootproto")

	    if bootproto and bootproto == 'dhcp':
		onboot = self.devices[device].get("ONBOOT")
		if onboot != "no":
		    return 1

	return 0

    def handleMissingOptionalIP(self, field):
	return not self.intf.messageWindow(_("Error With Data"),
				_("You have not specified the field \"%s\".  Depending on your network environment this may cause problems later.") % (field,), type="custom", custom_buttons=["gtk-cancel", _("C_ontinue")])

    def handleIPError(self, field, errmsg):
	newfield = string.replace(field, "_", "")
	self.intf.messageWindow(_("Error With Data"),
				_("An error occurred converting "
				  "the value entered for \"%s\":\n%s" % (newfield, errmsg)))

    def hostnameManualCB(self, widget, data):
	self.hostnameEntry.set_sensitive(widget.get_active())
        
	if widget.get_active():
	    self.hostnameEntry.grab_focus()

    def apply(self, *args):
        print "in apply"
        self.getNext()

        # If the /etc/X11/XF86Config file exists, then change it's keyboard settings
        fullname, layout, model, variant, options = self.kbdDict[self.kbd.get()]

        try:
            #If we're in reconfig mode, this will fail because there is no self.mainWindow
            self.mainWindow.destroy()
        except:
            pass
        return 0

    def anacondaScreen(self, networkLabel, network):
        print "okAnacondaClicked", networkLabel, network
        self.networkLabel = networkLabel
        self.network = network

        print networkLabel
        self.doDebug = None
        self.keyboardLabel = networkLabel
        self.setupScreen()
        return FirstbootGuiWindow.anacondaScreen(self, NetworkWindow.windowTitle, iconPixbuf)

    def okAnacondaClicked(self, *args):
        self.getNext()

childWindow = NetworkWindow

class NicClass:
    def __init__(self, deviceName):
        self.deviceName = deviceName
        self.vbox = gtk.VBox(gtk.FALSE, 5)
        self.vbox.set_border_width(5)

        self.activateCheckButton = gtk.CheckButton(_("_Activate on boot"))
        self.dhcpRadioButton = gtk.RadioButton(None, _("Configure using D_HCP"))
        self.staticRadioButton = gtk.RadioButton(self.dhcpRadioButton, _("Configure using _Static IP"))

	options = [(_("_IP Address"), "ipaddr"),
		   (_("Net_mask"),    "netmask")]

#	if len(dev) >= 3 and dev[:3] == 'ctc':
#	    newopt = (_("Point to Point (IP)"), "remip")
#	    options.append(newopt)
            
        ipTable = gtk.Table(len(options), 2)
        ipTable.set_row_spacings(5)
        ipTable.set_sensitive(gtk.FALSE)

        self.dhcpRadioButton.set_active(gtk.TRUE)
	self.dhcpRadioButton.connect("toggled", self.DHCPtoggled, (ipTable))


	# go ahead and set up DHCP on the first device
#	dhcpCheckButton.set_active(bootproto == 'DHCP')


#	entrys = {}

        label = gtk.Label("%s:" %(options[0][0],))
        label.set_alignment(0.0, 0.5)
        label.set_property("use-underline", gtk.TRUE)
        ipTable.attach(label, 0, 1, 0, 1, gtk.FILL, 0, 10)

        ipEntry = ipwidget.IPEditor()
#        entry.hydrate(self.devices[dev].get(options[0][1]))
        label.set_mnemonic_widget(ipEntry.getFocusableWidget())
        ipTable.attach(ipEntry.getWidget(), 1, 2, 0, 1, 0, gtk.FILL|gtk.EXPAND)

        label = gtk.Label("%s:" %(options[1][0],))
        label.set_alignment(0.0, 0.5)
        label.set_property("use-underline", gtk.TRUE)
        ipTable.attach(label, 0, 1, 1, 2, gtk.FILL, 0, 10)

        netmaskEntry = ipwidget.IPEditor()
#        entry.hydrate(self.devices[dev].get(options[1][1]))
        label.set_mnemonic_widget(netmaskEntry.getFocusableWidget())
        ipTable.attach(netmaskEntry.getWidget(), 1, 2, 1, 2, 0, gtk.FILL|gtk.EXPAND)

        self.vbox.pack_start(self.dhcpRadioButton, gtk.FALSE)
        self.vbox.pack_start(self.staticRadioButton, gtk.FALSE)        
        self.vbox.pack_start(ipTable, gtk.FALSE)
        self.vbox.pack_start(gtk.HSeparator(), 5)
        self.vbox.pack_start(self.activateCheckButton, gtk.FALSE)

    def getVBox(self):
        return self.vbox

    def getActivateCheckButton(self):
        return self.activateCheckButton

    def getDhcpRadioButton(self):
        return self.dhcpRadioButton

    def getDeviceName(self):
        return self.deviceName

    def DHCPtoggled(self, widget, table):
        table.set_sensitive(not self.dhcpRadioButton.get_active())
        

