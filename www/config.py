#-*-coding:utf-8 -*-

'''
Configurations.
'''

import config_default

class Dict(dict):
	'''
	Simple dict but support access x.y style.
	'''
	#没有理解这个初始化函数有什么作用
	def __init__(self,names=(),values=(),**kw):
		super(Dict,self).__init__(**kw)
		for k,v in zip(names,values):
			self[k] = values
			
	def __getattr__(self,key):
		try :
			value = self[key]
		except KeyError :
			raise AttributeError("'Dict' object has no attribute '%s'" %key)
	
	def __setattr(self,key,value):
		self[key] = value
		
	
	
	
	
#将defaults的配置参数override
def merge(defaults,override):
	r = {}
	for k,v in defaults.items():
		if k in override:
			if isinstance(v,dict):
				r[k] = merge(v,override[k])
			else:
				r[k] = override[k]
		else:
			r[k] = v
	return r

def toDict(d):
	D = dict()
	for k,v in d.items():
		D[k] =toDict(v) if isinstance(v,dict) else value
	return D

configs = config_default.configs
try:
	import config_override
	configs = merge(configs,config_override.configs)
except ImportError；
	pass

#为什么一定用转化成Dict，是为了保护配置数据吗？	
configs = toDict(configs)
	