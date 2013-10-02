Edx-presenter
=============

Edx-presenter.py is a python script that makes it possible to easily host virtual project presentations on the [OpenedX platform](https://github.com/edX). Presentations can consist of several components, such as HTML files, youtube videos, python source code and data files. To simplify the formatting for students, presentations are always held on just one page (i.e a vertical in edX parlance). A discussion is always appended.

With the input of a few data files and one configuration file, edx-presenter.py generates all the XML files (actually bundled in a .tar.gz) that are needed for an edX course. This bundle can then be imported into a blank edX course. The original input can be given either as a git repository, as a folder, as an archive, locally or remotely (URL). Multiple sources are allowed. 

The import should probably be done by the instructor, but the script is portable so students can run it themselves and do their own testing on an edX sandbox. 

edx-presenter.py 
----------------

See the file itself for usage information.


make.py
-------
This script creates two archives:
- edx-presenter.tar.gz is an archive that is 'edx-presenter.py' readable. This presentation describes the edx-presenter project.
- to_submit.tar.gz is an edx submittable course, that contains two presentations: one for each of the the edx-presenter and skeleton projects. This file is for testing of the two presentations.
