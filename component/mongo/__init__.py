import shutil
import os
import signal
from binascii import b2a_uu as uuencode
import pkg_resources


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
    mongo_conf = self.config()
    path_list.append(mongo_conf)

    mongod_servers = " ".join((self.options['servers']).split())
    
    wrapper = self.createPythonScript(self.options['path'],
                                      'slapos.recipe.librecipe.execute.execute',
      [
      os.path.join(self.options['mongo-path'],'mongos'),'--configdb', mongod_servers, '--rest','--ipv6','--config',self.options['mongo-conf']
      ]
    )

    path_list.append(wrapper)

    return path_list



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
      os.path.join(self.options['mongo-path'],'mongod'),'--rest','--ipv6','--config',self.options['mongo-conf']
      ]
    
    try:
      repsetname = self.options['repset']
      arguments1.append('--replSet')
      arguments1.append(repsetname)    
      try:
        servers = self.options['servers']

        arguments2 = [
          os.path.join(self.options['init-path'], '-s', repsetname, '-n', servers, '-i',self.options['ip'], '-p', self.options['port']
          ]
        print "arguments2", arguments2

      except:
        print "servers not defined"

    except:
      print "repset not defined"

    wrapper1 = self.createPythonScript( os.path.join(self.options['path'], 'mongo1'),'slapos.recipe.librecipe.execute.execute', arguments1)
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
    wrapper = self.createPythonScript(self.options['path'],
                                   'slapos.recipe.librecipe.execute.execute',
        [
        os.path.join(self.options['mongo-path'],'mongod'),'--configsvr','--ipv6','--config',self.options['mongo-conf']
        ]
    )

    path_list.append(wrapper)

    return path_list



