/* /proc/partitions */
#include "balkan.h"

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define next_line(foo) while (*foo && *foo != '\n') foo++; \
			     if (!*foo) goto out; \
			     *foo = '\0'; foo++;

#define next_field(foo) while (*foo && !isspace(*foo)) foo++; \
				if (!*foo) goto out; \
				while (*foo && isspace(*foo)) foo++; \
			        if (!*foo) goto out;
			       


int procpReadTable(char *device, struct partitionTable * table) {
	int fd, currpart = 0, i;
	char *buf, *tmp, *part, *dev;
	unsigned long size;
	
	fd = open("/proc/partitions", O_RDONLY);
	buf = alloca(32768);
	if ( (i = read(fd,buf,32768)) == -1)
	  return BALKAN_ERROR_BADMAGIC;
	buf[i] = '\0';
	close(fd);
	
	dev = device;
	if (!strncmp(device,"/dev/",5) || !strncmp(device,"/tmp/",5))
	  dev = device + 5;
	else
	  dev = device;

	table->sectorSize = 512;
	table->maxNumPartitions = 0;
	for (i=0; i<50; i++) {
		table->parts[i].type = -1;
	}
	
	next_line(buf);
	next_line(buf);

	while (1) {
		next_field(buf);
		next_field(buf);
		next_field(buf);
	
		size = strtoul(buf,NULL,10);
		next_field(buf);
		tmp = part = buf;
		next_line(buf);
		while (*tmp && !isspace(*tmp)) tmp++;
		*tmp = '\0';
		if (!strncmp(dev, part, strlen(dev)) && strcmp(dev,part)) {
			table->maxNumPartitions++;
			table->parts[currpart].type = BALKAN_PART_EXT2;
			table->parts[currpart].size = size * 2;
			table->parts[currpart].startSector = 0;
			currpart++;
		}
	}
out:
	return 0;
}
