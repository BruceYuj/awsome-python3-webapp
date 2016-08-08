#-*- coding:utf-8 -*-

__author__='BruceYuj'

import logging;logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime

from aiohttp import web
from urllib import parse
from jinja2 import Environment,FileSystemLoader

import orm
from coroweb import add_routes,add_static

#工厂函数
#在每个响应之前打印日志
async def logger_factory(app,handler):
	async def logger(request):
		logging.info('Response:%s %s' %(request.method,request.path))
		return await handler(request)
	return logger

#通过cookie找到当前用户信息，把用户绑定在request.__user__
#该方法还在测试
async def auth_factory(app,handler):
		async def auth(request):
			logging.info('check user:%s %s'%(request.method,request.path))
			cookie = request.cookies.get(COOKIE_NAME)
			reuqest.__user__ = await User.fin_by_cookie(cookie)
			if request.__user__ is not None:
				loggin.info('set current user:%s' %request.__user__.email)
			return await handler(request)
		return auth
		
#处理request中的一些参数和数据（用户传过来的）		
async def data_factory(app,handler):
	async def parse_data(request):
		logging.info('data_factory...')
		#如果method是'POST'，通常数据再body中，分为json类型和form类型
		if request.method == 'POST':
			if not request.content_type:
				return web.HTTPBadRequest(text='Missing Content-Type.')
			content_type = request.content_type.lower()
			if content_type.startswith('application/json'):
				request.__data__=await request.json()
				if not isinstance(request.__data__,dict):
					return web.HTTPBadRequest(text='JSON body must be object.')
				logging.info('request json: %s'%request.__data__)
			elif content_type.startswith(('application/x-www-form-urlencoded','multipart/form-data')):
				params = await request.post()
				request.__data__ = dict(**params)
				logging.info('request form: %s'%request.__data__)
			else:
				return web.HTTPBadRequest(text='Unsupported Content-Type:%s'%content_type)
		elif request.method == 'GET':   #如果是GET，可能参数在url中
			qs = request.query_string
			#需要测试parse.parse_qs返回的值，为什么是v[0]？可能返回的是{a:[values]}
			request.__data__ = {k:v[0] for k,v in parse.parse_qs(qs,True).items()}
			logging.info('request query:%s'%request.__data__)
		else:
			request.__data__ = dict()
		return await handler(request)
		
	return parse_data

#把任何返回值封装成aiohttp支持的Response对象
async def response_factory(app,handler):
	async def response(request):
		logging.info('response handler...')
		r = await handler(request)
		if isinstance(r,web.StreamResponse):
			return r
		if isinstance(r,bytes):
			resp = web.Response(body=r)
			resp.content_type = 'application/octet-stream'
			return resp
		if isinstance(r,str):
			if r.startswith('redirect:'):
				return web.HTTPFound(r[9:])
			resp = web.Response(body=r.encode('utf-8'))
			resp.content_type = 'text/html;charset=utf-8'
			return resp
		if isinstance(r,dict):
			template = r.get('__template__')
			if template is None:
				resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
				resp.content_type = 'application/json;charset=utf-8'
				return resp
			else:
			#如果用jinja2渲染，绑定已验证过的用户
			#	r['__user__'] = request.__user__
				resp = web.Response(body=app['__template__'].get_template(template).render(**r).encode('utf-8'))
				resp.content_type = 'text/html;charset=utf-8'
				return resp
		if isinstance(r,int) and 100 <=r < 600:
			return web.Response(status=r)
		if isinstance(r,tuple) and len(r) == 2:
			status,message = r
			if isinstance(status,int) and 100<= status <600:
				return web.Response(status=status,text=str(message))
		
		#default
		resp = web.Response(body=str(r).encode('utf-8'))
		resp.content_type = 'text/plain;charset = utf-8'
		return resp
		
	return response
	
#jinja2初始化函数
def init_jinja2(app,**kw):
	logging.info('init jinja2...')
	options = dict(
		autoescape = kw.get('autoescape',True),
		block_start_string = kw.get('block_start_string','{%'),
		block_end_string = kw.get('block_end_string','%}'),
		variable_end_string = kw.get('variable_end_string','}}'),
		variable_start_string = kw.get('variable_start_string','{{'),
		auto_reload = kw.get('auto_reload',True)
	)
	path = kw.get('path',None)
	if path is None:
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
	logging.info('set jinja2 template path: %s' %path)
	env =Environment(loader=FileSystemLoader(path),**options)
	filters = kw.get('filters',None)
	if filters is not None:
		for name,f in filters.items():
			env.filters[name] = f
	app['__template__'] = env

def datetime_filter(t):
	delta = int(time.time()-t)
	if delta < 60:
		return u'1分钟前'
	if delta < 3600:
		return u'%s分钟前' %(delta // 60)
	if delta < 86400:
		return u'%s小时前' %(delta // 3600)	
	if delta < 604800:
		return u'%s天前' %(delta // 86400)
	dt = datetime.fromtimestamp(t)
	return u'%s年%s月%s日' %(dt.year,dt.month,dt.day)
	
	
	
async def init(loop):
	await orm.create_pool(loop=loop, host='127.0.0.1', port=3306,user='root',password='admin',db='awesome')
	
	app=web.Application(loop=loop,middlewares=[logger_factory,data_factory,response_factory])
	init_jinja2(app,filters=dict(datetime=datetime_filter))
	#	app.router.add_route('GET','/',index)
	add_routes(app,'handlers')
	add_static(app)
	srv=await loop.create_server(app.make_handler(),'127.0.0.1',9000)
	logging.info('server started at http://127.0.0.1:9000...')
	return srv
	
loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
