#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt

import BaseHTTPServer
import CGIHTTPServer


def usage():
    print "Uso: microhttpd -h -p port"
    print "     -h         Help"
    print "     -p port    Launch server"
    print "     -d dirname Change web directory (default: .)"

try:
    opts, args = getopt.getopt(sys.argv[1:], "hp:d:", ["help", "port=", "dir="])
except getopt.GetoptError:
    usage()
    sys.exit(2)

port = None
basedir = "www/"
for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    if o in ("-p", "--port"):
        port = a
    if o in ("-d", "--dir"):
        basedir = a

if (port == None):
    usage()
    sys.exit()

try:
    address = ('', int(port))
except ValueError:
    usage()
    sys.exit(2)

os.chdir(basedir)
CGIHTTPServer.CGIHTTPRequestHandler.extensions_map['.webm'] = 'video/webm'
CGIHTTPServer.CGIHTTPRequestHandler.extensions_map['.png'] = 'image/png'
CGIHTTPServer.CGIHTTPRequestHandler.extensions_map['.jpg'] = 'image/jpeg'
httpd = BaseHTTPServer.HTTPServer(address, CGIHTTPServer.CGIHTTPRequestHandler)
httpd.serve_forever()
