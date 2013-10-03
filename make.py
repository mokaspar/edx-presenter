#!/usr/bin/env python
# -*- coding: utf-8 -*- 


# Handles command line arguments
from optparse import OptionParser

# Logging functionality of python.
import logging

# Packages for file and process operatons
import os
import tarfile
import subprocess
import shutil
import tempfile

# misc
import uuid



# The following block parses the arguments supplied.
parser = OptionParser(usage='Usage')
parser.add_option("-v", "--verbose",
                  action="count", dest="verbose", default=False,
                  help="Increase verbosity (specify multiple times for more)")
parser.add_option("--tmp",
                  metavar="DIR", dest="tmp",
                  help="""Configures the directory to use for the intermediate files.
If set, this direcory will not be deleted. If not specified, 
a temporary directory is created by the operating system and deleted.
"""
	                  )
(options, _) = parser.parse_args()

# Setting up the logging facility.
log_level = logging.WARNING
if options.verbose == 1:
	log_level = logging.INFO
elif options.verbose >= 2:
	log_level = logging.DEBUG
logging.root.setLevel(log_level)


# When debugging, it's always good to know the values of the following variables:
logging.debug("Options %s", options)


# Setup of our temorary directory, where we do all the file processing.
if options.tmp is None:
	tmp_dir = tempfile.mkdtemp();
else:
	tmp_dir = os.path.join(options.tmp, str(uuid.uuid4()))
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)
logging.debug("tmp directory %s", tmp_dir)


(script_directory , filename) = os.path.split(os.path.realpath(__file__))

# Copy the template of the edx-presenter
edx_dir = os.path.join(tmp_dir,'edx-presenter')
shutil.copytree(os.path.join(script_directory, 'presentations','edx-presenter'), edx_dir)


# Create a scr-directory: Empty directories are not preserved by GIT
if not os.path.exists(os.path.join(edx_dir,'src')):
	os.makedirs(os.path.join(edx_dir,'src'))
# Copy the script
shutil.copyfile(os.path.join(script_directory, 'edx-presenter.py'), os.path.join(edx_dir,'src','edx-presenter.py'))


# Compress the skeleton project and add it
skeleton_path = os.path.join(script_directory, 'presentations', 'skeleton')
archive_skeleton_path = os.path.join(edx_dir, 'files', 'skeleton.tar.gz')
if os.path.exists(archive_skeleton_path):
	os.remove(archive_skeleton_path)
tar = tarfile.open(archive_skeleton_path, "w:gz")
tar.add(skeleton_path, arcname=os.path.basename(skeleton_path))
tar.close()


# Compress the edx-presenter dir and add it to itself
tmp_archive_presenter = os.path.join(tmp_dir, 'edx-presenter.tar.gz')
tar = tarfile.open(tmp_archive_presenter, "w:gz")
tar.add(edx_dir, arcname=os.path.basename(edx_dir))
tar.close()

archive_presenter = os.path.join(edx_dir, 'files', 'edx-presenter.tar.gz')
if os.path.exists(archive_presenter):
	os.remove(archive_presenter)
shutil.copyfile(tmp_archive_presenter, archive_presenter)


# Compress the edx-project for output
tar = tarfile.open('edx-presenter.tar.gz', "w:gz")
tar.add(edx_dir, arcname=os.path.basename(edx_dir))
tar.close()


# Run the edx-presenter script
p = subprocess.Popen([os.path.join(script_directory,'edx-presenter.py'), '-v', edx_dir, os.path.join(script_directory,'presentations','skeleton')])
p.wait()
if p.returncode != 0:
	logging.error("Failed to create the edx-file")


# Delete the temp-dir
shutil.rmtree(tmp_dir)
