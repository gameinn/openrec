#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

def initRoot(level = logging.INFO,handler = None):
    root = logging.getLogger()
    root.setLevel(level)
    if handler is None:
        handler = streamHandler()
    root.addHandler(handler)
def streamHandler(stream = None):
    return logging.StreamHandler(stream)

import HTMLParser,htmlentitydefs,re
class MultibyteParser(HTMLParser.HTMLParser):
    HTMLParser.entityref = re.compile('&([a-zA-Z][-.a-zA-Z0-9]*);')
    def feed(self,data,charset = "utf-8"):
        HTMLParser.HTMLParser.feed(self,data.decode(charset))
        
    def handle_entityref(self,name):
        try:
            self.handle_data(htmlentitydefs.entitydefs[name])
        except KeyError as e:
            logger.error("KeyError:{0} in MultibyteParser.".format(e.message))
            
            return
    def handle_charref(self,ref):
        if ref.isdigit():
            num = int(ref)
        else:
            try:
                num = int(ref[1:],16)
            except ValueError as e:
                logger.error("ValueError:{0} in MultibyteParser.".format(e.message))
                return
        self.handle_data(unichr(num))

import urllib2
def get_charset(response):
     return response.info().getparam("charset")
     

import subprocess
def get_args():
    import sys
    args = sys.argv
    result = args[1:]
    return map(str.decode,result)
    
def call(*popenargs, **kwargs):
    return subprocess.call(*popenargs,**kwargs)

def pipe(cmd1,cmd2,output = False):
    p1 = first_p(cmd1)
    p2 = last_p(cmd2,p1,output)
    p1.stdout.close()
    r = p2.communicate()
    p1.wait()
    return p1.returncode

def first_p(cmd):
    return subprocess.Popen(cmd,stdout = subprocess.PIPE)
def last_p(cmd,pre_p,output):
    if output:
        output = subprocess.PIPE
    else:
        output = None
    return subprocess.Popen(cmd,stdin = pre_p.stdout,stdout = output,stderr = output)


