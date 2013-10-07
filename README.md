Edx-presenter
=============

Mat101-presenter.py is a python script that makes it possible to easily host virtual project presentations on the [OpenedX platform](https://github.com/edX). Presentations can consist of several components, such as HTML files, youtube videos, python source code and data files. To simplify the formatting for students, presentations are always held on just one page (i.e a vertical in edX parlance). A discussion is always appended.

With the input of a few data files and one configuration file, mat101-presenter.py generates all the XML files (actually bundled in a .tar.gz) that are needed for an edX course. This bundle can then be imported into a blank edX course. The original input can be given either as a git repository, as a folder, as an archive, locally or remotely (URL). Multiple sources are allowed. 

The import should probably be done by the instructor, but the script is portable so students can run it themselves and do their own testing on an edX sandbox. 

mat101-presenter.py 
-------------------

See the file itself for usage information.


License
-------

The code in this repository is licensed under version 3 of the AGPL.

Please see ``LICENSE.txt`` for details.


Credit
------
This code has been written by Kaspar Mösinger for the course ['MAT101 Programming in Python'](http://www.vorlesungen.uzh.ch/HS13/suche/sm-50648594.modveranst.html) at the Departement of Mathematics of the University of Zurich.

Special thanks goes to the instructor [Paul-Olivier Dehaye](http://user.math.uzh.ch/dehaye/), for the idea and supervising my work.
