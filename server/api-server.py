#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

import zmq

import cherrypy

"""
It is highly recommend to use this api server behind a proxy with ssl
"""

USER = 'user'
PASSWORD = '4321'
INTERFACE = '127.0.0.1'
PORT = 8888

ZMQ_ADDRESS = '127.0.0.1'
ZMQ_PORT = 5555
REQUEST_TIMEOUT = 1000
DRAW_TEXT_NODE = 'Parsed_drawtext_2'


def send_zmq(data):
    context = zmq.Context(1)
    client = context.socket(zmq.REQ)
    print("Connecting to server…")
    client.connect('tcp://{}:{}'.format(ZMQ_ADDRESS, ZMQ_PORT))

    poll = zmq.Poller()
    poll.register(client, zmq.POLLIN)

    request = ''
    reply_msg = ''

    for key, value in data.items():
        request += "{}='{}':".format(key, value)

    request = "{} reinit {}".format(DRAW_TEXT_NODE, request.rstrip(':'))

    print('Sending "{}"'.format(request))
    client.send_string(request)

    socks = dict(poll.poll(REQUEST_TIMEOUT))

    if socks.get(client) == zmq.POLLIN:
        reply = client.recv()

        if reply and reply.decode() == '0 Success':
            print('Server replied OK ({})'.format(reply.decode()))
            reply_msg = reply.decode()
        else:
            print('Malformed reply from server: {}'.format(reply.decode()))
            reply_msg = reply.decode()
    else:
        reply_msg = 'No response from server'
        print(reply_msg)

    client.setsockopt(zmq.LINGER, 0)
    client.close()
    poll.unregister(client)

    context.term()
    return {'Success': reply_msg}


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
    cherrypy.config.update({'environment': 'production',
                            # 'log.error_file': 'site.log',
                            'server.socket_host': INTERFACE,
                            'server.socket_port': PORT,
                            })

    cherrypy.quickstart(MessengerAPI(), '/', conf)
