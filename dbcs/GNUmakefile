include ../Makefile.inc

CFLAGS = -g -Wall

objects = widestr.o

.PHONY: all
all: Makefile
	make -f Makefile

widestr.o: widestr.c widestr.h
Makefile: Setup Makefile.pre.in
	make -f Makefile.pre.in boot

.PHONY: install
install: all
	install dbcs.so $(DESTDIR)/$(PYTHONLIBDIR)

.PHONY: clean
clean: Makefile
	$(RM) $(objects)
	make -f Makefile $@

.PHONY: distclean
distclean: clean
	$(RM) core widestr dbcs.so Makefile Makefile.pre config.c sedscript
