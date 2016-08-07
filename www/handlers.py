#-*- coding:utf-8 -*-

from coroweb import get,post
from aiohttp import web

@get('/register')
def register():
	return b'ok'

if __name__=='__main__':
	print(register.__route__)
	print(register.__method__)