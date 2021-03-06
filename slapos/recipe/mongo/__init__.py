import shutil
import os
import signal
from binascii import b2a_uu as uuencode
import pkg_resources
import socket
import sys
from slapos.recipe.librecipe import GenericBaseRecipe
from slapos.recipe.librecipe import BaseSlapRecipe



class BaseRecipe(GenericBaseRecipe):

  def config(self):
    path_list = [] 

    mongo_arg = dict(
      ip = self.options['ip'],
      port = self.options['port'],
      datadir = self.options['mongo-data']
    )

    mongo_conf = self.createFile(self.options['mongo-conf'],
      self.substituteTemplate(self.getTemplateFilename('mongodb.in'),
                              mongo_arg)
    )
    return mongo_conf


#the interaction between users and the cluster
#its job is to hide all of the internals of sharding and present
#a clean, single-server interface to the user
class Mongos(BaseRecipe):

  def install(self):
    path_list = []

    mongod_servers = ",".join((self.options['servers']).split()) # MongoConf servers
    
    wrapper = self.createPythonScript( os.path.join( self.options['path'], "mongos"),
                                      'slapos.recipe.librecipe.execute.execute',
      [
      os.path.join(self.options['mongo-path'],'mongos'),'--configdb', mongod_servers, '--ipv6', '--rest', '--bind_ip', self.options['ip'],'--port', self.options['port']
      ]
    )

    path_list.append(wrapper)

    return path_list


class MongoSzk(BaseRecipe):

  def install(self):
    #print "szerveres", self.options['servers']
    self.checkListening(self.options['servers'])
    path_list = []
    mongo_arg = dict(
      ip = self.options['ip'],
      port = self.options['port'],
      configdb = ",".join((self.options['servers']).split())
    )

    mongo_conf = self.createFile(self.options['mongo-conf'],
      self.substituteTemplate(self.getTemplateFilename('mongos.in'),
                              mongo_arg)
    )

    path_list.append(mongo_conf)

    bootstrap = self.options['bootstrap']
    zk = '-z %s' % self.options['zookeeper']
    conf = '-c %s' % self.options['mongo-conf']
    ip = '-i %s' % self.options['ip']
    port = '-p %s' % self.options['port']
    mongo = '-b %s' % os.path.join(self.options['mongo-path'],'mongos')

    wrapper = self.createPythonScript(os.path.join(self.options['path'], 'mongos'),
                                      'slapos.recipe.librecipe.execute.execute',
      [
       bootstrap, zk, mongo, ip, port, conf
      ]
    )

    path_list.append(wrapper)

    wrapper2 = self.addShards()
    if wrapper2 :
      path_list.append(wrapper2)

    return path_list
  
  def addShards(self):
    wrapper2 = None
    try:
        shards = self.options['shards']
        arguments2 = [
          self.options['mongo-shard-add-bin'], '-s',  shards, '-i',"[%s]" %  self.options['ip'], '-p', self.options['port']
          ]
        wrapper2 = self.createPythonScript( os.path.join(self.options['path'], 'mongosaddshard'),'slapos.recipe.librecipe.execute.execute', arguments2)
    
    except Exception, e:
        print "shards not defined", e
    return wrapper2

  def checkListening(self, hosts):
    print "hosts : ", hosts
    hostslist = hosts.split()
    hostname = None
    port = None
    try:
      for host in hostslist:
        hostname, sep, port = host.rpartition(':')
        s = socket.create_connection((hostname, port))
        s.close()
    except (socket.error, socket.timeout):
      sys.stderr.write("isn't listening\n" )
      sys.exit(127)


class Mongo(BaseRecipe):
  
  def install(self):
    path_list = []
    wrapper1 = None
    wrapper2 = None
    arguments1 = None
    arguments2 = None

    mongo_conf = self.config()
    path_list.append(mongo_conf)
    
    arguments1 = [
      os.path.join(self.options['mongo-path'],'mongod'),'--rest','--config', self.options['mongo-conf']
      ]
    
    try:
      repsetname = self.options['repset']
      arguments1.append('--replSet')
      arguments1.append(repsetname)    
      try:
        servers = self.options['servers']
        arguments2 = [
          self.options['mongo-shard-init-bin'], '-s', repsetname, '-n', servers, '-i',"[%s]" %  self.options['ip'], '-p', self.options['port']
          #self.options['mongo-shard-init-bin'], '-s', repsetname, '-n', servers
          ]
        print "arguments2", arguments2

      except:
        print "servers not defined"

    except:
      print "repset not defined"
    wrapper1 = self.createPythonScript( os.path.join(self.options['path'],'mongo1'),'slapos.recipe.librecipe.execute.execute', arguments1)
    path_list.append(wrapper1)
    if arguments2:
      wrapper2 = self.createPythonScript( os.path.join(self.options['path'], 'mongo2'),'slapos.recipe.librecipe.execute.execute', arguments2)
      path_list.append(wrapper2)    
    print "path_list", path_list
    return path_list

class Mongozk(BaseRecipe):
  
  def install(self):
    path_list = []
    mongo_conf = self.config()
    path_list.append(mongo_conf)
    
    bootstrap = self.options['bootstrap']
    zk = '-z %s' % self.options['zookeeper']
    conf = '-c %s' % self.options['mongo-conf']
    ip = '-i %s' % self.options['ip']
    port = '-p %s' % self.options['port']
    mongo = '-b %s' % os.path.join(self.options['mongo-path'],'mongod')

    wrapper = self.createPythonScript(self.options['path'],
                                      'slapos.recipe.librecipe.execute.execute',
      [
       bootstrap, zk, mongo, ip, port, conf
      ]
    )

    path_list.append(wrapper)

    return path_list


#it hold the configuration of a cluster: shards, mongos process and system adminstrators
class MongoConfsrv(BaseRecipe):

  def install(self):
    path_list = []
    mongo_conf = self.config()
    path_list.append(mongo_conf)
    wrapper = self.createPythonScript( os.path.join(self.options['path'], 'mongoCFG'),
                                   'slapos.recipe.librecipe.execute.execute',
        [
        os.path.join(self.options['mongo-path'],'mongod'),'--configsvr', '--rest', '--config',self.options['mongo-conf']
        ]
    )

    path_list.append(wrapper)

    return path_list



