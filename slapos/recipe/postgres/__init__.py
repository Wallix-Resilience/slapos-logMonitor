##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import md5
import os
import sys
import subprocess
import textwrap
from zc.buildout import UserError

from slapos.recipe.librecipe import GenericBaseRecipe
from slapos.recipe.librecipe import filehash


class Recipe(GenericBaseRecipe):

    def _options(self, options):
        options['password'] = self.generatePassword()
        options['url'] = 'postgresql://%(user)s:%(password)s@[%(host)s]:%(port)s/%(dbname)s' % dict(options, host=options['ipv6_host'].pop())


    def install(self):
        pgdata = self.options['pgdata-directory']

        if not os.path.exists(pgdata):
            self.createCluster()
            self.createConfig()
            self.createDatabase()
            self.createSuperuser()
            self.createRunScript()

        return [
                # XXX what to return here?
                # os.path.join(pgdata, 'postgresql.conf')
                ]


    def createCluster(self):
        initdb_binary = os.path.join(self.options['bin'], 'initdb')

        pgdata = self.options['pgdata-directory']

        try:
            subprocess.check_call([initdb_binary,
                                   '-D', pgdata,
                                   '-A', 'ident',
                                   '-E', 'UTF8',
                                   ])
        except subprocess.CalledProcessError:
            raise UserError('Could not create cluster directory in %s' % pgdata)


    def createConfig(self):
        pgdata = self.options['pgdata-directory']

        with open(os.path.join(pgdata, 'postgresql.conf'), 'wb') as cfg:
            # XXX TODO listen_addresses
            cfg.write(textwrap.dedent("""\
                    logging_collector = on
                    log_rotation_size = 50MB
                    max_connections = 100
                    datestyle = 'iso, mdy'

                    lc_messages = 'en_US.UTF-8'
                    lc_monetary = 'en_US.UTF-8'
                    lc_numeric = 'en_US.UTF-8'
                    lc_time = 'en_US.UTF-8'
                    default_text_search_config = 'pg_catalog.english'
                    """))


        with open(os.path.join(pgdata, 'pg_hba.conf'), 'wb') as cfg:
            # see http://www.postgresql.org/docs/9.1/static/auth-pg-hba-conf.html

            cfg.write(textwrap.dedent("""\
                    # TYPE  DATABASE        USER            ADDRESS                 METHOD

                    # "local" is for Unix domain socket connections only
                    local   all             all                                     ident
                    host    all             all             127.0.0.1/32            md5
                    host    all             all             ::1/128                 md5
                    """))


    def createDatabase(self):
        self.runPostgresCommand(cmd='CREATE DATABASE "%s"' % self.options['dbname'])


    def createSuperuser(self):
        """
        Creates a Postgres superuser - other than "slapuser#" for use by the application.
        """
        password = 'insecure'
        enc_password = md5.md5(password).hexdigest()
        self.runPostgresCommand(cmd="""CREATE USER "%s" PASSWORD '%s' SUPERUSER""" % (self.options['user'], enc_password))


    def runPostgresCommand(self, cmd):
        """
        Executes a command in single-user mode, with no daemon running.

        Multiple commands can be executed by providing newlines,
        preceeded by backslash, between them.
        See http://www.postgresql.org/docs/9.1/static/app-postgres.html
        """

        pgdata = self.options['pgdata-directory']
        postgres_binary = os.path.join(self.options['bin'], 'postgres')

        try:
            p = subprocess.Popen([postgres_binary,
                                  '--single',
                                  '-D', pgdata,
                                  'postgres',
                                  ], stdin=subprocess.PIPE)

            p.communicate(cmd+'\n')
        except subprocess.CalledProcessError:
            raise UserError('Could not create database %s' % pgdata)


    def createRunScript(self):
        """
        Creates a script that runs postgres in the foreground.
        'exec' is used to allow easy control by supervisor.
        """
        content = textwrap.dedent("""\
                #!/bin/sh
                exec %(bin)s/postgres \\
                    -D %(pgdata-directory)s
                """ % self.options)
        name = os.path.join(self.options['services'], 'postgres-start')
        self.createExecutable(name, content=content)


