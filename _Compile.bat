REM Px report compile script
REM Assumes MiKTeX (TeXworks) installed
REM use as wanted

@ECHO OFF
TITLE Select action
SET de=0
CLS

ECHO 1 - Compile fast
ECHO 2 - Compile with Table of contents
ECHO 3 - Compile with references
ECHO D - Delete files
ECHO Q - Exit

SET /P comp=Your choice [1, 2, 3, D, E, Q]: 

CLS
IF %comp%==d (
    SET de=1
    GOTO d
)
IF %comp%==e GOTO ea
IF %comp%==q EXIT

SET c=%comp%
SET /A r=1

IF %comp% EQU 1 GOTO 1
IF %comp% EQU 2 GOTO 2
IF %comp% EQU 3 GOTO 3
ECHO Bad choice!
PAUSE
EXIT

:3
TITLE pdflatex: %r%/%c%
pdflatex main
SET /A r=%r%+1
CLS
TITLE bibtex
bibtex main
CLS

:2
TITLE pdflatex: %r%/%c%
pdflatex main
SET /A r=%r%+1
CLS

:1
TITLE pdflatex: %r%/%c%
pdflatex main
CLS

:d
TITLE Deleting
DEL *.log
DEL *.aux
DEL *.out
DEL *.toc
DEL *.gz
DEL *.gz(busy)
DEL *.bbl
DEL *.blg
DEL *.tdo
DEL *.lof
DEL *.brf
DEL *.lot
DEL *.dvi
IF %de% EQU 1 EXIT

REM Check compile error level
