#-*- coding:utf-8 -*-

from coroweb import get,post
from aiohttp import web
from models import User, next_id


@get('/')
async def index(request):
	users = await User.findAll()
	return {
		'__template__':'test.html',
		'users': users
	}

@get('/register')
def register():
	return web.Response(b'ok')

if __name__=='__main__':
	print(register.__route__)
	print(register.__method__)