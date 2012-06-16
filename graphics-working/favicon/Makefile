


images	= favicon-16.ppm favicon-mask-16.pgm \
		favicon-32.ppm favicon-mask-32.pgm \
		favicon-64.ppm favicon-mask-64.pgm \
		favicon-96.ppm favicon-mask-96.pgm


all: favicon.ico

install: all
	cp -p favicon.ico ../../static/style

clean:
	rm -f $(images)
	rm -f favicon.ico

favicon.ico: $(images)
	ppmtowinicon -and $(images) > $@

.SUFFIXES: .png .ppm .pgm

.png.ppm:
	pngtopnm $< > $@

.png.pgm:
	pngtopnm $< | ppmtopgm > $@

