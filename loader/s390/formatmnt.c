/*****************************************************************************
 *  DASD setup                                                               *
 *  (c) 2000-2001 Bernhard Rosenkraenzer <bero@redhat.com>                   *
 *  Copyright (C) 2001 Florian La Roche <laroche@redhat.com>                 *
 *  Copyright (C) 2001 Karsten Hopp <karsten@redhat.de>                      *
 *****************************************************************************/

#include <newt.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <libintl.h>
#include "common.h"

#define MAX_DASD	26
#define DASD_FMT	"dasd%c"

#define DEV_DASD_FMT	"/dev/" DASD_FMT
#define DEV_DASD_FMT_P1 DEV_DASD_FMT "1"
#define FDASD		"/sbin/fdasd"
#define PROCDASDDEV	"/proc/dasd/devices"
#define DASDFMT		"/sbin/dasdfmt"

#define DASD_HEIGHT	10

#define _(String) gettext((String))

int
main (int argc, char **argv)
{
	newtGrid grid, subgrid, buttonbar;
	newtComponent form, subform, formats, tb, blank;
	newtComponent scroll, ret, ok, cancel;
	newtComponent cb[MAX_DASD], mpf[MAX_DASD];
	newtComponent yesnoform, cdl, ldl, tb2;
	int format[MAX_DASD], have_dasd[MAX_DASD];
	int w, h, i, j, dasds = 0, dasdcount = 0;
	FILE *f, *g;
	char dasd[sizeof (DEV_DASD_FMT) + 1], tmp[4096], error[4096];
	char *mp[MAX_DASD];

	if(getuid() != 0) {
		printf("This program must be run with superuser privileges !\nAborted.\n");
		exit (EXIT_FAILURE);
	}
	for (i = 0; i < MAX_DASD; i++) {
		int fd;
		mp[i] = "";
		sprintf (dasd, DEV_DASD_FMT, 'a' + i);
		if ((fd = open (dasd, O_RDONLY)) >= 0) {
			dasds++;
			have_dasd[i] = 1;
			dasdcount++;
			close (fd);
		} else
			have_dasd[i] = 0;
	}
	doNewtInit (&w, &h);

	/* analyze the initial mountpoints from the commandline,
         * which should be given as argv's in the style:
         * /dev/dasda1:/usr /dev/dasdb1:/tmp
         */
	for (i = 2; i < argc; i++) {
		int n;
		char *d = argv[i];
		char *p = strchr (d, ':');
		char msg[1024];
 
		if (!p) {
			snprintf (msg, sizeof msg, "Invalid parameter: %s\n"
				"Usage is: %s <dasd-partition>:<mountpoint>",
				d, argv[0]);
			newtWinMessage ("Error", "Ok", msg);
			newtFinished ();
			exit (EXIT_FAILURE);
		}
		*p++ = '\0';
		for (n = 0; n < MAX_DASD; n++) {
			sprintf (dasd, DEV_DASD_FMT_P1, 'a' + n);
			if (strncmp (d, dasd, strlen (dasd)) == 0)
				break;
		}
 
		if (n >= MAX_DASD) {
			snprintf (msg, sizeof msg,
				"Invalid %s DASD device in command-line.", d);
			newtWinMessage ("Error", "Ok", msg);
			continue;
		}
 
		if (p[0] != '/') {
			snprintf (msg, sizeof msg, "Invalid path '%s' for "
				"DASD device %s in command-line.", p, d);
			newtWinMessage ("Error", "Ok", msg);
			continue;
		}
 
		if (!have_dasd[n]) {
			snprintf (msg, sizeof msg,
				"DASD device %s is not on-line.", d);
			newtWinMessage ("Error", "Ok", msg);
			continue;
		}
 
		/* save this mountpoint */
		mp[n] = p;
	}

	if (dasds == 0) {
		newtWinMessage ("Error", "Ok",
			"No DASD devices found.\nPlease check your setup.");
		newtFinished ();
		exit (EXIT_FAILURE);
	}
	scroll = newtVerticalScrollbar(-1, -1, DASD_HEIGHT, 
					NEWT_COLORSET_CHECKBOX,
					NEWT_COLORSET_ACTCHECKBOX);
	tb = newtTextbox (1, 0, w - 23, 2, NEWT_FLAG_WRAP);
	newtTextboxSetText (tb, "Please choose which DASDs you would like to "
		"format and where they should be mounted.");
	formats = newtForm (NULL, NULL, 0);
	for (i = 0; i < MAX_DASD; i++) {
		if (! have_dasd[i])
			continue;
		sprintf (dasd, DEV_DASD_FMT, 'a' + i);
		cb[i] = newtCheckbox ( -1, (i % 10),
			dasd, '*', NULL, NULL);
		mpf[i] = newtEntry(21, (i % 10),
			 mp[i], 20, &mp[i], NEWT_FLAG_SCROLL);
		newtFormSetWidth(mpf[i], 20);
		newtFormAddComponent (formats, cb[i]);
		newtFormAddComponent (formats, mpf[i]);
	}
	blank = newtForm(NULL, NULL, 0);
	newtFormSetWidth(blank, 1);
	newtFormSetHeight(blank, DASD_HEIGHT);
	newtFormSetWidth(formats, 30);
	if(dasdcount > DASD_HEIGHT) {
		subgrid = newtGridHCloseStacked(NEWT_GRID_COMPONENT, formats,
			NEWT_GRID_COMPONENT, blank,
			NEWT_GRID_COMPONENT, scroll, NULL);
	} else {
		subgrid = newtGridHCloseStacked(NEWT_GRID_COMPONENT, formats,
				NULL);
	}
	subform = newtForm (NULL, NULL, 0);
	newtFormSetWidth(subform, 50);
	newtGridAddComponentsToForm(subgrid, subform, 1);
	buttonbar = newtButtonBar(_("Ok"), &ok, _("Cancel"), &cancel, NULL);

	grid = newtGridBasicWindow(tb, subgrid, buttonbar);
	form = newtForm (NULL, NULL, 0);
	newtGridAddComponentsToForm(grid, form, 1);
	newtGridWrappedWindow(grid, _("DASD initialisation"));
	newtGridFree(grid, 1);
	ret = newtRunForm (form);
	if (ret == cancel) {
		newtFinished ();
		exit (EXIT_FAILURE);
	}

	for (i = 0; i < MAX_DASD; i++)
		format[i] = (have_dasd[i] &&
			newtCheckboxGetValue (cb[i]) == '*');
	newtPopWindow ();
	for (i = 0; i < MAX_DASD; i++) {
		int format_dasd, err = 0;
		char proc[256];

		if (! format[i])
			continue;

		sprintf (dasd, DEV_DASD_FMT, 'a' + i);
		newtCenteredWindow (48, 3, "DASD initialization");
		form = newtForm (NULL, NULL, 0);
		tb = newtTextbox (1, 0, 46, 3, NEWT_FLAG_WRAP);
		sprintf (tmp, "Checking DASD %s...", dasd);
		newtTextboxSetText (tb, tmp);
		newtFormAddComponent (form, tb);
		newtDrawForm (form);
		newtRefresh ();

		/* Check if we need to run dasdfmt... */
		sprintf (tmp, DASD_FMT ":active", 'a' + i);
		f = fopen (PROCDASDDEV, "r");
		format_dasd = (f && !ferror (f));
		while (format_dasd && !feof (f)) {
			fgets (proc, sizeof proc, f);
			if (strstr (proc, tmp))
				format_dasd = 0;
		}
		if (f)
			fclose (f);
		
		sprintf(tmp, "%s %s >/dev/null 2>&1", FDASD, dasd);
		f = popen(tmp, "w");
		fprintf(f, "q\n");
		if (pclose(f)) {	/* not formatted in z/OS compatible */
					/* disk layout                      */
			sprintf(tmp, 
			"DASD %s is currently formatted with the Linux disk layout (LDL).\n\n"
			"The preferred disk layout for Red Hat Linux for S/390 "
			"is the zOS compatible layout (CDL).\n\n"
			"In which layout shall it be reformatted now ?" , dasd);
			yesnoform = newtForm (NULL, NULL, 0);
			newtCenteredWindow (w - 22, h - 6, "DASD initialization");
			tb2 = newtTextbox (1, 0, 46, 9, NEWT_FLAG_WRAP);
			newtTextboxSetText (tb2, tmp);
			newtFormAddComponent (yesnoform, tb2);
			cdl = newtButton((w - 22) / 2 - 15, h - 10, "CDL");
			ldl = newtButton((w - 22) / 2 + 5, h - 10, "LDL");
			newtFormAddComponents(yesnoform, cdl, ldl, NULL);
			newtDrawForm (yesnoform);
			ret = newtRunForm(yesnoform);
			newtFormDestroy(yesnoform);
			newtPopWindow();
			newtCenteredWindow (48, 2, "DASD initialization");
			if (ret == ldl) {  /* User selected LDL format */
				/* It is already formatted, should we enable this to be sure ?
				 * It take quite long to format, so I'd rather skip it
				 */
				/*
				sprintf (tmp, "Formatting DASD %s in LDL mode.\n"
					"This can take several minutes - Please wait.", dasd);
				newtTextboxSetText (tb, tmp);
				newtDrawForm (form);
				newtRefresh ();
				sprintf (tmp, "%s -d ldl -b 4096 -y -f %s >/dev/null 2>&1", DASDFMT, dasd);
				if ((err = system (tmp))) { 
					sprintf (error,
						"Error %d while trying to run\n%s:\n%s",
						err, tmp, strerror (errno));
					newtWinMessage ("Error", "Ok", error);
					continue;
				}
				*/
			} else {   /* User selected CDL format */
				sprintf (tmp, "Formatting DASD %s in CDL mode. "
					"This can take several minutes - Please wait.", dasd);
				newtTextboxSetText (tb, tmp);
				newtDrawForm (form);
				newtRefresh ();
				sprintf (tmp, "%s -d cdl -b 4096 -y -f %s >/dev/null 2>&1", DASDFMT, dasd);
				if ((err = system (tmp))) {
					sprintf (error,
						"Error %d while trying to run\n%s\n",
						err, tmp);
					newtWinMessage ("Error", "Ok", error);
					continue;
				} else {
					sprintf (tmp, "Making a partition on DASD %s...\n",
						dasd);
					newtTextboxSetText (tb, tmp);
					newtDrawForm (form);
					newtRefresh ();
					sprintf(tmp, "%s -s -a %s >/dev/null 2>&1", FDASD, dasd);
					if ((err = system (tmp))) {
						sprintf (error,
						"Error %d while trying to run\n%s:\n%s",
						err, tmp, strerror (errno));
						newtWinMessage ("Error", "Ok", error);
						continue;
					}
				}
			}
		} else {        /* zOS compatible disk layout */
			sprintf(tmp, "%s1", dasd);
			if (((g = fopen(tmp, "r")) == NULL) || ((j = fgetc(g)) == EOF)) {
				fclose(g);
				sprintf(tmp, "DASD %s is already in zOS compatible disk layout "
					"but no partitions were found. Adding a new partition.",
					dasd);
				newtTextboxSetText (tb, tmp);
				newtDrawForm (form);
				newtRefresh ();
				sleep(3);
				sprintf(tmp, "%s -s -a %s >/dev/null 2>&1", FDASD, dasd);
				if ((err = system (tmp))) {
					sprintf (error,
					"Error %d while trying to run\n%s:\n%s",
					err, tmp, strerror (errno));
					newtWinMessage ("Error", "Ok", error);
					continue;
				}
			} else {
				sprintf(tmp, "DASD %s is already in zOS compatible disk layout. "
					"Low-level formatting is not required on this DASD.",
					dasd);
				newtTextboxSetText (tb, tmp);
				newtDrawForm (form);
				newtRefresh ();
				sleep(3);
				if(g) fclose(g);
			}
		}
		if (err == 0) {
			sprintf (tmp, "Making %s filesystem on DASD %s...\n"
				"This can take a while - Please wait.",
				"ext2", dasd);
			newtTextboxSetText (tb, tmp);
			newtDrawForm (form);
			newtRefresh ();
			sprintf (tmp, "/sbin/mke2fs -b 4096 %s1 >>"
				"/tmp/mke2fs.log 2>&1", dasd);
			err = system (tmp);
			if (err != 0) {
				sprintf (error,
					"Error %u while trying to run\n%s:\n"
					"Perhaps you need to low-level format the DASD ?"
					"Try dasdfmt -d cdl -b 4096 -y -f %s",
					err, tmp, dasd);
				newtWinMessage ("Error", "Ok", error);
				newtPopWindow ();
				newtFinished ();
				exit (EXIT_FAILURE);
			}
		}
		newtPopWindow ();
	}
	f = fopen (argv[1], "w");
	for (i = 0; i < MAX_DASD; i++) {
		if (have_dasd[i]) {
			char tmp[512];
			sprintf (dasd, DEV_DASD_FMT_P1, 'a' + i);
			mp[i] = newtEntryGetValue (mpf[i]);
			if (mp[i] && strlen (mp[i])) {
				int err;
				fprintf (f, "%s:%s\n", dasd, mp[i]);
				snprintf (tmp, sizeof (tmp),
					"/sbin/tune2fs -L %s %s"
					" >/dev/null 2>&1", mp[i], dasd);
				err = system (tmp);
				if (err != 0) {
					char s[2048];
					snprintf (s, sizeof (s),
						"Error %u while "
						"running\n%s:\n%s", err, tmp,
						strerror (errno));
					newtWinMessage ("Error", "Ok", s);
				}
			}
		}
	}
	if(f) fclose (f);
	newtFinished ();
	exit (EXIT_SUCCESS);
}
