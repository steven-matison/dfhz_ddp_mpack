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
from resource_management.libraries.functions.get_bare_principal import get_bare_principal
from ambari_server.serverConfiguration import get_ambari_properties, get_ambari_version

class DDP30StackAdvisor(DDP21StackAdvisor):

  def getServiceConfigurationRecommenderDict(self):
    parentRecommendConfDict = super(DDP30StackAdvisor, self).getServiceConfigurationRecommenderDict()
    childRecommendConfDict = {
      "RANGER": self.recommendRangerConfigurations
    }
    parentRecommendConfDict.update(childRecommendConfDict)
    return parentRecommendConfDict

  def getServiceConfigurationValidators(self):
    parentValidators = super(DDP30StackAdvisor, self).getServiceConfigurationValidators()
    childValidators = {
        "RANGER": {"ranger-ugsync-site": self.validateRangerUsersyncConfigurations}
    }
    self.mergeValidators(parentValidators, childValidators)
    return parentValidators

  def recommendRangerConfigurations(self, configurations, clusterData, services, hosts):
    super(DDP30StackAdvisor, self).recommendRangerConfigurations(configurations, clusterData, services, hosts)

    putRangerUgsyncSite = self.putProperty(configurations, 'ranger-ugsync-site', services)

    delta_sync_enabled = False
    if 'ranger-ugsync-site' in services['configurations'] and 'ranger.usersync.ldap.deltasync' in services['configurations']['ranger-ugsync-site']['properties']:
      delta_sync_enabled = services['configurations']['ranger-ugsync-site']['properties']['ranger.usersync.ldap.deltasync'] == "true"

    if delta_sync_enabled:
      putRangerUgsyncSite("ranger.usersync.group.searchenabled", "true")
    else:
      putRangerUgsyncSite("ranger.usersync.group.searchenabled", "false")

  def validateRangerUsersyncConfigurations(self, properties, recommendedDefaults, configurations, services, hosts):
    ranger_usersync_properties = properties
    validationItems = []

    delta_sync_enabled = 'ranger.usersync.ldap.deltasync' in ranger_usersync_properties \
      and ranger_usersync_properties['ranger.usersync.ldap.deltasync'].lower() == 'true'
    group_sync_enabled = 'ranger.usersync.group.searchenabled' in ranger_usersync_properties \
      and ranger_usersync_properties['ranger.usersync.group.searchenabled'].lower() == 'true'

    if delta_sync_enabled and not group_sync_enabled:
      validationItems.append({"config-name": "ranger.usersync.group.searchenabled",
                            "item": self.getWarnItem(
                            "Need to set ranger.usersync.group.searchenabled as true, as ranger.usersync.ldap.deltasync is enabled")})

    return self.toConfigurationValidationProblems(validationItems, "ranger-ugsync-site")

  def getCardinalitiesDict(self, hosts):
    return {
      'ZOOKEEPER_SERVER': {"min": 3},
      'METRICS_COLLECTOR': {"min": 1}
    }
