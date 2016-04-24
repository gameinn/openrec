#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

import urllib2,urlparse,os,re,optparse
import openrec,lib

CONF_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir)),u"settings.ini")



class HLSPlayer(object):
    
    
    def __init__(self,ffmpeg_path = None,player_path = None,ffmpeg_loglevel = None):
        
        self.conf = HLSConfig()
        
        self.sites = {
            openrec.DOMAIN:[None,openrec.OpenRecManager]
        }
        self.opener = urllib2.build_opener()
        
        self.parser = optparse.OptionParser(usage = "%prog [OPTIONS] [URL] [QUALITY]")
        self.parser.add_option("-o","--output",dest="output",action="store")
        self.parser.add_option("-f","--ffmpeg-path",dest="ffmpeg_path",action="store")
        self.parser.add_option("-p","--player-path",dest="player_path",action="store")
        self.parser.add_option("-s","--by-source",dest="by_src",action="store_true",default=False)
        self.parser.add_option("-P","--print-only",dest="print_only",action="store_true",default=False)
        self.parser.add_option("-n","--no-ffmpeg",dest="direct",action="store_true",default=False)
        self.parser.add_option("-l","--ffmpeg-loglevel",dest="ffmpeg_loglevel",action="store")
        
        self.parser.add_option("--settings-path",dest="settings_path",action="store")
        self.parser.add_option("--override-settings",dest="override_settings",action="store_true",default=False)
        
    def get_stream(self,url):
        p_result = urlparse.urlparse(url)
        site = self.sites.get(p_result.netloc,None)
        if site is None:
            return None
        else:
            if site[0] is None:
                manager = site[1](self.opener)
                site[0] = manager
            else:
                manager = site[0]
            return manager.get_stream(url)
    def play(self,commands):
        (options,args) = self.parser.parse_args(commands)
        if options.settings_path is not None:
            self.conf.load(options.settings_path)
            
        
        (ffmpeg_path,player_path,ffmpeg_loglevel) = self.conf.validate(options.ffmpeg_path,options.player_path,options.ffmpeg_loglevel)
        if options.override_settings:
            if not self.conf.updated(ffmpeg_path,player_path,ffmpeg_loglevel):
                logger.warn(u"No updated setting.")
            else:
                self.conf.dump(options.settings_path,ffmpeg_path,player_path,ffmpeg_loglevel)
        a_length = len(args)
        if a_length == 0:
            logger.error(self.parser.get_usage())
            return
        
        url = args[0]
        if not options.by_src:
            stream = self.get_stream(url)
            if stream is None:
                logger.error("{0} is an invalid URL.".format(url))
                return
            title = stream.title
            if title is None:
                logger.warn(u"No title.")
                
            else:
                logger.info(u'Title:{0}'.format(title))
            
            if stream.parent is None:
                logger.error(u"No parent manifest.")
                return
            if not stream.has_srcs():
                logger.error("No source for {0}.".format(stream.parent))
                return
            
            logger.info(u"Enable qualities:{0}".format(",".join(stream.get_qualities())))
            
            if a_length >= 2:
                
                quality = args[1]
                src = stream.get_src(quality)
                if src is None:
                    logger.error(u"{0} is an invalid quality.".format(quality))
                    return
            elif stream.allow_no_quality:
                src = stream.parent
            else:
                return
            format = stream.FORMAT
            ext = stream.EXT
        else:
            title = None
            src = url
            format = base.Stream.FORMAT
            ext = base.Stream.EXT
        logger.info(u"Source:{0}".format(src))
        
        
        if options.print_only:
            return
        
        if options.direct:
            if HLSConfig.is_invalid(player_path):
                logger.error(u"No player path.")
                return
            lib.call([player_path,src])
        else:
            if HLSConfig.is_invalid(ffmpeg_path):
                logger.error(u"No ffmpeg path.")
                return
                
            if HLSConfig.is_invalid(ffmpeg_loglevel):
                ffmpeg_loglevel = "fatal"
            
            if options.output is None:
                if HLSConfig.is_invalid(player_path):
                    logger.error(u"No player path.")
                    return
                cmd = self.get_cmd(src,"pipe:1",ffmpeg_loglevel,ffmpeg_path,format)
                lib.pipe(cmd,[player_path,"-"])
            else:
                output = options.output
                (root,ext) = os.path.splitext(output)
                if len(ext) == 0:
                    output = output + ext
                cmd = self.get_cmd(src,output,ffmpeg_loglevel,ffmpeg_path,format)
                lib.call(cmd)
        
        return
        
    def get_cmd(self,src,dst,ffmpeg_loglevel,ffmpeg_path,format):
        return [ffmpeg_path,"-i",src,"-c","copy","-f",format,"-loglevel",ffmpeg_loglevel,dst]
    
import ConfigParser,traceback,codecs

class HLSConfig(object):
    SECTIONS = ("ffmpeg","player")
    OPTIONS = {SECTIONS[0]:("path","loglevel"),SECTIONS[1]:("path",)}
    
    def __init__(self,ffmpeg_path = None,player_path = None,ffmpeg_loglevel = None):
        self.conf = ConfigParser.SafeConfigParser(allow_no_value = True)
        
        
        self.__load(CONF_PATH)
        self.validate_conf()
        self.set(ffmpeg_path,player_path,ffmpeg_loglevel)
    
    @classmethod
    def is_invalid(cls,param):
        return param is None or len(param) == 0
    def validate(self,ffmpeg_path,player_path,ffmpeg_loglevel):
        if self.is_invalid(ffmpeg_path):
            ffmpeg_path = self.ffmpeg_path
        
        if self.is_invalid(player_path):
            player_path = self.player_path
        
        if self.is_invalid(ffmpeg_loglevel):
            ffmpeg_loglevel = self.ffmpeg_loglevel
        return (ffmpeg_path,player_path,ffmpeg_loglevel)
    def set(self,ffmpeg_path,player_path,ffmpeg_loglevel):
        (ffmpeg_path,player_path,ffmpeg_loglevel) = self.validate(ffmpeg_path,player_path,ffmpeg_loglevel)
        self.ffmpeg_path = ffmpeg_path
        self.player_path = player_path
        self.ffmpeg_loglevel = ffmpeg_loglevel
        self.__set()
    def __set(self):
        for section in self.SECTIONS:
            for option in self.OPTIONS[section]:
                param = getattr(self,self.__get_attr_name(section,option))
                if param is not None:
                    param = param.encode("utf-8")
                self.conf.set(section,option,param)
        

    def get(self):
        return (self.ffmpeg_path,self.player_path,self.ffmpeg_loglevel)
        
    def __get(self,section,option):
        return self.conf.get(section,option)
    
    def __get_attr_name(self,section,option):
        return section + "_" + option
    
    def validate_conf(self):
        for section in self.SECTIONS:
            if not self.conf.has_section(section):
                self.conf.add_section(section)
            options = self.OPTIONS[section]
            for option in options:
                if not self.conf.has_option(section,option):
                    self.conf.set(section,option,None)
                setattr(self,self.__get_attr_name(section,option),self.conf.get(section,option))
    
    def updated(self,ffmpeg_path,player_path,ffmpeg_loglevel):
        return (ffmpeg_path,player_path,ffmpeg_loglevel) != self.get()
    
    def load(self,file_name = None):
        if file_name is None:
            file_name = CONF_PATH
        self.__load(file_name)
        self.validate_conf()
    
    def __load(self,file_name):
        try:
            f = codecs.open(file_name,"r","utf-8")
            self.conf.readfp(f)
            f.close()
        except IOError:
            logger.error(traceback.format_exc())
            return
        
        logger.info(u"Load settings from {0}.".format(os.path.abspath(file_name)))
        return
    def dump(self,file_name,ffmpeg_path,player_path,ffmpeg_loglevel):
        self.set(ffmpeg_path,player_path,ffmpeg_loglevel)
        if file_name is None:
            file_name = CONF_PATH
        self.__dump(file_name)
    def __dump(self,file_name):
        try:
            with open(file_name,"w") as f:
                f.write(u"# -*- coding: utf-8 -*-\n".encode("utf-8"))
                self.conf.write(f)
                f.write(u"#openrec.py --override-settings -f [ffmpeg_path] -p [player_path] -l [ffmpeg_loglevel]\n".encode("utf-8"))
        except IOError:
            logger.error(trabceback.format_excc())
            return
        logger.info(u"Dump settings to {0}.".format(os.path.abspath(file_name)))
    
    
    