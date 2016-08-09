#-*- coding:utf-8 -*-

import time

from aiohttp import web

from coroweb import get,post
from models import User, next_id,Blog

@get('/blogs')
def blogs(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }
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