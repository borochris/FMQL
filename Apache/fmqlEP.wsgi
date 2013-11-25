#
# fmqlEP wsgi v1.1b
#
# This class stitches together brokerRPC and an FMQLQueryProcessor to make 
# an FMQL Endpoint that runs in Apache.
#
# LICENSE:
# This program is free software; you can redistribute it and/or modify it under the terms of 
# the GNU Affero General Public License version 3 (AGPL) as published by the Free Software 
# Foundation.
# (c) 2010-2013 caregraf
#

import os, sys, urlparse, re, json
sys.path.append(os.path.dirname(__file__))
from brokerRPC import RPCConnectionPool

class FMQLEP:

    def __init__(self):
        self.rpcc = None
        self.fmqlEnviron = None

    def setFMQLEnviron(self, fmqlEnviron):
        # for simple server
        # TBD: way to use os.environ instead?
        self.fmqlEnviron = fmqlEnviron

    def __call__(self, environ, start_response):
        try:
            if not self.rpcc: # TBD make thread safe
                if not self.fmqlEnviron: # for Apache, not simple server
                    self.fmqlEnviron = {}
                    self.fmqlEnviron["rpcbroker"] = environ["fmql.rpcbroker"]
                    self.fmqlEnviron["rpchost"] = environ["fmql.rpchost"]
                    self.fmqlEnviron["rpcport"] = environ["fmql.rpcport"]
                    self.fmqlEnviron["rpcaccess"] = environ["fmql.rpcaccess"]
                    self.fmqlEnviron["rpcverify"] = environ["fmql.rpcverify"]
                self.__initConnectionPool(environ)
            queryArgs = urlparse.parse_qs(environ['QUERY_STRING'])
            if "fmql" not in queryArgs:
                raise Exception("Expect fmql=")
            fmqlQuery = queryArgs["fmql"][0]
            reply = self.rpcc.invokeRPC("CG FMQL QP", [fmqlQuery])
        # Exceptions: setting up comms to VistA or even QP code error
        except Exception as e:
            print >> sys.stderr, "FMQLEP: %s" % e # internal or entry level errors
            status = '200 Error Handled'
            reply = json.dumps({"error": "Exception: %s" % e})
        else:
            status = '200 OK'
        response_headers = [('Content-type', 'application/json'),
                            ('Content-Length', str(len(reply)))]
        start_response(status, response_headers)
        return [reply]

    def __initConnectionPool(self, environ):
        # 25 if multi-threaded (ala winnt mpm or worker mpm), 1 otherwise (prefork unix, the Apache unix default). Nice if could
        # get actual number of threads in a process.
        noThreads = 25 if environ["wsgi.multithread"] == True else 1
        self.rpcc = RPCConnectionPool(self.fmqlEnviron["rpcbroker"], noThreads, self.fmqlEnviron["rpchost"], int(self.fmqlEnviron["rpcport"]), self.fmqlEnviron["rpcaccess"], self.fmqlEnviron["rpcverify"], "CG FMQL QP USER", WSGILogger("BrokerRPC"))

class WSGILogger:
    def __init__(self, generator):
        self.generator = generator

    def logError(self, tag, msg):
        logmsg = "%s (%s): %s -- %s" % (self.generator, os.getpid(), tag, msg)
        # TBD: consider passing in environ["wsgi.errors"] problem with expiration
        print >> sys.stderr, logmsg

    def logInfo(self, tag, msg):
        # self.logError(tag, msg)
        pass

application = FMQLEP()

if __name__ == '__main__':
    try:
        # create a simple WSGI server and run the application
        from wsgiref import simple_server
        print "Running test application - point your browser at http://localhost:8000/fmqlEP?fmql=DESCRIBE 2-1 ..."
        httpd = simple_server.WSGIServer(('', 8000), simple_server.WSGIRequestHandler)
        fmqlEnviron = {"rpcbroker": "VistA", "rpchost": "localhost", "rpcport": "9201", "rpcaccess": "QLFM1234", "rpcverify": "QLFM1234!!"}
        application.setFMQLEnviron(fmqlEnviron)
        httpd.set_app(application)
        httpd.serve_forever()
    except ImportError:
        # wsgiref not installed
        for content in application({}, lambda status, headers: None):
            print content
