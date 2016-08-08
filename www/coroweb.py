#-*- coding:utf-8 -*-

import asyncio,inspect,functools
import importlib
from aiohttp import web
import logging
from errors import APIError

def get(path):
	'''
	Define decorator @get('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args,**kw):
			return func(*args,**kw)
		wrapper.__method__='GET'
		wrapper.__route__=path
		return wrapper
	return decorator
	
def post(path):
	'''
	Define decorator @post('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args,**kw):
			return func(*args,**kw)
		wrapper.__method__='POST'
		wrapper.__route__=path
		return wrapper
	return decorator
	
def get_required_kw_args(fn):
	args=[]
	#这里返回的是mappingproxy对象，是一个ordered mapping，
	#里面存储的是parameter的name与对应的Parameter对象
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY:
			args.append(name)
	return tuple(args)
	
	
class RequestHandler(object):
	
	def __init__(self,func):
		self._func = func
		
	async def __call__(self,request):
		
		#获取函数的参数
		required_args = inspect.signature(self._func).parameters
		logging.info('required args:%s' %required_args)
		
		#获取冲GET或POST传进来的参数值，如果函数表里面有这参数名就加入
		kw = {arg:value for arg,value in request.__data__.items() if arg in required_args}
		#logging.info('now kw is:%s' %kw)
		#获取match_info的参数值，例如@get('/blog/{id}')之类的参数值
		kw.update(dict(**request.match_info))
		#logging.info('now kw is:%s' %kw)
		#如果有request就加入
		if 'request' in required_args:
			kw['request']=request
		#logging.info('now kw is:%s' %kw)	
		#检查参数
		for key,arg in required_args.items():
			#request不能是var参数类型（*request or **request）
			if key=='request' and arg.kind  in (inspect.Parameter.VAR_POSITIONAL,inspect.Parameter.VAR_KEYWORD):
				return web.HTTPBadRequest(text='request parameter can not be he var argument.')
			#确保url函数调用时有足够多的参数值（不然会报调用时缺少参数赋值）
			if arg.kind not in (arg.VAR_KEYWORD,arg.VAR_POSITIONAL):
				
				if arg.default == arg.empty and arg.name not in kw:
					return web.HTTPBadRequest(text='Missing argument: %s' %arg.name)
		
		logging.info('call with args: %s' %kw)
		try:
			return await self._func(**kw)
		except APIError as e:
			return dict(error=e.error,data=e.data,message=e.message)

#添加一个route
def add_route(app,fn):
	method = getattr(fn,'__method__',None)
	path = getattr(fn,'__route__',None)
#	print(method,path)
	if (path is None) or (method is None):
		raise ValueError('@get or @post not defined in %s.' %str(fn))
	
	fn=asyncio.coroutine(fn)
	logging.info('add route %s %s => %s(%s)'%(method,path,fn.__name__,''.join(inspect.signature(fn).parameters.keys())))
	app.router.add_route(method,path,RequestHandler(fn))

#添加一个模块所有的route
def add_routes(app,module_name):
	#动态导入模块
	mod=importlib.import_module(module_name)
#	mod=__import__(module_name,fromlist=['get_submodule'])
	for attr in dir(mod):   
		if attr.startswith('_'):
			continue
		fn=getattr(mod,attr)
		if callable(fn):
			method = getattr(fn,'__method__',None)
			path = getattr(fn,'__route__',None)
			if path and method:
				add_route(app,fn)
			
#添加静态文件，未完成
def add_static(app):
	pass