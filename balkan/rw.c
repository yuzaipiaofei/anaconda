#include "balkan.h"
#include "dos.h"

int balkanReadTable(char *device, int fd, struct partitionTable * table) {
    int ret;

    /* Try sun labels first: they contain
       both magic (tho 16bit) and checksum.  */
    ret = sunpReadTable(fd, table);
    if (ret != BALKAN_ERROR_BADMAGIC)
	return ret;
    ret = bsdlReadTable(fd, table);
    if (ret != BALKAN_ERROR_BADMAGIC)
	return ret;

    ret = dospReadTable(fd, table);    
    if (ret != BALKAN_ERROR_BADMAGIC)
	return ret;
      
    ret = procpReadTable(device, table);
    return ret;
}
