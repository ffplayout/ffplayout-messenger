#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

import cherrypy
import zmq

"""
It is highly recommend to use this api server behind a proxy with ssl
"""

USER = 'user'
PASSWORD = '4321'
INTERFACE = '127.0.0.1'
PORT = 8888

ZMQ_ADDRESS = '127.0.0.1'
ZMQ_PORT = 5555


def send_zmq(data):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect('tcp://{}:{}'.format(ZMQ_ADDRESS, ZMQ_PORT))
    filter_str = ''

    for key, value in data.items():
        filter_str += "{}='{}':".format(key, value)

    socket.send_string(
        "Parsed_drawtext_2 reinit " + filter_str.rstrip(':'))

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    if poller.poll(1000):
        print('got message ', socket.recv(zmq.NOBLOCK))
    else:
        print('error: message timeout')

    message = socket.recv()

    socket.close()
    context.term()
    return {'Success': message.decode()}


def enable_crossdomain():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
    cherrypy.response.headers[
        "Access-Control-Allow-Methods"] = "POST"
    # generate allow headers for crossdomain.
    allow_headers = [
        "Cache-Control", "X-Proxy-Authorization",
        "X-Requested-With", "Content-Type"]
    cherrypy.response.headers[
        "Access-Control-Allow-Headers"] = ','.join(allow_headers)


@cherrypy.expose
@cherrypy.tools.json_out()
@cherrypy.tools.json_in()
class MessengerAPI(object):

    def GET(self):
        enable_crossdomain()
        raise cherrypy.HTTPError(405, 'Not allowed.')

    def POST(self):
        enable_crossdomain()
        request = cherrypy.request.json

        if 'user' in request and 'password' in request and \
                request['user'] == USER and request['password'] == PASSWORD:

            if 'data' in request:
                msg = send_zmq(request['data'])
                return json.dumps(msg)
            else:
                msg = {'Success': False}
                return json.dumps(msg)
        else:
            msg = {'Success': False}
            return json.dumps(msg)

    def PUT(self):
        enable_crossdomain()
        raise cherrypy.HTTPError(405, 'Not allowed.')

    def DELETE(self):
        enable_crossdomain()
        raise cherrypy.HTTPError(405, 'Not allowed.')


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'response.headers.server': '',
            'tools.response_headers.headers': [('Content-Type',
                                                'application/json')],
        }
    }
    cherrypy.__version__ = ''
    cherrypy.config.update({  # 'environment': 'production',
                            # 'log.error_file': 'site.log',
                            'server.socket_host': INTERFACE,
                            'server.socket_port': PORT,
                            })

    cherrypy.quickstart(MessengerAPI(), '/', conf)
