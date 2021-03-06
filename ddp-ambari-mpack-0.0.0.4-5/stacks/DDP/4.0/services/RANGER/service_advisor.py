#!/usr/bin/env ambari-python-wrap
"""
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
"""

import imp
import os
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STACKS_DIR = os.path.join(SCRIPT_DIR, '../../../3.2.b/services/RANGER/')
PARENT_FILE = os.path.join(STACKS_DIR, 'service_advisor.py')

try:
  with open(PARENT_FILE, 'rb') as fp:
    service_advisor = imp.load_module('service_advisor', fp, PARENT_FILE, ('.py', 'rb', imp.PY_SOURCE))
except Exception as e:
  traceback.print_exc()
  print "Failed to load parent"

class DDP34RANGERServiceAdvisor(service_advisor.RangerServiceAdvisor):

  def __init__(self, *args, **kwargs):
    self.as_super = super(DDP34RANGERServiceAdvisor, self)
    self.as_super.__init__(*args, **kwargs)

  def getServiceConfigurationRecommendations(self, configurations, clusterData, services, hosts):
    super(DDP34RANGERServiceAdvisor, self).getServiceConfigurationRecommendations(configurations, clusterData, services, hosts)

    recommender = DDP34RangerRecommender()
    recommender.recommendRangerConfigurationsFromDDP34(configurations, clusterData, services, hosts)

class DDP34RangerRecommender(service_advisor.ServiceAdvisor):
  """
  Ranger Recommender suggests properties when adding the service for the first time or modifying configs via the UI.
  """

  def __init__(self, *args, **kwargs):
    self.as_super = super(DDP34RangerRecommender, self)
    self.as_super.__init__(*args, **kwargs)

  def recommendRangerConfigurationsFromDDP34(self, configurations, clusterData, services, hosts):

    putRangerAdminProperty = self.putProperty(configurations, "ranger-admin-site", services)
    putRangerAdminAttribute = self.putPropertyAttribute(configurations, "ranger-admin-site")
    servicesList = [service["StackServices"]["service_name"] for service in services["services"]]

    if 'forced-configurations' not in services:
      services["forced-configurations"] = []

    if "KNOX" in servicesList:
      knox_host = self.getHostWithComponent("KNOX", "KNOX_GATEWAY", services, hosts)
      knox_host_ip = knox_host['Hosts']['ip']

      if 'knox-env' in services['configurations'] and 'knox_user' in services['configurations']['knox-env']['properties']:
        knox_user = services['configurations']['knox-env']['properties']['knox_user']
        knox_old_user = self.getOldValue(services, "knox-env", "knox_user")

        putRangerAdminProperty('ranger.proxyuser.{0}.users'.format(knox_user), '*')
        putRangerAdminProperty('ranger.proxyuser.{0}.hosts'.format(knox_user), '*')
        putRangerAdminProperty('ranger.proxyuser.{0}.groups'.format(knox_user), '*')
        putRangerAdminProperty('ranger.proxyuser.{0}.ip'.format(knox_user), knox_host_ip)

        if knox_old_user is not None and knox_user != knox_old_user:
          putRangerAdminAttribute('ranger.proxyuser.{0}.users'.format(knox_old_user), 'delete', 'true')
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.users'.format(knox_old_user)})
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.users'.format(knox_user)})

          putRangerAdminAttribute('ranger.proxyuser.{0}.hosts'.format(knox_old_user), 'delete', 'true')
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.hosts'.format(knox_old_user)})
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.hosts'.format(knox_user)})

          putRangerAdminAttribute('ranger.proxyuser.{0}.groups'.format(knox_old_user), 'delete', 'true')
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.groups'.format(knox_old_user)})
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.groups'.format(knox_user)})

          putRangerAdminAttribute('ranger.proxyuser.{0}.ip'.format(knox_old_user), 'delete', 'true')
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.ip'.format(knox_old_user)})
          services['forced-configurations'].append({'type' : 'ranger-admin-site', 'name' : 'ranger.proxyuser.{0}.ip'.format(knox_user)})
