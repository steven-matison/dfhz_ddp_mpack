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
import os
import imp
import traceback
from os.path import dirname
from ambari_server.serverConfiguration import get_ambari_properties, get_ambari_version

SCRIPT_DIR = dirname(dirname(dirname(dirname(dirname(os.path.abspath(__file__))))))
PARENT_FILE = os.path.join(SCRIPT_DIR, 'service_advisor.py')

try:
    with open(PARENT_FILE, 'rb') as fp:
        service_advisor = imp.load_module('service_advisor', fp, PARENT_FILE, ('.py', 'rb', imp.PY_SOURCE))
except Exception as e:
    traceback.print_exc()
    print "Failed to load parent"

class DDP20STORMServiceAdvisor(service_advisor.ServiceAdvisor):

    def __init__(self, *args, **kwargs):
        self.as_super = super(DDP20STORMServiceAdvisor, self)
        self.as_super.__init__(*args, **kwargs)

    def getSiteProperties(self,configurations, siteName):
        siteConfig = configurations.get(siteName)
        if siteConfig is None:
            return None
        return siteConfig.get("properties")

    def getServicesSiteProperties(self,services, siteName):
        configurations = services.get("configurations")
        if not configurations:
            return None
        siteConfig = configurations.get(siteName)
        if siteConfig is None:
            return None
        return siteConfig.get("properties")

    def getServiceComponentLayoutValidations(self, services, hosts):
        items = super(DDP20STORMServiceAdvisor, self).getServiceComponentLayoutValidations(services, hosts)
        return items

    def getServiceConfigurationRecommendations(self, configurations, clusterData, services, hosts):
        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        putStormSiteProperty = self.putProperty(configurations, "storm-site", services)
        putStormStartupProperty = self.putProperty(configurations, "storm-site", services)
        putStormSiteAttributes = self.putPropertyAttribute(configurations, "storm-site")

        # Storm AMS integration
        if 'AMBARI_METRICS' in servicesList:
            putStormSiteProperty('metrics.reporter.register', 'org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter')

        storm_site = self.getServicesSiteProperties(services, "storm-site")
        security_enabled = (storm_site is not None and "storm.zookeeper.superACL" in storm_site)
        if "ranger-env" in services["configurations"] and "ranger-storm-plugin-properties" in services["configurations"] and \
                        "ranger-storm-plugin-enabled" in services["configurations"]["ranger-env"]["properties"]:
            putStormRangerPluginProperty = self.putProperty(configurations, "ranger-storm-plugin-properties", services)
            rangerEnvStormPluginProperty = services["configurations"]["ranger-env"]["properties"]["ranger-storm-plugin-enabled"]
            putStormRangerPluginProperty("ranger-storm-plugin-enabled", rangerEnvStormPluginProperty)

        rangerPluginEnabled = ''
        if 'ranger-storm-plugin-properties' in configurations and 'ranger-storm-plugin-enabled' in  configurations['ranger-storm-plugin-properties']['properties']:
            rangerPluginEnabled = configurations['ranger-storm-plugin-properties']['properties']['ranger-storm-plugin-enabled']
        elif 'ranger-storm-plugin-properties' in services['configurations'] and 'ranger-storm-plugin-enabled' in services['configurations']['ranger-storm-plugin-properties']['properties']:
            rangerPluginEnabled = services['configurations']['ranger-storm-plugin-properties']['properties']['ranger-storm-plugin-enabled']

        nonRangerClass = 'org.apache.storm.security.auth.authorizer.SimpleACLAuthorizer'
        rangerServiceVersion=''
        if 'RANGER' in servicesList:
            rangerServiceVersion = [service['StackServices']['service_version'] for service in services["services"] if service['StackServices']['service_name'] == 'RANGER'][0]

        if rangerServiceVersion and rangerServiceVersion == '0.4.0':
            rangerClass = 'com.xasecure.authorization.storm.authorizer.XaSecureStormAuthorizer'
        else:
            rangerClass = 'org.apache.ranger.authorization.storm.authorizer.RangerStormAuthorizer'
        # Cluster is kerberized
        if security_enabled:
            if rangerPluginEnabled and (rangerPluginEnabled.lower() == 'Yes'.lower()):
                putStormSiteProperty('nimbus.authorizer',rangerClass)
            elif (services["configurations"]["storm-site"]["properties"]["nimbus.authorizer"] == rangerClass):
                putStormSiteProperty('nimbus.authorizer', nonRangerClass)
        else:
            putStormSiteAttributes('nimbus.authorizer', 'delete', 'true')

        if "storm-site" in services["configurations"]:
            # atlas
            notifier_plugin_property = "storm.topology.submission.notifier.plugin.class"
            if notifier_plugin_property in services["configurations"]["storm-site"]["properties"]:
                notifier_plugin_value = services["configurations"]["storm-site"]["properties"][notifier_plugin_property]
                if notifier_plugin_value is None:
                    notifier_plugin_value = " "
            else:
                notifier_plugin_value = " "

            include_atlas = "ATLAS" in servicesList
            atlas_hook_class = "org.apache.atlas.storm.hook.StormAtlasHook"
            if include_atlas and atlas_hook_class not in notifier_plugin_value:
                if notifier_plugin_value == " ":
                    notifier_plugin_value = atlas_hook_class
                else:
                    notifier_plugin_value = notifier_plugin_value + "," + atlas_hook_class
            if not include_atlas and atlas_hook_class in notifier_plugin_value:
                application_classes = []
                for application_class in notifier_plugin_value.split(","):
                    if application_class != atlas_hook_class and application_class != " ":
                        application_classes.append(application_class)
                if application_classes:
                    notifier_plugin_value = ",".join(application_classes)
                else:
                    notifier_plugin_value = " "
            if notifier_plugin_value != " ":
                putStormStartupProperty(notifier_plugin_property, notifier_plugin_value)

    def validateStormConfigurations(self, properties, recommendedDefaults, configurations, services, hosts):
        validationItems = []
        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        # Storm AMS integration
        if 'AMBARI_METRICS' in servicesList and "metrics.reporter.register" in properties and \
                        "org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter" not in properties.get("metrics.reporter.register"):

            validationItems.append({"config-name": 'metrics.reporter.register',
                                    "item": self.getWarnItem(
                                        "Should be set to org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter to report the metrics to Ambari Metrics service.")})

        return self.toConfigurationValidationProblems(validationItems, "storm-site")

    def validateStormRangerPluginConfigurations(self, properties, recommendedDefaults, configurations, services, hosts):
        validationItems = []
        ranger_plugin_properties = self.getSiteProperties(configurations, "ranger-storm-plugin-properties")
        ranger_plugin_enabled = ranger_plugin_properties['ranger-storm-plugin-enabled'] if ranger_plugin_properties else 'No'
        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        if ranger_plugin_enabled.lower() == 'yes':
            # ranger-storm-plugin must be enabled in ranger-env
            ranger_env = self.getServicesSiteProperties(services, 'ranger-env')
            if not ranger_env or not 'ranger-storm-plugin-enabled' in ranger_env or \
                            ranger_env['ranger-storm-plugin-enabled'].lower() != 'yes':
                validationItems.append({"config-name": 'ranger-storm-plugin-enabled',
                                        "item": self.getWarnItem(
                                            "ranger-storm-plugin-properties/ranger-storm-plugin-enabled must correspond ranger-env/ranger-storm-plugin-enabled")})
        if ("RANGER" in servicesList) and (ranger_plugin_enabled.lower() == 'Yes'.lower()) and not 'KERBEROS' in servicesList:
            validationItems.append({"config-name": "ranger-storm-plugin-enabled",
                                    "item": self.getWarnItem(
                                        "Ranger Storm plugin should not be enabled in non-kerberos environment.")})
        return self.toConfigurationValidationProblems(validationItems, "ranger-storm-plugin-properties")

    def validateConfigurationsForSite(self, configurations, recommendedDefaults, services, hosts, siteName, method):
        properties = self.getSiteProperties(configurations, siteName)
        if properties:
            return super(DDP20STORMServiceAdvisor, self).validateConfigurationsForSite(configurations, recommendedDefaults, services, hosts, siteName, method)
        else:
            return []

    def getServiceConfigurationsValidationItems(self, configurations, recommendedDefaults, services, hosts):
        siteName = "storm-site"
        method = self.validateStormConfigurations
        items = self.validateConfigurationsForSite(configurations, recommendedDefaults, services, hosts, siteName, method)

        siteName = "ranger-storm-plugin-properties"
        method = self.validateStormRangerPluginConfigurations
        items.extend(self.validateConfigurationsForSite(configurations, recommendedDefaults, services, hosts, siteName, method))

        return items