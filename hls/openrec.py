#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)
import urllib2,urlparse,os.path,re
import base ,lib


DOMAIN = u"www.openrec.tv"

class OpenRecManager(base.BaseManager):
    LIVE = 0
    MOVIE = 16
    
    def __super(self):
        return super(OpenRecManager,self)
    def __init__(self,opener):
        self.__super().__init__(opener)
        self.live_parser = OpenRecLiveParser()
        self.movie_parser = OpenRecMovieParser()
        
    def get_stream(self,url):
        url_type = self.get_type(url)
        if url_type is None:
            return None
        if url_type == OpenRecManager.LIVE:
            (title,parent) = self.get_info(url,self.live_parser)
        else:
            (title,parent) = self.get_info(url,self.movie_parser)
        if parent is not None:
            srcs = self.get_srcs(parent)
        else:
            srcs = None
        return base.Stream(title,parent,srcs)
    def get_type(self,url):
        pr = urlparse.urlparse(url)
        if pr.netloc == DOMAIN:
            if len(pr.path) > 0:
                dir = os.path.split(pr.path)[0]
                if dir == u"/live":
                    return self.LIVE
                elif dir == u"/movie":
                    return self.MOVIE
        
        return None

    def get_info(self,url,parser):
        r_watch = self.opener.open(url)
        charset = lib.get_charset(r_watch)
        if charset is None:
            charset = "utf-8"
        parser.feed(r_watch.read(),charset)
        parent = parser.data_file
        title = parser.title
        
        
        
        parser.close()
        parser.reset()
        r_watch.close()
        return (title,parent)

    def get_live_qualities(self,src):
        return self.get_qualities(src,self.re_lq)
    def get_movie_qualities(self,src):
        return self.get_qualities(src,self.re_mq)
    
    
class BaseOpenRecParser(lib.MultibyteParser):
    #call in __init__
    def reset(self):
        lib.MultibyteParser.reset(self)
        self.data_file = None
        self.in_title = False
        self.title = None
    
    def handle_starttag(self,tag,attrs):
        if tag == "div":
            for attr in attrs:
                if attr[0] == "class":
                    if attr[1] == "p-playbox__content__info__title":
                        self.in_title = True
        
    def handle_data(self,data):
        if self.in_title:
            self.title = data
            
    def handle_endtag(self,tag):
        if tag == "div":
            if self.in_title:
                self.in_title = False
            
        
    
class OpenRecLiveParser(BaseOpenRecParser):
    
    def handle_starttag(self,tag,attrs):
        if tag == "div":
            is_js_data_player = False
            data_file = None
            for attr in attrs:
                if attr[0] == "class":
                    if attr[1] == "js-data__player":
                        is_js_data_player = True
                    elif attr[1] == "p-playbox__content__info__title":
                        self.in_title = True
                elif attr[0] == "data-file":
                    data_file = attr[1]
                
            if is_js_data_player and data_file is not None and len(data_file) > 0:
                self.data_file = data_file
                

class OpenRecMovieParser(BaseOpenRecParser):
    def __init__(self):
        BaseOpenRecParser.__init__(self)
        self.re_movie = re.compile(ur"(https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z0-9-]+(?:/[a-zA-Z0-9-_]+)+/index\.m3u8)")
        
    #call in __init__
    def reset(self):
        BaseOpenRecParser.reset(self)
        self.in_js = False
        
    def handle_starttag(self,tag,attrs):
        if tag == "div":
            for attr in attrs:
                if attr[0] == "class":
                    if attr[1] == "p-playbox__content__info__title":
                        self.in_title = True
        elif tag == "script":
            for attr in attrs:
                if attr[0] == "type":
                    if attr[1] == "text/javascript":
                        self.in_js = True
    def handle_data(self,data):
        if self.in_title:
            self.title = data
        elif self.in_js:
            m = self.re_movie.search(data)
            if m is not None:
                self.data_file = m.group(1)
        
    def handle_endtag(self,tag):
        if tag == "div":
            if self.in_title:
                self.in_title = False
           
        elif tag == "script":
            if self.in_js:
                self.in_js = False
            
        


