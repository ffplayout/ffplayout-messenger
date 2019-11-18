#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import time

from subprocess import Popen

context = zmq.Context()
port = "5555"

print("start ffplay ...")
cmd = ['ffplay', '-hide_banner', '-nostats', '-dumpgraph', '1', '-f', 'lavfi',
       ("color=s=512x288:c=black,zmq,drawtext=text='':fontsize=34:"
        "fontcolor=ffffff:x=(w-text_w)/2:y=(h-text_h)/2")]
proc = Popen(cmd)

print("Connecting to server with port {}".format(port))
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:{}".format(port))

print("Sending request ...")
socket.send("Parsed_drawtext_2 reinit "
            "text='Hello\\ World,\\ whats\\ up?':alpha='"
            "ifnot(ld(1),st(1,t));if(lt(t,ld(1)+1),0,"
            "if(lt(t,ld(1)+2),(t-(ld(1)+1))/1,if(lt(t,ld(1)+8),1,"
            "if(lt(t,ld(1)+9),(1-(t-(ld(1)+8)))/1,0))))'".encode('ascii'))
message = socket.recv()

print("Received reply: ", message.decode())

time.sleep(12)

proc.terminate()
