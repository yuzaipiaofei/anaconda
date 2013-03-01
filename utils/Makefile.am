# utils/Makefile.am for anaconda
#
# Copyright (C) 2009  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: David Cantrell <dcantrell@redhat.com>

SUBDIRS = log_picker

utilsdir            = $(libexecdir)/$(PACKAGE_NAME)

dist_sbin_SCRIPTS    = logpicker handle-sshpw
utils_PROGRAMS       = dud_list dud_extract

dud_list_LDADD = $(RPM_LIBS) $(LIBARCHIVE_LIBS)
dud_list_SOURCES = rpmutils.c dud_list.c

dud_extract_LDFLAGS = $(LIBARCHIVE_LIBS) $(RPM_LIBS)
dud_extract_SOURCES = rpmutils.c dud_extract.c

MAINTAINERCLEANFILES = Makefile.in
