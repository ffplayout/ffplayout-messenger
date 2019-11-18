#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

import cherrypy


def enable_crossdomain():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
    cherrypy.response.headers[
        "Access-Control-Allow-Methods"] = "GET, POST, HEAD, PUT, DELETE"
    # generate allow headers for crossdomain.
    allow_headers = [
        "Cache-Control", "X-Proxy-Authorization",
        "X-Requested-With", "Content-Type"]
    cherrypy.response.headers[
        "Access-Control-Allow-Headers"] = ",".join(allow_headers)


@cherrypy.expose
@cherrypy.tools.json_out()
@cherrypy.tools.json_in()
class StringGeneratorWebService(object):

    @cherrypy.tools.accept(media='text/plain')
    def GET(self):
        enable_crossdomain()
        msg = {'Success': False}
        return json.dumps(msg)

    def POST(self):
        enable_crossdomain()
        req = cherrypy.request.json
        json_req = json.loads(req)
        print(json_req['length'])
        return json_req

    def PUT(self):
        enable_crossdomain()
        msg = {'Success': False}
        return json.dumps(msg)

    def DELETE(self):
        enable_crossdomain()
        msg = {'Success': False}
        return json.dumps(msg)


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    cherrypy.quickstart(StringGeneratorWebService(), '/', conf)
