#!/bin/bash
#Copyright Thalley.com
echo Choose what you want to do
echo 1 - Compile fast
echo 2 - Compile with Table of contents
echo 3 - Compile with references
echo D - Delete files
echo Q - Exit
read -p "Your choice: [1, 2, 3, D, Q] " choice
case $choice in
  3 )
	pdflatex --shell-escape master.tex
	bibtex master.tex;&
  2 )
	pdflatex --shell-escape master.tex;&
  1 ) 
	pdflatex --shell-escape master.tex;&
  D )
	rm *.log;
	rm *.aux;
	rm *.out;
	rm *.toc;
	rm *.gz;
	rm *.bbl;
	rm *.blg;
	rm *.tdo;
	rm *.brf;
	rm *.lot;
	rm *.dvi;
	rm *.lof;;
  * ) read -p "Not valid option";;
esac
