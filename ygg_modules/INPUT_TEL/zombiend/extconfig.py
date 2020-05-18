# -*- coding: utf-8 -*-
from os import path
from .corpse import dict2

def videoserver_settings(filename) :
  if filename != None :
    config_file = filename
  else :
    config_file = path.join(path.dirname(__file__),'videoserver.conf')
  config_file = path.abspath(config_file)
  video_registrators = []
  video_global_config = {'enabled' : False}
  dict_conf = get_config(config_file)
  if dict_conf == None :
    return video_global_config, video_registrators
  for k, v in dict_conf.iteritems() :
    if v.has_key('ip') and v.has_key('port') and v.has_key('driver') :
      video_registrators.append(v)
    if k == 'global' and v['enabled'].lower() == 'on' :
      video_global_config['enabled'] = True
  return video_global_config, video_registrators


def getsettings(settings_type, filename=None) :
  settings_type = settings_type.upper()
  if settings_type == 'VIDEOSERVER' :
    return videoserver_settings(filename)
  else :
    raise Exception('Unknown settings type')

def get_config(fname) :
  try :
    f = open(fname, 'r')
    raw_conf = [s for s in f.read().split('\n') if (len(s.strip()) > 0) and (s[0] != ';')]
    f.close()
  except :
    return None
  dict_conf = dict2()
  current_section = None
  for s in raw_conf :
    s = s.strip()
    if s[0] == '[' and s[-1] == ']' and len(s[1 :-1].strip()) > 0 :
      current_section = s[1 :-1].strip()
      if not dict_conf.has_key(current_section) : dict_conf[current_section] = dict2()
    elif current_section != None :
      kv = [i.strip() for i in s.split('=')]
      if len(kv) >= 2 :
        dict_conf[current_section][kv[0]] = kv[1]
  return dict_conf
