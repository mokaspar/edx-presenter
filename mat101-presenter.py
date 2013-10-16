#!/usr/bin/env python
# -*- coding: utf-8 -*- 
VERSION = "1.0.4"
# Official repo: https://github.com/pdehaye/edx-presenter
# (a fork of mokaspar's release)

# Originally authored by mokaspar (edx-presenter.py), 
# tailored for mat101 by Paul-Olivier Dehaye (mat101-presenter.py)



# To see the full help, type: ./mat101-presenter.py --help

"""
README

This comman line tool requires the PyYAML library. This library can be installed by the following two commands in your shell:
$ easy_install pip
$ pip install pyyaml

"""


usage = """usage: %prog [options] <source1>, [<source2>,...]


Introduction:
This command line tool converts groups into an edx course. It also individually compresses groups into single files.
A group is a local directory or remote GIT repository containing a 'group.yaml' file (for more information on YAML, see http://en.wikipedia.org/wiki/YAML). This file describes the content of the group and must contain the following properties:

project: Project A
group: Group 1
authors:
  - name: mokaspar
    email: mokaspar@gmail.com
    edx: NotAvailable
content:
  - pdf: docs/introduction.pdf
  - html: docs/html1.html
  - text: docs/simple.txt
  - html: docs/html2.html
  - file: docs/sample-data.zip
  - video: http://www.youtube.com/watch?v=04ZOMuAg2bA
  - source: src/

The order order of the content is preserved and the same content type can be added multiple times.
The paths are expected to be relative to the directory containing the 'group.yaml' file. 
'pdf', 'html' and 'text' just process one file but 'source' processes all files in the directory and it's subdirectories.
Note that you can use LaTeX in 'html' and 'text' files inside the usual \[ ... \] block.
'video' currently supports just YouTube. Remember to make your video public, or at least unlisted.


Remark:
- All files are expected to be UTF-8 encoded.
"""

# Source
"""

Workflow
1. A temporary directory is created
2. All GIT sources are cloned inside this temporary directory
3. The 'group.yaml' of each group is interpreted to build the data tree.
4. A edx directory is created inside the temporary directory, into which all the data is processed
5. The edx directory gets compressed


The source is in 3 parts (reversed to the workflow)

Part 1:
For each content type there is a class ContentXXX which takes care about generating the files for the edx directory

Part 2:
Group and project is represented by a class.

Part 3:
Contains the __main__ method and does the GIT handling


"""

DISPLAY_NAME = "MAT101 projects"
ORG_NAME = "IMATHatUZH"
PROFILE_BASE = "http://edx.math.uzh.ch/courses/IMATHatUZH/MAT101/Fall_2013/wiki/MAT101/profiles/"

# Handles command line arguments
from optparse import OptionParser

# Logging functionality of python.
import logging

# XML and yaml
from xml.etree.cElementTree import Element, SubElement, ElementTree


# Regular expressions
import re

# Packages for file and process operatons
import sys
import os
import tarfile
import subprocess
import shutil
import tempfile

# utf-8 support
import codecs

# misc
import uuid
import operator
import cgi
import urlparse

# PyYAML is not a core module.
try:
    import yaml
except ImportError: 
    print """ERROR: The module PyYAML is required but missing. You can install it with the following commands:
$ easy_install pip
$ pip install pyyaml
"""
    sys.exit(1)



def escape(string):
    '''Escapes the string for HTML.'''
    return cgi.escape(string).encode('ascii', 'xmlcharrefreplace')


# --- Part 1 -----------------------------------------------------------------

class ContentDiscussion:

    def __init__(self, parent):
        self.parent = parent

    def url_name(self):
        "Using the fact, that there is exactly one discussion for each group."
        return re.sub(r'\W+', '', self.parent.url_name() + '_discussion')

    def edx(self, out_dir):
        discussion_dir = os.path.join(out_dir, 'discussion')
        if not os.path.exists(discussion_dir):
            os.makedirs(discussion_dir)
        discussion = Element('discussion', {'discussion_id':self.url_name(), 
                                            'discussion_category': self.parent.project(), 
                                            'discussion_target': self.parent.group() })
        tree = ElementTree(discussion)
        tree.write(os.path.join(discussion_dir, "{0}.xml".format(self.url_name())) )

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'discussion', {'url_name':self.url_name()})


class ContentIntro:

    def __init__(self, parent):
        self.parent = parent

    def url_name(self):
        "Using the fact, that there is exactly one intro for each group."
        return re.sub(r'\W+', '', self.parent.url_name() + '_intro')

    def edx(self, out_dir):

        # Create the HTML-page with the details
        html_dir = os.path.join(out_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        html = Element('html', {'filename':self.url_name(), 'display_name':"Intro"});
        tree = ElementTree(html)
        tree.write(os.path.join(html_dir, "{0}.xml".format(self.url_name())) )

        #Create the corresponding html-file
        html = '''<h2>%(project)s: %(group)s</h2>
        ''' % {'project':escape(self.parent.project()), 'group':escape(self.parent.group()) }

        html += '<div class="authors">Author(s):<ul>'
        for author in self.parent.authors():
            profile_URL = PROFILE_BASE + escape(author['edx']) + "/"
            print "Please check that the following profile exists", profile_URL
            html += '<li><a href="mailto:%(email)s">%(name)s</a> AKA <a href="%(profile_URL)s">%(edx)s</a></li>' %  {
                'email':escape(author.get('email',"")), 
                'name':escape(author['name']), 
                'edx':escape(author['edx']), 
                'profile_URL':profile_URL}

        html += '</ul></div>'

        with codecs.open(os.path.join(html_dir, "{0}.html".format(self.url_name())), mode='w', encoding='utf-8') as f:
            f.write(html)

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'html', {'url_name':self.url_name()})


class ContentHTML:

    def __init__(self, parent, path):
        logging.debug("ContentHTML:__init__ %s", path)
        self.parent = parent
        self.path = path

    def url_name(self):
        return re.sub(r'\W+', '', self.parent.url_name() + '_html_' + self.path)

    def edx(self, out_dir):
        html_dir = os.path.join(out_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        html = Element('html', {'filename':self.url_name(), 'display_name':"HTML"});
        tree = ElementTree(html)
        tree.write(os.path.join(html_dir, "{0}.xml".format(self.url_name())) )

        #Copy the corresponding html-file
        shutil.copyfile(os.path.join(self.parent.path, self.path), os.path.join(html_dir, "{0}.html".format(self.url_name())) );

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'html', {'url_name':self.url_name()})


class ContentFile:

    def __init__(self, parent, path):
        logging.debug("ContentFile:__init__ %s", path)
        self.parent = parent
        self.path = path

    def url_name(self):
        fileName, fileExtension = os.path.splitext(self.path)
        return re.sub(r'[^(\w|.)]+', '', self.parent.url_name() + '_' + fileName)

    def edx(self, out_dir):
        # Copy the Pdf to the static directory
        static_dir = os.path.join(out_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        # In order to get an unique filename inside edx, we have to prefix the project and group name
        _, fileExtension = os.path.splitext(self.path)
        target_filename = self.url_name()+fileExtension
        target_path = os.path.join(static_dir,target_filename)
        shutil.copyfile(os.path.join(self.parent.path, self.path), target_path);

        html_dir = os.path.join(out_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        html = Element('html', {'filename':self.url_name(), 'display_name':"File"});
        tree = ElementTree(html)
        tree.write(os.path.join(html_dir, "{0}.xml".format(self.url_name())) )


        (_ , filename) = os.path.split(self.path)
        html = '''
        <a href="/static/%(file)s">Download %(filename)s</a>
        ''' % {'file':target_filename, 'filename':filename}

        with codecs.open(os.path.join(html_dir, "{0}.html".format(self.url_name())), mode='w', encoding='utf-8') as f:
            f.write(html)

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'html', {'url_name':self.url_name()})


class ContentSource:

    def __init__(self, parent, path):
        logging.debug("ContentSource:__init__ %s", path)
        self.parent = parent
        self.path = path

    def url_name(self):
        return re.sub(r'\W+', '', self.parent.url_name() + '_source_' + self.path)

    def edx(self, out_dir):

        # Path of the source directory relative to our working directory
        path_complete = os.path.join(self.parent.path, self.path)

        # Create a archive with the source inside the static directory
        static_dir = os.path.join(out_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        # In order to get an unique filename inside edx, we have to prefix the project and group name
        target_filename = self.url_name()+'.tar.gz'
        target_path = os.path.join(static_dir, target_filename)
        tar = tarfile.open(target_path, "w:gz")
        tar.add(path_complete, arcname=os.path.basename(path_complete))
        tar.close()


        html_dir = os.path.join(out_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        html = Element('html', {'filename':self.url_name(), 'display_name':"Source"});
        tree = ElementTree(html)
        tree.write(os.path.join(html_dir, "{0}.xml".format(self.url_name())) )

        html = '''<h3>Source of %(path)s</h3>
        ''' % {'path':escape(self.path) }

        html += '''
        <a href="/static/%(file)s">Download source as archive</a>
        ''' % {'file':target_filename}

        if self.path[-3:] == ".py":
            # Link to a single file
            # We simulate the output of os.walk:
            tmp_path = os.path.split(os.path.join(self.parent.path, self.path))
            cleaned_path = [(os.path.join(tmp_path[:-1][0]), None, [tmp_path[-1]])]
        else:
            cleaned_path = os.walk(os.path.join(self.parent.path, self.path))

        for dirname, dirnames, filenames in cleaned_path:
            # Process each file
            for filename in filenames:

                #ignore any non-python file
                if not filename.endswith('.py') or filename.startswith('.'):
                    continue

                path_full = os.path.join(dirname, filename)
                # This path is relative to the group definition
                path_relative = path_full[len(self.parent.path):]

                html += '<h3>%(path)s</h3>\n' % {'path':escape(path_relative)}

                # It would be better to control the font-size by the theme
                html += '<script src="https://google-code-prettify.googlecode.com/svn/loader/run_prettify.js?skin=tomorrow"></script>'
                html += '<pre class="prettyprint python">'
                with codecs.open(path_full, mode='r', encoding='utf-8') as f:
                    html += escape(f.read())
                html += '</pre>'

        with codecs.open(os.path.join(html_dir, "{0}.html".format(self.url_name())), mode='w', encoding='utf-8') as f:
            f.write(html)

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'html', {'url_name':self.url_name()})


class ContentText:

    def __init__(self, parent, path):
        logging.debug("ContentText:__init__ %s", path)
        self.parent = parent
        self.path = path

    def url_name(self):
        return re.sub(r'\W+', '', self.parent.url_name() + '_text_' + self.path)

    def edx(self, out_dir):
        html_dir = os.path.join(out_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        html = Element('html', {'filename':self.url_name(), 'display_name':"Text"});
        tree = ElementTree(html)
        tree.write(os.path.join(html_dir, "{0}.xml".format(self.url_name())) )

        html = ''
        html += '<div>'
        with codecs.open (os.path.join(self.parent.path, self.path), mode="r", encoding='utf-8') as f:
            html += re.sub('\n', '<br/>',escape(f.read()) )
        html += '</div>'

        with codecs.open(os.path.join(html_dir, "{0}.html".format(self.url_name())), mode='w', encoding='utf-8') as f:
            f.write(html)

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'html', {'url_name':self.url_name()})


class ContentVideoYouTube:

    def __init__(self, parent, youtube_id):
        logging.debug("ContentVideoYouTube:__init__ %s", youtube_id)
        self.parent = parent
        self.youtube_id = youtube_id

    def url_name(self):
        return re.sub(r'\W+', '', self.parent.url_name() + '_youtube_' + self.youtube_id)

    def edx(self, out_dir):
        video_dir = os.path.join(out_dir, 'video')
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        video = Element('video', {'youtube':'1.00:'+self.youtube_id, 'youtube_id_1_0':self.youtube_id});
        tree = ElementTree(video)
        tree.write(os.path.join(video_dir, "{0}.xml".format(self.url_name())) )


    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'video', {'url_name':self.url_name()})


class ContentPdf:

    def __init__(self, parent, path):
        logging.debug("ContentPdf:__init__ %s", path)
        self.parent = parent
        self.path = path

    def url_name(self):
        return re.sub(r'\W+', '', self.parent.url_name() + '_' + self.path)

    def edx(self, out_dir):
        # Copy the Pdf to the static directory
        static_dir = os.path.join(out_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        # In order to get an unique filename inside edx, we have to prefix the project and group name
        target_filename = self.url_name()+'.pdf'
        target_path = os.path.join(static_dir,target_filename)
        shutil.copyfile(os.path.join(self.parent.path, self.path), target_path);

        html_dir = os.path.join(out_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        html = Element('html', {'filename':self.url_name(), 'display_name':"Pdf"});
        tree = ElementTree(html)
        tree.write(os.path.join(html_dir, "{0}.xml".format(self.url_name())) )

        # We have to double %% because % is a placeholder for the argument
        html = ''
        if courseURL == None:
            logging.warning("courseURL is not specified. Therefore the inline pdf-viewer will be disabled.")
        else:
            html += '''
            <iframe src="http://docs.google.com/viewer?url=%(courseURL)s/asset/%(file)s&embedded=true"  style="border: none; width:100%%; height:780px;"></iframe>
            ''' % {'courseURL':courseURL , 'file':target_filename}
        
        html += '''
        <a href="/static/%(file)s">Download Pdf %(name)s</a>
        ''' % {'file':target_filename, 'name':os.path.basename(self.path)}

        with codecs.open(os.path.join(html_dir, "{0}.html".format(self.url_name())), mode='w', encoding='utf-8') as f:
            f.write(html)

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'html', {'url_name':self.url_name()})

class ContentImg:
    def __init__(self, parent, path):
        logging.debug("ContentImg:__init__ %s", path)
        self.parent = parent
        self.path = path

    def url_name(self):
        return re.sub(r'\W+', '', self.parent.url_name() + '_' + self.path)

    def edx(self, out_dir):
        # Copy the image to the static directory
        static_dir = os.path.join(out_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        # In order to get an unique filename inside edx, we have to prefix the project and group name
        # We cannot use the filename, because it may contain characters, that have to be escaped.
        # Therefore we just add the extension, which is expected to contain [a-z][A-Z][0-9].
        _, fileExtension = os.path.splitext(self.path)
        target_filename = self.url_name()+fileExtension
        target_path = os.path.join(static_dir,target_filename)
        shutil.copyfile(os.path.join(self.parent.path, self.path), target_path);

        html_dir = os.path.join(out_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        html = Element('html', {'filename':self.url_name(), 'display_name':"Img"});
        tree = ElementTree(html)
        tree.write(os.path.join(html_dir, "{0}.xml".format(self.url_name())) )

        # We have to double %% because % is a placeholder for the argument
        html = '<img src="/static/%(file)s">' % {'file':target_filename}
        
        html += '''<br>
        <a href="/static/%(file)s">Download Image %(name)s</a>
        ''' % {'file':target_filename, 'name':os.path.basename(self.path)}

        with codecs.open(os.path.join(html_dir, "{0}.html".format(self.url_name())), mode='w', encoding='utf-8') as f:
            f.write(html)

    def parent_tag(self, xml):
        "Adds the XML element pointing to this resoure to the vertical."
        e = SubElement(xml, 'html', {'url_name':self.url_name()})


# --- Part 2 -----------------------------------------------------------------


class Project:

    def __init__(self,project):
        self.project = project
        self.groups = []

    def append(self, group):
        """Appends a group to a project and keeps the groups list sorted"""
        self.groups.append(group)
        self.groups = sorted(self.groups, key=operator.methodcaller('group'))

    def __len__(self):
        return len(self.groups)

    def __getitem__(self, key):
        return self.groups[key]

    def url_name(self):
        """Just keeps the basic ASCII characters: It removes any whitespaces and umlauts."""
        return re.sub(r'\W+', '', self.project)

    def __repr__(self):
        return "<Project '{0}' {1}>".format(escape(self.project), repr(self.groups))

    def edx(self, out_dir):
        chapter_dir = os.path.join(out_dir, 'chapter')
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)
        chapter = Element('chapter', {'display_name':escape(self.project)});
        for group in self.groups:
            e = SubElement(chapter, 'sequential')
            e.set('url_name', group.url_name())
        tree = ElementTree(chapter)
        tree.write(os.path.join(chapter_dir, "{0}.xml".format(self.url_name())) )

        for group in self.groups:
            group.edx(out_dir)


class Group:
    """Represents a submitted group."""

    def __init__(self, path):
        self.path = path
        self.content = []

    def load(self):
        """Reads the definition file of this group."""

        # We don't catch any exception here, because the using function should decide on what to do.
        f = codecs.open(os.path.join(self.path, 'group.yaml'), mode='r', encoding='utf-8')
        self.properties = yaml.safe_load(f)

        self.content = []
        self.content.append(ContentIntro(self))

        for c in self.properties['content']:
            co = None
            if 'html' in c:
                co = ContentHTML(self, c['html'])
            if 'source' in c:
                co = ContentSource(self, c['source'])
            if 'text' in c:
                co = ContentText(self, c['text'])
            if 'video' in c:
                # We currently only support youtube
                o = urlparse.urlparse(c['video'])
                if o.netloc == 'www.youtube.com':
                    co = ContentVideoYouTube(self, o.query[2:])
                else:
                    raise SubprocessError('Undefined video source {0}'.format(c['video']))
            if 'pdf' in c:
                co = ContentPdf(self, c['pdf'])
            if 'file' in c:
                co = ContentFile(self, c['file'])
            if 'img' in c:
                co = ContentImg(self, c['img'])


            if co is not None:
                self.content.append(co)
            else:
                logging.info('Undefined source %s', c)

        self.content.append(ContentDiscussion(self))

    def project(self):
        return self.properties['project']

    def group(self):
        return self.properties['group']

    def authors(self):
        return self.properties['authors']

    def url_name(self):
        """Just keeps the basic ASCII characters: It removes any whitespaces and umlauts."""
        return re.sub(r'\W+', '', (self.project() + '__' + self.group()).replace(" ","_") )

    def __repr__(self):
        return "<Group '{0}/{1}'>".format(escape(self.project()), escape(self.group()))

    def edx(self, out_dir):
        sequential_dir = os.path.join(out_dir, 'sequential')
        if not os.path.exists(sequential_dir):
            os.makedirs(sequential_dir)
        sequential = Element('sequential', {'display_name':escape(self.group())});
        e = SubElement(sequential, 'vertical')
        e.set('url_name', self.url_name()+'_vertical')
        tree = ElementTree(sequential)
        tree.write(os.path.join(sequential_dir, "{0}.xml".format(self.url_name())) )

        vertical_dir = os.path.join(out_dir, 'vertical')
        if not os.path.exists(vertical_dir):
            os.makedirs(vertical_dir)
        vertical = Element('vertical', {'display_name':'MainUnit'});

        for c in self.content:
            c.parent_tag(vertical)
            c.edx(out_dir)

        tree = ElementTree(vertical)
        tree.write(os.path.join(vertical_dir, "{0}.xml".format(self.url_name()+'_vertical')) )


# --- Part 3 -----------------------------------------------------------------


# This customized LoggingFormatter formats all the output of this tool.
class LoggingFormatter(logging.Formatter):
    FORMATS = {logging.DEBUG :    "DEBUG: %(module)s: %(lineno)d: %(message)s",
               logging.ERROR :     "ERROR: %(message)s",
               logging.WARNING : "WARNING: %(message)s",
               logging.INFO : "%(message)s",
               'DEFAULT' :         "%(levelname)s: %(message)s"
               }

    def format(self, record):
        self._fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        return logging.Formatter.format(self, record)


class SubprocessError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def main():

    # The following block parses the arguments supplied.
    parser = OptionParser(usage=usage)
    parser.add_option("-u", "--course-url", default=None,
                      dest="course_url",
                      help="Specifies the public URL of the course. It is used for the inline Pdf viewer using Google-Docs. [default: %default]")
    parser.add_option("-v", "--verbose",
                      action="count", dest="verbose", default=False,
                      help="Increase verbosity (specify multiple times for more)")
    parser.add_option("-o", "--output", default="to_import.tar.gz",
                      metavar="FILE", dest="output",
                      help="Specifies the filename of the generated edx-file relative to the working directory. [default: %default]")
    parser.add_option("--tmp",
                      metavar="DIR", dest="tmp",
                      help="""Configures the directory to use for the intermediate files.
If set, this direcory will not be deleted. If not specified, 
a temporary directory is created by the operating system and deleted.
"""
                      )
    (options, sources) = parser.parse_args()

    global courseURL
    courseURL = options.course_url

    # Setting up the logging facility.
    log_level = logging.WARNING
    if options.verbose == 1:
        log_level = logging.INFO
    elif options.verbose >= 2:
        log_level = logging.DEBUG

    fmt = LoggingFormatter()
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(fmt)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(log_level)


    # When debugging, it's always good to know the values of the following variables:
    logging.debug("Options %s", options)
    logging.debug("Sources %s", sources)


    if len(sources) == 0:
        logging.error("Expects least one source.")
        parser.print_help()
        sys.exit(1)

    
    try:
        # Setup of our temorary directory, where we do all the file processing.
        if options.tmp is None:
            tmp_dir = tempfile.mkdtemp();
        else:
            tmp_dir = options.tmp
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
        logging.debug("Temporary directory: %s", tmp_dir)


        # The strategy is as follows:
        # projects is a dictionary with the project name as the key and a list of groups as values.
        # When all groups are loaded, we transform the dict into a tuple, sort it and sort all the groups inside each project.
        projects = {}


        # If we are verbose, we print stdout/stderr of subprocesses (GIT).
        subprocess_setting = {'stderr':subprocess.PIPE, 'stdout':subprocess.PIPE}
        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            subprocess_setting = {'stderr':None, 'stdout':None}

        # We now load each source.
        for source in sources:
            if not os.path.exists(source):
                if source.endswith(('zip', 'tar.gz')):
                    logging.info("Assuming that %s is a remote archive.", source)

                    # requests is not a core module.
                    try:
                        import requests
                    except ImportError: 
                        print """ERROR: The module requests is required but missing for remote archives. You can install it with the following commands:
$ easy_install pip
$ pip install requests
"""
                        sys.exit(1)

                    # We need a 'unique' directory for the local checkout
                    dest = str(uuid.uuid4())
                    local_path = os.path.join(tmp_dir, dest)
                    os.makedirs(local_path)

                    # Wen need the file-extension of the remote file
                    o = urlparse.urlparse(source)
                    (_ , filename_compressed) = os.path.split(o.path)
                    archive_path = os.path.join(local_path, filename_compressed)
                    logging.info("Downloading remote archive to %s.", archive_path);

                    with open(archive_path, 'wb') as handle:
                        request = requests.get(source, stream=True)
                        # Raise in case of server/network problems: (4xx, 5xx, ...)
                        request.raise_for_status()

                        for block in request.iter_content(1024):
                            if not block:
                                break
                            handle.write(block)

                    if archive_path.endswith('.zip'):
                        # We use the external unzip utility.
                        logging.info("Unzip %s", source)
                        try:
                            p = subprocess.Popen(['unzip', archive_path], cwd=local_path, **subprocess_setting)
                            p.wait()
                            if p.returncode != 0:
                                logging.error("Failed to unzip  %s", source)
                                raise SubprocessError("Failed to unzip %s".format(source))

                        except OSError:
                            logging.error("unzip not found. Do you have unzip installed?")
                            raise

                    if archive_path.endswith('.tar.gz'):
                        # We use the external untar utility.
                        logging.info("untar %s", source)
                        try:
                            p = subprocess.Popen(['tar', '-zxvf', archive_path], cwd=local_path, **subprocess_setting)
                            p.wait()
                            if p.returncode != 0:
                                logging.error("Failed to untar  %s", source)
                                raise SubprocessError("Failed to untar %s".format(source))

                        except OSError:
                            logging.error("tar not found. Do you have tar installed?")
                            raise

                    # We search for a file called group.yaml, which gives us the directory to process
                    path = None
                    for dirname, dirnames, filenames in os.walk(local_path):

                        # Process each file
                        for filename in filenames:
                            if filename == 'group.yaml':
                                logging.debug("Found a group.yaml file inside %s.", dirname)
                                path = dirname
                    if path==None:
                        logging.error("No group.yaml file found in %s", source)
                        raise SubprocessError("No group.yaml file found in %s".format(source))


                else:
                    logging.info("There is no directory %s. Assuming that it's a remote GIT repository.", source)
                    # We need a 'unique' directory for the local checkout
                    dest = str(uuid.uuid4())
                    path = os.path.join(tmp_dir, dest)

                    logging.warning("Cloning %s", source)
                    try:
                        p = subprocess.Popen(['git', 'clone', source, dest], cwd=tmp_dir, **subprocess_setting)
                        p.wait()
                        if p.returncode != 0:
                            logging.error("Failed to clone GIT repository %s", source)
                            raise SubprocessError("Failed to clone GIT repository %s".format(source))

                    except OSError:
                        logging.error("GIT not found. Do you have GIT installed?")
                        raise
            else:
                path = source


            logging.info("Processing %s", path)
            
            # We load the group definition and add it to the corresponding group.            
            g = Group(path)
            g.load()
            if g.project() not in projects:
                projects[g.project()] = Project(g.project())
            projects[g.project()].append(g)

            print "Archiving %(path)s as %(url_name)s" % { 'path':path, 'url_name':g.url_name()}
            tar = tarfile.open(g.url_name()+".tar.gz", "w:gz")
            
            tar.add(path, arcname = g.url_name())
            tar.close()



        # Sort the projects alphabetically
        projects = projects.values()
        list.sort(projects, key=operator.attrgetter('project'))
        

        # We now have successfully read all groups and we proceed to create the edx course.

        # Setup the edx directory structure 
        # All the other files and directories inside are uuid named. We don't have to fear a name clash.
        out_dir = os.path.join(tmp_dir, DISPLAY_NAME)
        # Delete the output directory, if it already exists
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir)

        # Create course.xml
        course = Element('course');
        course.set('url_name', 'url_name')
        course.set('org', ORG_NAME)
        course.set('course', 'course')
        tree = ElementTree(course)
        tree.write(os.path.join(out_dir, "course.xml"))

        # Create course/course.xml
        course_dir = os.path.join(out_dir, 'course')
        os.makedirs(course_dir)
        course = Element('course');
        course.set('display_name', DISPLAY_NAME)
        for project in projects:
            e = SubElement(course, 'chapter')
            e.set('url_name', project.url_name())
        tree = ElementTree(course)
        tree.write(os.path.join(course_dir, "{0}.xml".format('url_name')) )                

        # Let each project and implicitly each group create it's files
        for project in projects:
            project.edx(out_dir)

        # Archive the directory to the output file
        print "Creating the archive %(path)s" % { 'path':options.output}
        tar = tarfile.open(options.output, "w:gz")
        tar.add(out_dir, arcname=os.path.basename(out_dir))
        tar.close()


    # If any expection occurs, we still want to delete the temporary directory.
    finally:
        try:
            # We don't delete the temp_dir if it's path was specified by the user.
            if options.tmp is None:
                shutil.rmtree(tmp_dir)
            else:
                logging.warning("The manually set temporary directory won't be deleted (%s).", tmp_dir)
        except OSError as exc:
            if exc.errno != 2: # Unless the error says, that the tmp-directory doesn't exist anymore.
                raise 


if __name__ == '__main__':
    print "This is mat101-presenter, version ", VERSION
    main()
    print "\n\nPlease TEST your project on a sandbox before submitting."




