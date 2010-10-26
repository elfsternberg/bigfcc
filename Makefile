FILES = AUTHORS COPYING INSTALL README TODO \
       bigfcc.py bigfcc_man.tex Makefile

TARFILES = ${FILES} bigfcc_man.html bigfcc.1 bigfcc.man

bigfcc_man.html: bigfcc_man.tex
	latex2man -H bigfcc_man.tex bigfcc_man.html

bigfcc.1: bigfcc_man.tex
	latex2man bigfcc_man.tex bigfcc.1

bigfcc.man: bigfcc.1
	nroff -Tascii -man bigfcc.1 > bigfcc.man

all: ${TARFILES}

archive: all
	tar cvf - ${TARFILES} | gzip -9c > bigfcc.tar.gz
