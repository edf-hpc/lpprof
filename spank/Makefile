CC=gcc
LDFLAGS=-shared -fPIC

lpprof.so: lpprof.c lpprof_util.c
	${CC} -o $@ ${LDFLAGS} $^

clean:
	rm -f *.so
