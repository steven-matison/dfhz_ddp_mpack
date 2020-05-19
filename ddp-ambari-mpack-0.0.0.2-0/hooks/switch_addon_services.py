#!/usr/bin/env python

'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import ast
import json
import os
import sys

from ambari_server.setupMpacks import get_mpack_properties, process_stack_addon_service_definitions_artifact, \
  STACK_ADDON_SERVICE_DEFINITIONS_ARTIFACT_NAME
from ambari_commons.logging_utils import print_info_msg, print_error_msg, print_warning_msg, get_verbose, set_verbose

class _named_dict(dict):
  """
  Allow to get dict items using attribute notation, eg dict.attr == dict['attr']
  """
  def __init__(self, _dict):

    def repl_list(_list):
      for i, e in enumerate(_list):
        if isinstance(e, list):
          _list[i] = repl_list(e)
        if isinstance(e, dict):
          _list[i] = _named_dict(e)
      return _list

    dict.__init__(self, _dict)
    for key, value in self.iteritems():
      if isinstance(value, dict):
        self[key] = _named_dict(value)
      if isinstance(value, list):
        self[key] = repl_list(value)

  def __getattr__(self, item):
    if item in self:
      return self[item]
    else:
      dict.__getattr__(self, item)

def switch_addon_services(config_file):

  old_verbose_level = get_verbose()
  set_verbose(True)
  if not os.path.exists(config_file):
    print_error_msg('Configuration file {0} does not exist!'.format(config_file))
    set_verbose(old_verbose_level)
    return 1

  print_info_msg("Switching addon services using config file {0}".format(config_file))
  stack_location, extension_location, service_definitions_location, mpacks_staging_location, dashboard_location = get_mpack_properties()
  mpack_metadata = _named_dict(json.load(open(config_file, "r")))
  if not mpack_metadata:
    print_error_msg('Malformed configuration file {0}'.format(config_file))
    set_verbose(old_verbose_level)
    return 1

  mpack_name = mpack_metadata.name
  mpack_version = mpack_metadata.version
  mpack_dirname = mpack_name + "-" + mpack_version
  mpack_staging_dir = os.path.join(mpacks_staging_location, mpack_dirname)

  options = _named_dict(ast.literal_eval("{'force' : True, 'verbose' : True}"))
  for artifact in mpack_metadata.artifacts:
    # Artifact name (Friendly name)
    artifact_name = artifact.name
    # Artifact type (stack-definitions, extension-definitions, service-definitions, etc)
    artifact_type = artifact.type
    # Artifact directory with contents of the artifact
    artifact_source_dir = os.path.join(mpack_staging_dir, artifact.source_dir)

    # Artifact directory with contents of the artifact
    artifact_source_dir = os.path.join(mpack_staging_dir, artifact.source_dir)
    print_info_msg("Processing artifact {0} of type {1} in {2}".format(
        artifact_name, artifact_type, artifact_source_dir))
    if artifact.type == STACK_ADDON_SERVICE_DEFINITIONS_ARTIFACT_NAME:
      process_stack_addon_service_definitions_artifact(artifact, artifact_source_dir, options)

  print_info_msg("Successfully switched addon services using config file {0}".format(config_file))
  set_verbose(old_verbose_level)
  return 0

def main(argv=None):
  if argv is None or len(argv) != 2:
    print "Error: Invalid parameters passed"
    print "Usage:"
    print "python switch_addon_services.py <config-file-path>"
    return 1
  return switch_addon_services(argv[1])

if __name__ == "__main__":
  exit (main(sys.argv))
