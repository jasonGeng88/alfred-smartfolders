#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net. All rights reserved.
#
# Created on 2013-10-29
#

"""
Search specific Smart Folder or all folders in ~/Library/Saved Searches
"""

from __future__ import print_function

import sys
import os
import logging
import subprocess

import alfred
from docopt import docopt

__usage__ = u"""Search smart folders

Usage:
    smartfolders [-f <folder>|--folder=<folder>] [<query>]
    smartfolders (-h|--help)
    smartfolders --helpfile

Options:
    -f, --folder=<folder>   Search contents of named folder
                            Specify the folder name, not the path
    -h, --help              Show this message
    --helpfile              Open the enclosed help file in your web browser

"""

MAX_RESULTS = 50
HELPFILE = os.path.join(os.path.dirname(__file__), u'Help.html')

# logging.basicConfig(filename=os.path.join(alfred.work(volatile=True),
#                                           'smartfolders.log'),
#                     level=logging.DEBUG)

# log = logging.getLogger(u'smartfolders')


def open_help_file():
    subprocess.call([u'open', HELPFILE])


def make_folder_items(folders):
    """Make alfred.Item for smart folders `folders`

    Returns:
        list of alfred.Item instances
    """
    items = []
    for i, folder in enumerate(folders):
        folder, path = folder
        item = alfred.Item(
            {'uid': alfred.uid(i),
             'arg': path,
             'valid': 'no',
             'autocomplete': folder + u' ',
             # Hard to know what to do with smart folders.
             # Most 'file' functions don't work on them,
             # only 'Reveal in Finder' and that's about it.
             'type': 'file',
             'path': path
             },
            folder,
            u'',
            icon=('com.apple.finder.smart-folder',
                  {'type' : 'filetype'})
        )
        items.append(item)
    return items


def get_smart_folders():
    """Get list of all Smart Folders on system

    Returns:
        list of tuples (name, path)
    """
    results = []
    output = subprocess.check_output(['mdfind', 'kind:saved search']).decode('utf-8')
    paths = [path.strip() for path in output.split('\n') if path.strip()]
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        results.append((name, path))
    results.sort()
    return results


def search_folder(folder, query, limit=MAX_RESULTS):
    """Return list of items in `folder` matching `query`

    Returns:
        list of alfred.Item instances
    """
    # log.debug(u'folder : {!r} query : {!r}'.format(folder, query))
    results = []

    output = subprocess.check_output(['mdfind', '-s', folder]).decode('utf-8')
    files = [path.strip() for path in output.split('\n') if path.strip()]
    # log.debug(u'{} files in folder {}'.format(len(files), folder))
    for i, path in enumerate(files):
        name = os.path.basename(path)
        if query and not name.lower().startswith(query.lower()):
            continue

        item = alfred.Item(
                    {'uid': alfred.uid(u"%02d" % i),
                     'arg': path,
                     'valid': 'yes',
                     # 'autocomplete': path,
                     'type': 'file'},
                    name,
                    path,
                    icon=(path, {u'type' : u'fileicon'}))
        results.append(item)
        if len(results) == limit:
            break
    return results


def search_folders(query=None):
    """Search folder names/contents of folders

    Returns:
        list of alfred.Item instances
    """
    folders = get_smart_folders()
    results = []
    if query is None:
        results = make_folder_items(folders)
    else:
        query = query.lower()
        for (name, path) in folders:
            if query == name.lower():  # Exact match; show folder contents
                results = search_folder(name, u'')
                break
            elif query.startswith(name.lower()):  # search in folder
                query = query[len(name):].strip()
                results = search_folder(name, query)
                break
        if not results:  # found no matching folder; filter folders
            results = make_folder_items([t for t in folders if
                                        t[0].lower().startswith(query)])
    return results


def main():
    args = docopt(__usage__, alfred.args())
    # log.debug(u'args : {}'.format(args))
    if args.get(u'--helpfile'):
        open_help_file()
        return 0
    query = args.get(u'<query>')
    folder = args.get(u'--folder')
    results = []
    if folder is None:
        results = search_folders(query)
    else:
        if query is None:  # show list of contents of folder
            query = u''
        results = search_folder(folder, query)
    xml = alfred.xml(results, maxresults=MAX_RESULTS)
    # log.debug(u'Returning {} results to Alfred'.format(len(results)))
    # log.debug('\n{}'.format(xml))
    alfred.write(xml)
    return 0

if __name__ == '__main__':
    sys.exit(main())