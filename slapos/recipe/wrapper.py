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

import shlex

from slapos.recipe.librecipe import GenericBaseRecipe

class Recipe(GenericBaseRecipe):

    def install(self):

        command_line = shlex.split(self.options['command-line'])

        wait_files = self.options.get('wait-for-files')
        if wait_files is not None:
            wait_files = [filename.strip() for filename in wait_files.split()
                          if filename.strip()]

        environment = self.options.get('environment')
        if environment is not None:
            environment = dict((k.strip(), v.strip()) for k, v in [
                             line.split('=')
                             for line in environment.split('\n')
                           ])

        return [self.createPythonScript(
            self.options['output'],
            'slapos.recipe.librecipe.execute.generic_exec',
            (command_line, wait_files, environment,),
        )]
