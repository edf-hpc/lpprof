MAN = lpprof.1
MAINDOC = user_guide.html

all: $(MAN) ${MAINDOC}
clean:
	rm -f man/*.1 *.pdf *.html

%.1: source/%.md
	pandoc -f markdown -s -t man $< -o man/$@

%.html: source/%.asc
	asciidoctor -a stylesheet=source/user_guide.css $< -o $@
