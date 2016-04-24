#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

import urllib2,urlparse,re
import lib


class BaseManager(object):
    
    SRC_PATTERN = ur"^#.*BANDWIDTH=(\d+).*\n(.*\.m3u8(?:\?.*)?)"
    
    def __init__(self,opener = None):
        if opener is None:
            self.opener = urllib2.build_opener()
        else:
            self.opener = opener
        self.re_src = re.compile(self.SRC_PATTERN,flags = re.M)
    def get_stream(self,url):
        return BaseStream()
    def to_srcs(self,base,raw_srcs):
        srcs = {}
        for raw_src in raw_srcs:
            srcs[str(self.round(int(raw_src[0]) / 1000))] = urlparse.urljoin(base,raw_src[1])
        return srcs
    def to_src(self,quality,parent):
        return {quality:parent}
    def round(self,bitrate):
        if bitrate >= 100:
            return bitrate / 100 * 100
        else:
            return bitrate
    def get_srcs(self,parent):
        r = self.opener.open(parent)
        charset = lib.get_charset(r)
        if charset is None:
            charset = "utf-8"
        r_str = r.read().decode(charset)
        r.close()
        founds = self.re_src.findall(r_str)
        
        return self.to_srcs(self.get_base(parent),founds)
    def get_base(self,parent):
        return parent
class Stream(object):
    FORMAT = u"mpegts"
    EXT = u".ts"
    
    def __init__(self,title,parent,srcs,allow_no_quality = False):
        self.title = title
        self.parent = parent
        self.__srcs = srcs
        self.allow_no_quality = allow_no_quality
    def has_srcs(self):
        return self.__srcs is not None
    def get_src(self,quality):
        return self.__srcs[quality]
    def get_qualities(self):
        qualities = self.__srcs.keys()
        return sorted(qualities,key = lambda x:int(x),reverse = True)

class Video(Stream):
    FORMAT = u"flv"
    EXT = u".flv"
    
