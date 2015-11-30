#!/bin/bash
for i in *.tex; 
do 
	if [[ $i != "config.tex" ]]; then 
		pdflatex $i 
	fi 
done;
for i in *.pdf; do mv $i ../pdf/$i; done;