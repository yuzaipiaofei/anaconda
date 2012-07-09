#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <glob.h>

#include "rpmutils.h"
#include "dud_utils.h"

static const char shortopts[] = "a:d:k:v";

enum {
    OPT_NONE = 0,
};

static const struct option longopts[] = {
    //{name, no_argument | required_argument | optional_argument, *flag, val}
    {"directory", required_argument, NULL, 'd'},
    {"kernel", required_argument, NULL, 'k'},
    {"anaconda", required_argument, NULL, 'a'},
    {"verbose", no_argument, NULL, 'v'}
};

struct _version_struct {
    char* kernel;
    char* anaconda;
};

int globErrFunc(const char *epath, int eerrno)
{
    /* TODO check fatal errors */

    return 0;
}


/*
 * check if the RPM in question provides
 * Provides: <dep> = <version>
 * we use it to check if kernel-modules = <kernelversion>
 */
int dlabelProvides(const char* dep, const char* version, uint32_t sense, void *userptr)
{
    char *kernelver = ((struct _version_struct*)userptr)->kernel;
    char *anacondaver = ((struct _version_struct*)userptr)->anaconda;

    int packageflags = 0;

    //logMessage(DEBUGLVL, "Provides: %s = %s", dep, version);

    if (version == NULL)
        return 0;

    /* is it a modules package? */
    if (!strcmp(dep, "kernel-modules")) {

        /*
         * exception for 6.0 and 6.1 DUDs, we changed the logic a bit and need to maintain compatibility.
         */
        if ((!strncmp(version, "2.6.32-131", 10)) || (!strncmp(version, "2.6.32-71", 9)))
            packageflags |= dup_modules | dup_firmwares;

        /*
         * Use this package only if the version match string is true for this kernel version
         */
        if (!matchVersions(kernelver, sense, version))
            packageflags |= dup_modules | dup_firmwares;
    }

    /* is it an app package? */
    if (!strcmp(dep, "installer-enhancement")) {

        /*
         * If the version string matches anaconda version, unpack binaries to /tmp/DD
         */
        if (!matchVersions(anacondaver, sense, version))
            packageflags |= dup_binaries | dup_libraries;
    }

    return packageflags;
}

int dlabelOK(Header *rpmheader, int packageflags)
{
}

int main(int argc, char *argv[])
{
    char *cvalue = NULL;
    int option;
    int option_index;

    char *directory = NULL;
    int verbose = 0;

    struct _version_struct versions;

    while ((option = getopt_long(argc, argv, shortopts, longopts, &option_index)) != -1) {
        switch (option) {
        case 0:
            /* long option */
            break;

        case 'd':
            directory = optarg;
            break;

        case 'k':
            versions.kernel = optarg;
            break;

        case 'a':
            versions.anaconda = optarg;
            break;

        case 'v':
            verbose = 1;
            break;
        }

    }

    char *globpattern;
    checked_asprintf(&globpattern, "%s/*.rpm", directory);

    glob_t globres;
    char** globitem;

    if (!glob(globpattern, GLOB_NOSORT|GLOB_NOESCAPE, globErrFunc, &globres)) {
        /* iterate over all rpm files */
        globitem = globres.gl_pathv;
        while (globres.gl_pathc>0 && globitem != NULL && *globitem != NULL) {
            checkDUDRPM(*globitem, dlabelProvides, NULL, dlabelOK, &versions);
            globitem++;
        }
        globfree(&globres);
        /* end of iteration */
    }
    free(globpattern);

    return 0;
}
