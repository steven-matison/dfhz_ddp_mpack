from __future__ import print_function

import os
import re

from ambari_server.setupMpacks import get_mpack_properties
from resource_management.core import shell
from resource_management.core import sudo
from resource_management.core.logger import Logger

Logger.initialize_logger()

SMARTSENSE_VERSION_TEMPLATE = "{BASE_VERSION}.{AMBARI_VERSION}"
VERSION_RE = r"^(([0-9]+)\.([0-9]+)\.([0-9]+))\.([0-9]+)((\.|-).*)?$"
FILES_LIST = [
  "metainfo.xml",
  "configuration/hst-agent-conf.xml",
  "package/scripts/hst_script.py",
  "package/scripts/params.py"
]

STACKS_PATH, _, _, _, _ = get_mpack_properties()
SMARTSENSE_DIRECTORY = os.path.join(STACKS_PATH, "HDF", "3.2.b", "services", "SMARTSENSE")
VIEW_JAR_FOLDER = os.path.join(SMARTSENSE_DIRECTORY, "package", "files", "view")


def get_ambari_version():
  code, out = shell.checked_call(["ambari-server", "--version"], sudo=True)
  possible_version = out.strip()
  match = re.match(VERSION_RE, possible_version)
  if match:
    return possible_version, match.group(1)
  else:
    raise Exception("Failed to get ambari-server version")


def fix_smartsense_versions():
  ambari_version, _3_digit_ambari_version = get_ambari_version()
  if _3_digit_ambari_version == "2.7.3":
    base_version = "1.5.1"
  else:
    base_version = "1.5.0"
  desired_version = SMARTSENSE_VERSION_TEMPLATE.format(BASE_VERSION=base_version, AMBARI_VERSION=ambari_version)
  for _file in FILES_LIST:
    file_path = os.path.join(SMARTSENSE_DIRECTORY, _file)
    file_content = sudo.read_file(file_path, "utf8")
    file_content = file_content.replace("${project.version}", desired_version)
    sudo.create_file(file_path, file_content, "utf8")

  source_view_jar_file_path = os.path.join(
    VIEW_JAR_FOLDER,
    "smartsense-ambari-view-{version}.jar".format(version=_3_digit_ambari_version)
  )
  new_view_jar_file_path = os.path.join(
    VIEW_JAR_FOLDER,
    "smartsense-ambari-view-{version}.jar".format(version=desired_version)
  )
  shell.checked_call(["cp", "-f", source_view_jar_file_path, new_view_jar_file_path], sudo=True)
