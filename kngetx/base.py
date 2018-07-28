#!/usr/bin/env python
# coding: utf-8

import os
import re
import sys
import time
import copy
import random
import json
import shlex
import requests
from hashlib import sha1
from .inifile import IniFile
from .inifile import IniException
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

__all__ = [
    'main',
    'Knget',
    'KngetShell'
]

_NO_ERROR = 0
_CONFIG_ERROR = 1
_USAGE_ERROR = 2
_CONNECT_ERROR = 3
_DOWNLOAD_ERROR = 4

_USAGE = '''\
Usage: {0} <tags> <[begin]<end>>
'''.format(sys.argv[0])

# Ensure _PROMPT_STR is unicode
_PROMPT_STR = u'KGXSH> '

_CONFIG_TIPS = '''\
; KngetPy Project.
; File auto-generated by {0}
;
; Edit the base_url in the custom section
; to download different kind of images on site.
;
; Project links:
;   https://github.com/urain39/KngetPy
;   https://github.com/urain39/IniFilePy
;
'''.format(sys.argv[0])

_DEFAULT_CONFIG = {
    'custom': {
        'base_url': 'https://capi.sankakucomplex.com',
        'page_limit': 10,
        'user_agent': 'SCChannelApp/3.0 (Android; black)',
        'load_time_fake': '1-2',
        'post_rating': 'e q s',
        'post_min_score': 100,
        'post_tags_blacklist': 'video mp4 webm'
    },
    'download': {
        'timeout': 30,
        'maxsize': 10,
        'bufsize': 1048576,
        'retry_wait': 8,
        'retry_count': 3
    },
    'account': {
        'username': 'knget',
        'password': 'knget.py'
    }
}

class KngetError(Exception):
    '''KngetPy BaseException.
    '''
    pass


class Knget(object):
    def __init__(self, config):
        self._curdir = os.getcwd()
        self._custom = config.get_section('custom')
        self._config = config.get_section('download')
        self._account = config.get_section('account')
        self._session = requests.Session()
        self._login_data = dict()
        self._task_pool = dict()
        self._meta_infos = list()
        self._session.headers = {
                'Accept': '*/*',
                'Connection': 'Keep-Alive',
                'User-Agent': self._custom.get('user_agent'),
        }
        self._session.cookies = requests.cookies.cookielib.LWPCookieJar(self._curdir + '/cookies.txt')

        if os.path.exists(self._curdir + '/cookies.txt'):
            self._msg('Loading cookies.')
            self._session.cookies.load()

    def _load_faker(self):
        load_time_fake = [
            int(i) for i in (
                self._custom.get('load_time_fake') or '1-3'
            ).split('-')[:2]
        ]

        load_time = random.randint(*load_time_fake) + random.random()

        self._msg2("Load time: %0.2f" % load_time)
        time.sleep(load_time)

    def _login(self, username, password):
        for cookie_name in [cookie.name.lower() for cookie in self._session.cookies]:
            if 'sankaku' in cookie_name:
                self._msg('Logined, skip login.')
                return

        appkey = sha1(
            'sankakuapp_{0}_Z5NE9YASej'.format(
                str(username)
            ).encode()
        ).hexdigest()

        password_hash = sha1(
            'choujin-steiner--{0}--'.format(
                str(password)
            ).encode()
        ).hexdigest()

        self._login_data.update(
            {
                'login': username,
                'password_hash': password_hash,
                'appkey': appkey
            }
        )

        response = self._session.post(
            '{base_url}/user/authenticate.json'.format(
                base_url=self._custom.get('base_url')
            ),
            data={
                'user[name]': username,
                'user[password]': password,
                'appkey': appkey
            }
        )

        if not (response.ok and response.json().get('success')):
            raise KngetError('Cannot login!')

    def _msg(self, msg):
        sys.stderr.write('=> {0}\n'.format(msg))

    def _msg2(self, msg):
        sys.stderr.write('    => {0}\n'.format(msg))

    def _chdir(self, tags):
            save_dir = 'kn-' + '-'.join(
                tags.split()
            )

            # FIXME: Windows filename cannot with '< > / \ | : " * ?'

            if not os.path.exists(save_dir):
                if os.path.isfile(save_dir):
                    os.remove(save_dir)
                os.mkdir(save_dir)
            os.chdir(save_dir)

    def _check_url(self, url):
        protocol = re.match(r'((?:ht|f)tps?:).*', url)

        if protocol is None:
            # Get protocol from base_url
            base_url = self._custom.get('base_url')
            return re.match(r'((?:ht|f)tps?:).*', base_url).group(1) + url

        return url

    def _download(self, job):
        url =  job['file_url']
        file_size = job['file_size']
        file_name = '{post_id}.{file_ext}'.format(
            post_id=job['id'],
            # XXX: Some sites not have file_ext!
            file_ext=job['file_url'].split('.')[-1]
        )

        file_name = file_name.split('?')[0]

        response = self._session.get(
            url=self._check_url(url),
            stream=True,
            timeout=self._config.get('timeout') or 10,
            params=self._login_data
        )

        self._load_faker()
        if ( not os.path.exists(file_name) or
                os.path.getsize(file_name) != file_size ):
            with open(file_name, 'wb') as fp:
                bufsize = self._config.get('bufsize') or (1<<20)

                for data in response.iter_content(chunk_size=bufsize):
                    fp.write(data)

    def _cleanup(self):
        if not len(self._meta_infos) < 1:
            with open('meta_data.json', 'w') as fp:
                json.dump(self._meta_infos, fp)

        os.chdir(self._curdir)
        for _dir in os.listdir(self._curdir):
            if os.path.isdir(_dir) and len(os.listdir(_dir)) < 1:
                os.rmdir(_dir)
                self._msg2('save_dir {0} is empty, removed.'.format(_dir))

    def _filter(self):
        post_rating = self._custom.get('post_rating')
        post_min_score = self._custom.get('post_min_score')
        post_tags_blacklist = self._custom.get('post_tags_blacklist')

        if post_rating != r'' and post_rating != None:
            self._task_pool = [
                task
                for task in self._task_pool
                    if task.get('rating') in post_rating.split()
            ]

        if post_min_score != r'' and post_min_score != None:
            self._task_pool = [
                task
                for task in self._task_pool
                    if int(task.get('score') or
                        task.get('total_score') or 0) >= post_min_score
            ]

        if post_tags_blacklist != r'' and post_tags_blacklist != None:
            self._task_pool = [
                task
                for task in self._task_pool
                    if all( tag['name'] not in post_tags_blacklist.split()
                            for tag in task['tags'] )
            ]

    def work(self):
        self._filter()

        jobs_count = len(self._task_pool)
        retry_count = self._config.get('retry_count')
        retry_wait = self._config.get('retry_wait')

        cur_jobs_count = 0
        cur_retry_count = 0

        self._meta_infos.extend(self._task_pool)

        for job in self._task_pool:
            file_size = job.get('file_size')

            if (file_size or 0) < self._config.get('maxsize') * (1<<20):
                cur_jobs_count += 1
                cur_retry_count = 0

                while True:
                    try:
                        self._msg2( 'Process: %4d / %-4d' %
                                    (cur_jobs_count, jobs_count) )

                        self._download(job)
                        break
                    except requests.exceptions.RequestException as e:
                        if cur_retry_count < retry_count:
                            self._msg2('Error: {0}'.format(e))
                            self._msg2('wait {0}s...'.format(retry_wait))
                            time.sleep(retry_wait)
                            cur_retry_count += 1
                            continue
                        else:
                            self._cleanup()
                            sys.exit(_DOWNLOAD_ERROR)

    def run(self, tags, begin, end):
        self._chdir(tags)

        for page in range(begin, end + 1):
            self._load_faker()
            self._msg('[Page = {0} | tags = {1}]'.format(page, tags))

            payload = {
                    'page': page,
                    'tags': tags,
                    'limit': self._custom.get('page_limit')
            }

            # Add credential
            payload.update(self._login_data)

            # Get index data.
            try:
                response = self._session.get(
                    self._custom.get('base_url') + '/post/index.json',
                    timeout=self._config.get('timeout'),
                    params=payload )

                self._task_pool = response.json()

                if not isinstance(self._task_pool, list):
                    self._msg2('Error: response is not a list!')
                    self._msg2('Debug: {0}'.format(self._task_pool))
                    self._msg2('Debug: {0}'.format(self._session.cookies))
                    self._msg2('Breaking...')
                    break
            except (requests.exceptions.RequestException, ValueError) as e:
                self._msg2('Error: {0}'.format(e))
                self._msg2('Quitting...')
                break

            # Do the job from index data.
            if len(self._task_pool) < 1:
                break
            elif len(self._task_pool) < self._custom.get('page_limit'):
                self.work()
                break
            else:
                self.work()
        self._cleanup()
        self._session.cookies.save()


class KngetShell(Knget):
    '''KngetPy Extended Class for REPL.
    '''

    def __init__(self, config):
        self._commands = {}
        super(self.__class__, self).__init__(config)

        # cmd_name, implement, args_count, help_msg
        self.cmd_register('run', self.run, 3, 'run <tags> <begin> <end>')
        self.cmd_register('help', self.help, 0, 'show this help again')
        self.cmd_register('reload', self.reload, 0, 'reload config')
        self.cmd_register('exit', self.exit, 0, 'exit this session')
        self.cmd_register('login', self.login, 0, 'login your account')
        self.cmd_register('debug', self.debug, 0, 'show debug messages')
        self.cmd_register('runcmd', self.runcmd, 1, 'run terminal command')
        self.cmd_register('setprop', self.setprop, 2, 'setprop <propkey> <value>')

    def run(self, tags, begin, end):
        ''' Override method of Class Knget
        '''
        return super(self.__class__, self).run(tags, int(begin), int(end))

        self.__init__(config)

    def exit(self):
        sys.exit(_NO_ERROR)

    def login(self):
        self._login(**self._account)

    def runcmd(self, cmd_name):
        os.chdir(self._curdir)
        os.system(cmd_name)

    def reload(self, config=None):
        config = config or load_config()
        self._custom = config.get_section('custom')
        self._config = config.get_section('download')
        self._session.headers = {
                'Accept': '*/*',
                'Connection': 'Keep-Alive',
                'User-Agent': self._custom.get('user_agent'),
        }

    def debug(self):
        self._msg('DEBUG')
        self._msg2('WorkDir: {0}'.format(self._curdir))
        self._msg2('Logined: {0}'.format(self._login_data))
        self._msg2('Cookies: {0}'.format(self._session.cookies))
        self._msg2('Headers: {0}'.format(self._session.headers))
        self._msg2('Configs: {0}'.format(self._config))

    def setprop(self, propkey, value):
        _config = {
            'custom': self._custom,
            'download': self._config,
            'account': self._account
        }
        propkey = propkey.split('.')

        if len(propkey) == 2:
            section, key = propkey
            
            if not (section in _config.keys() and
                     key in _config[section].keys()):
                return

            _config[section][key] = value

            config = IniFile()
            config.reset(_config)
            self.reload(config)

    def cmd_register(self, cmd_name, callback, args_count=0, help_msg=None):
        ''' cmd_register: register a implemented method or function as a command
            :param: cmd_name, command name
            :param: callback, a implemented method or function
            :param: args_count, args count without self
            :param: help_msg, a short message of help for this command 
        '''
        # Pack
        self._commands[cmd_name] = (callback, args_count, help_msg or '')

    def help(self):
        print('Copyright (c) 2017-2018 urain39@cyfan.cf\n')
        print('Registered commands:')

        for cmd_name, cmd_itself in self._commands.items():
            _, _, help_msg = cmd_itself
            print(' ' * 4 + '{0:10s}{1}'.format(cmd_name, help_msg))

    def execute(self, lineno, cmd_name, args):
        if not cmd_name in self._commands.keys():
            self._msg2('#%d: Not found command %s\n' % (lineno, cmd_name))
            return self.help()
        else:
            # Unpack
            callback, args_count, help_msg = self._commands[cmd_name]

            # Check args count
            if len(args) != args_count:
                return self.help()

            # Matched!
            try:
                callback(*args)
            except (ValueError, OSError) as e:
                self._msg2('Error: {0}'.format(e))
                self._msg2('Usage: {0}'.format(help_msg))
 
    def session(self):
        lineno = 0

        if not sys.stdin.isatty():
            # Get stdin from a pipe.
            while True:
                line = sys.stdin.read()
                lineno += 1

                if len(line) < 1:
                    break # EOF
                line = shlex.split(line)

                if len(line) < 1:
                    continue # Blank
                self.execute(lineno, cmd_name=line[0], args=line[1:])
        else:
            _session = PromptSession(message=_PROMPT_STR,
                                     history=FileHistory(self._curdir + '/history.txt'))
            while True:
                line = _session.prompt()
                line = shlex.split(line)
                lineno += 1

                if len(line) < 1:
                    continue # Blank
                self.execute(lineno, cmd_name=line[0], args=line[1:])


def usage(status=None):
    print(_USAGE)

    if status is Non:
        return
    else:
        sys.exit(status)

def load_config():
    config_path = 'configx.ini'

    if os.name == 'posix':
        config_path = os.getenv('HOME') + '/kngetx.ini'
    elif os.name == 'nt':
        config_path = os.getenv('HOMEPATH') + '/kngetx.ini'

    if os.path.exists(config_path):
        try:
            config = IniFile(config_path)
        except IniException as e:
            print('{0}\n'.format(e))
            print('Possible config syntax error?')
            sys.exit(_CONFIG_ERROR)
    else:
        with open(config_path, 'w') as fp:
            config = IniFile()
            config.reset(_DEFAULT_CONFIG)
            fp.write(_CONFIG_TIPS + '\n')
            config.dump(fp)

    return config

def main(argv):
    config = load_config()

    if len(argv) < 3:
        KngetShell(config).session()
    elif len(argv) == 3:
        Knget(config).run(argv[1], 1 ,int(argv[2]))
    elif len(argv) == 4:
        Knget(config).run(argv[1], int(argv[2]), int(argv[3]))
    else:
        return usage(_USAGE_ERROR)

if __name__ == '__main__':
    try:
        main(sys.argv)
    except (KeyboardInterrupt, EOFError):
        sys.exit(_NO_ERROR)
