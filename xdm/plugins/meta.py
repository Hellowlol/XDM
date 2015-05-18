#!/usr/bin/env python
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
import xdm

from xdm.logger import *
import collections
import traceback
from xdm.classes import Config


class ConfigWrapper(object):
    """this will be the "c", "hc" or "e" of a plugin to easily get the config for the current plugin
    also handels the saving of the new config"""

    plugin_config = None
    hidden = None

    def __init__(self, config, hidden=False):
        self.plugin_config = config
        self.hidden = hidden

    def __getattr__(self, name):
        if xdm.common.CONFIGOVERWRITE:
            overwrite = xdm.common.getConfigOverWriteForPlugin(self._plugin)
            if name in overwrite:
                if isinstance(overwrite[name], dict):
                    if "store" in overwrite[name] and overwrite[name]["store"]:
                        setattr(self, name, overwrite[name]["value"])
                    self._configValueCache[name] = overwrite[name]["value"]
                else:
                    self._configValueCache[name] = overwrite[name]
                return self._configValueCache[name]

        for config in self.configs:
            if config.name == name:
                return config.value
        raise AttributeError(
            "no config with the name '{}' hidden: {}".format(
                name, self.hidden))

    @property
    def configs(self):
        return [c for c in self.plugin_config.configs if c.hidden == self.hidden]

    def __setattr__(self, name, value):
        if self.plugin_config:
            for config in self.plugin_config.configs:
                if self.hidden == config.hidden and config.name == name:
                    config.value = value
                    self.plugin_config.save()
                    return

        super(ConfigWrapper, self).__setattr__(name, value)


class ConfigMeta(collections.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs)) # use the free update to set keys

    def __getitem__(self, key):
        try:
            return self.store[self.__keytransform__(key)]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key



def pluginMethodWrapper(caller_name, run, alternative):
    """Return a wrapped instance method"""
    def outer(*args, **kwargs):
        try:
            return run(*args, **kwargs)
        except Exception as ex:
            # print ex, args, kwargs
            tb = traceback.format_exc()
            # print tb
            out = alternative(*args, **kwargs)
            try:
                log.error(
                    "Error during %s of %s \nError: %s\n\n%s\nNew value:%s" % (
                        run.__name__, caller_name, ex, tb, out),
                    traceback=tb,
                    new_out=out,
                    exception=ex)
            except:
                log.error("Error during %s of %s \nError: %s\n\n%s" % (run.__name__, caller_name, ex, tb))
            return out
    return outer

__all__ = ['pluginMethodWrapper', 'ConfigMeta', 'ConfigWrapper']
