import shutil
import os
import signal
from binascii import b2a_uu as uuencode
import pkg_resources


from slapos.recipe.librecipe import GenericBaseRecipe
from slapos.recipe.librecipe import BaseSlapRecipe

import pkg_resources


class Producer(GenericBaseRecipe):
  def install(self):
    path_list = []
    
    ip = self.options['ip']
    port = self.options['port']
    zookeeper_addr = self.options['zookeeper-addr']
    producer_bin = self.options['producer-bin']
  
    wrapper = self.createPythonScript(self.options['path'],
                                      'slapos.recipe.librecipe.execute.execute',
                                      [ producer_bin,
                                        '-z', zookeeper_addr,
                                        '-a', ip, '-p', port ]
                                      )
    path_list.append(wrapper)
    return path_list


class Consumer(GenericBaseRecipe):

  def install(self):
    path_list = []

    zookeeper_addr = self.options['zookeeper']
    normalizer =  pkg_resources.resource_filename(__name__, "normalizers")
    consumer_bin = self.options['consumer-bin']
  
    wrapper = self.createPythonScript(self.options['path'],
                                      'slapos.recipe.librecipe.execute.execute',
                                      [consumer_bin,
                                       '-z', zookeeper_addr, 
                                       '-n', normalizer]
                                      )
    path_list.append(wrapper)
    return path_list

class Cli(GenericBaseRecipe):

  def install(self):
    path_list = []

    zookeeper_addr = self.options['zookeeper-addr']
    cli_bin = self.options['cli-bin']
    
    command = self.options['command']
    
    if command == "certificat":
      data = self.options['data']
      data = data.strip()
      cmd = '-c %s' % data
    
    if command == "key":
      data = self.options['data']
      data = data.strip()
      cmd = '-k %s' % data

    wrapper = self.createPythonScript(self.options['path'],
                                      'slapos.recipe.librecipe.execute.execute',
                                      [cli_bin,
                                       '-s', zookeeper_addr, 
                                       cmd                                       
                                       ]
                                      )
    path_list.append(wrapper)
    return path_list
