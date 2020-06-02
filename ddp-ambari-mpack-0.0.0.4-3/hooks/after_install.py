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

import os
from switch_addon_services import switch_addon_services


def main():
  file_path = os.path.realpath(__file__)
  hooks_dir = os.path.dirname(file_path)
  hdf33_config_path = os.path.join(hooks_dir, "DDP-3.4.json")
  switch_addon_services(hdf33_config_path)
  return 0


if __name__ == "__main__":
  exit(main())
