#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import ConfigParser


class Limits(ConfigParser.ConfigParser):
    def __init__(self, limit_file_list):
        ConfigParser.ConfigParser.__init__(self)
        defconfig_path = os.path.split(os.path.split(os.path.realpath(__file__)))
        defconfig_file = os.path.join(defconfig_path, 'data/deflimits.cfg')

        if os.path.exists(defconfig_file):
            self.readfp(open(defconfig_file))
        if len(limit_file_list) > 0:
            self.read(limit_file_list)


def init_limits(limit_file_list):
    global limits
    limits = Limits(limit_file_list)
    # limits.get(section, option, raw, vars)
    # limits.getint
