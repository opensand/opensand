#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Setup file for the OpenSAND collector.
"""

###############################################################################
# First override the distutils.archive_util.make_tarball function             #
# with an option to follow symlinks when creating archive (for ChangeLog)     #
###############################################################################

import distutils.archive_util
from distutils.spawn import spawn
from distutils.dir_util import mkpath
import os

def my_make_tarball (base_name, base_dir, compress="gzip",
                  verbose=0, dry_run=0):
    """Create a (possibly compressed) tar file from all the files under
    'base_dir'.  'compress' must be "gzip" (the default), "compress",
    "bzip2", or None.  Both "tar" and the compression utility named by
    'compress' must be on the default program search path, so this is
    probably Unix-specific.  The output tar file will be named 'base_dir' +
    ".tar", possibly plus the appropriate compression extension (".gz",
    ".bz2" or ".Z").  Return the output filename.
    """
    # XXX GNU tar 1.13 has a nifty option to add a prefix directory.
    # It's pretty new, though, so we certainly can't require it --
    # but it would be nice to take advantage of it to skip the
    # "create a tree of hardlinks" step!  (Would also be nice to
    # detect GNU tar to use its 'z' option and save a step.)

    compress_ext = { 'gzip': ".gz",
                     'bzip2': '.bz2',
                     'compress': ".Z" }

    # flags for compression program, each element of list will be an argument
    compress_flags = {'gzip': ["-f9"],
                      'compress': ["-f"],
                      'bzip2': ['-f9']}

    if compress is not None and compress not in compress_ext.keys():
        raise ValueError, \
              "bad value for 'compress': must be None, 'gzip', or 'compress'"

    archive_name = base_name + ".tar"
    mkpath(os.path.dirname(archive_name), dry_run=dry_run)
    cmd = ["tar", "-chf", archive_name, base_dir]
    spawn(cmd, dry_run=dry_run)

    if compress:
        spawn([compress] + compress_flags[compress] + [archive_name],
              dry_run=dry_run)
        return archive_name + compress_ext[compress]
    else:
        return archive_name
    
MY_ARCHIVE_FORMATS = {
    'gztar': (my_make_tarball, [('compress', 'gzip')], "gzip'ed tar-file"),
    'bztar': (my_make_tarball, [('compress', 'bzip2')], "bzip2'ed tar-file"),
    'ztar':  (my_make_tarball, [('compress', 'compress')], "compressed tar file"),
    'tar':   (my_make_tarball, [('compress', None)], "uncompressed tar file"),
    'zip':   (distutils.archive_util.make_zipfile, [],"ZIP file")
    }
 
distutils.archive_util.ARCHIVE_FORMATS = MY_ARCHIVE_FORMATS

###############################################################################

from setuptools import setup, find_packages

setup(
    name="opensand-collector",
    version="1.0.0",
    author="Vincent Duvert",
    author_email="vduvert@toulouse.viveris.com",
    description=("Statistics and events collector for OpenSAND platform"),
    license="GPL",
    url="http://opensand.org",
    packages=find_packages(),
    scripts=["sand-collector"],
)
