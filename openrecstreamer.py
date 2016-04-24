#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import logging
import hls,hls.lib
hls.lib.initRoot(logging.DEBUG)


def run():
    player = hls.HLSPlayer()
    args = hls.lib.get_args()
    player.play(args)

def main():
    run()
    
if __name__ == "__main__":
    main()