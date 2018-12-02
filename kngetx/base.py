#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys
import json

from hashlib import sha1

from prompt_toolkit.shortcuts import message_dialog

from kngetx import __author__
from kngetx import __version__

from knget.base import Knget
from knget.base import KngetError
from knget.base import KngetShell
from knget.base import KngetCommand

__all__ = [
    'main',
    'KngetX',
    'KngetXError',
    'KngetXShell',
    'KngetXCommand'
]

_NO_ERROR = 0
_CONFIG_ERROR = 1
_USAGE_ERROR = 2
_CONNECT_ERROR = 3
_DOWNLOAD_ERROR = 4

_CMD = 'python -m kngetx'
_USAGE = '''Usage: {0} <tags> < <begin> [end] >
'''.format(sys.argv[0])

# Ensure _PROMPT_STR is unicode
_PROMPT_STR = u'KGXSH> '
_DEFAULT_CONFIG = {
    'custom': {
        'base_url': 'https://capi-beta.sankakucomplex.com',
        'page_limit': 10,
        'user_agent': 'Mozilla/5.0 (Linux; LittleKaiju)',
        'load_time_fake': '1, 2',  # <min, max>
        'post_rating': 's',  # At least one of 'e q s', split by space or tab.
        'post_min_score': 0,
        'post_tags_blacklist': 'video mp4 webm',
        'save_history': False,
        'history_path': 'history.txt',
        'save_cookies': False,
        'cookies_path': 'cookies.txt',
        'disable_dbgrun': True,  # It's not safety!
        # NO DOCS HERE, SO RTFS PLEASE! NOTE: `Knget._download`
        'filename_format': '{ordered_id:06d}_{file_id}.{file_ext}',
    },
    'download': {
        'timeout': 30,
        'maxsize': 10,
        'bufsize': 1048576,
        'retry_wait': 8,
        'retry_count': 3
    }
}


class KngetXError(KngetError):
    pass


class KngetX(Knget):
    """Extended class Knget for sankakucomplex.
    """

    # Please Keep it, Someone may need it.
    def load_config(self, config_path=None):
        # config = {}
        config_path = config_path or (self._homedir + '/kngetx.json')

        if os.path.exists(config_path):
            with open(config_path) as fp:
                config = json.load(fp)
        else:
            with open(config_path, 'w') as fp:
                config = _DEFAULT_CONFIG
                json.dump(config, fp, indent=2)

        self._custom = config.get('custom')
        self._config = config.get('download')

    def _chdir(self, tags):
        super(KngetX, self)._chdir(tags, prefix='kgx-')

    def _filter(self):
        post_rating = self._custom.get('post_rating')
        post_min_score = self._custom.get('post_min_score')
        post_tags_blacklist = self._custom.get('post_tags_blacklist')

        if post_rating != r'' and post_rating is not None:
            self._task_pool = [
                task for task in self._task_pool
                if task.get('rating') in post_rating.split()
            ]

        if post_min_score != r'' and post_min_score is not None:
            self._task_pool = [
                task for task in self._task_pool
                if int(task.get('score') or
                       task.get('total_score') or 0) >= post_min_score
            ]

        if post_tags_blacklist != r'' and post_tags_blacklist is not None:
            self._task_pool = [
                task for task in self._task_pool
                if all(tag['name'] not in post_tags_blacklist.split()
                       for tag in task['tags'])
            ]


class KngetXCommand(KngetCommand):
    """Extended class KngetCommand for sankakucomplex.
    """
    def __init__(self, command=None):
        super(KngetXCommand, self).__init__()

        if command:
            self._commands = command.commands
            self._commands.pop('login')
            self._commands.pop('autologin')

    @property
    def commands(self):
        return self._commands


class KngetXShell(KngetX, KngetShell):
    """Extended class KngetShell for sankakucomplex.
    NOTE: Do not let the `command` be a instance member(via `self.__init__()`)
        `command` is a decorator instance of `KngetShell` and `KngetXShell`,
        if `command` be a instance member, that you cannot decorate your methods!
    """

    command = KngetXCommand(KngetShell.command)

    @command.register(argtypes=r'M', help_msg="show version and exit.")
    def version(self):
        message_dialog(title=u"KngetX Version",
                       text=u"Author: {0}\nVersion: {1}".format(__author__, __version__))
        super(KngetXShell, self).version()  # Knget Version.

    def session(self, message=_PROMPT_STR):
        return super(KngetXShell, self).session(message=message)


def usage(status=None):
    print(_USAGE)

    if status is None:
        return
    else:
        sys.exit(status)


def main(argv):
    with KngetXShell() as kgxsh:
        if len(argv) < 2:
            kgxsh.session()
        elif len(argv) < 4:
            kgxsh.run(*argv)
        else:
            return usage(_USAGE_ERROR)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (KeyboardInterrupt, EOFError):
        sys.exit(_NO_ERROR)
