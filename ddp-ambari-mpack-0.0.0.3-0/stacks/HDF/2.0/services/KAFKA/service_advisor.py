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

class HDF20KAFKAServiceAdvisor(service_advisor.ServiceAdvisor):

    def __init__(self, *args, **kwargs):
        self.as_super = super(HDF20KAFKAServiceAdvisor, self)
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
        items = super(HDF20KAFKAServiceAdvisor, self).getServiceComponentLayoutValidations(services, hosts)
        return items

    def getServiceConfigurationRecommendations(self, configurations, clusterData, services, hosts):
        kafka_broker = self.getServicesSiteProperties(services, "kafka-broker")

        # kerberos security for kafka is decided from `security.inter.broker.protocol` property value
        security_enabled = (kafka_broker is not None and 'security.inter.broker.protocol' in  kafka_broker
                            and 'SASL' in kafka_broker['security.inter.broker.protocol'])
        putKafkaBrokerProperty = self.putProperty(configurations, "kafka-broker", services)
        putKafkaLog4jProperty = self.putProperty(configurations, "kafka-log4j", services)
        putKafkaBrokerAttributes = self.putPropertyAttribute(configurations, "kafka-broker")

        #If AMS is part of Services, use the KafkaTimelineMetricsReporter for metric reporting. Default is ''.
        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        if "AMBARI_METRICS" in servicesList:
            putKafkaBrokerProperty('kafka.metrics.reporters', 'org.apache.hadoop.metrics2.sink.kafka.KafkaTimelineMetricsReporter')

        if "ranger-env" in services["configurations"] and "ranger-kafka-plugin-properties" in services["configurations"] and \
                        "ranger-kafka-plugin-enabled" in services["configurations"]["ranger-env"]["properties"]:
            putKafkaRangerPluginProperty = self.putProperty(configurations, "ranger-kafka-plugin-properties", services)
            rangerEnvKafkaPluginProperty = services["configurations"]["ranger-env"]["properties"]["ranger-kafka-plugin-enabled"]
            putKafkaRangerPluginProperty("ranger-kafka-plugin-enabled", rangerEnvKafkaPluginProperty)

        if 'ranger-kafka-plugin-properties' in services['configurations'] and ('ranger-kafka-plugin-enabled' in services['configurations']['ranger-kafka-plugin-properties']['properties']):
            kafkaLog4jRangerLines = [{
                "name": "log4j.appender.rangerAppender",
                "value": "org.apache.log4j.DailyRollingFileAppender"
            },
                {
                    "name": "log4j.appender.rangerAppender.DatePattern",
                    "value": "'.'yyyy-MM-dd-HH"
                },
                {
                    "name": "log4j.appender.rangerAppender.File",
                    "value": "${kafka.logs.dir}/ranger_kafka.log"
                },
                {
                    "name": "log4j.appender.rangerAppender.layout",
                    "value": "org.apache.log4j.PatternLayout"
                },
                {
                    "name": "log4j.appender.rangerAppender.layout.ConversionPattern",
                    "value": "%d{ISO8601} %p [%t] %C{6} (%F:%L) - %m%n"
                },
                {
                    "name": "log4j.logger.org.apache.ranger",
                    "value": "INFO, rangerAppender"
                }]

            rangerPluginEnabled=''
            if 'ranger-kafka-plugin-properties' in configurations and 'ranger-kafka-plugin-enabled' in  configurations['ranger-kafka-plugin-properties']['properties']:
                rangerPluginEnabled = configurations['ranger-kafka-plugin-properties']['properties']['ranger-kafka-plugin-enabled']
            elif 'ranger-kafka-plugin-properties' in services['configurations'] and 'ranger-kafka-plugin-enabled' in services['configurations']['ranger-kafka-plugin-properties']['properties']:
                rangerPluginEnabled = services['configurations']['ranger-kafka-plugin-properties']['properties']['ranger-kafka-plugin-enabled']

            if  rangerPluginEnabled and rangerPluginEnabled.lower() == "Yes".lower():
                # recommend authorizer.class.name
                putKafkaBrokerProperty("authorizer.class.name", 'org.apache.ranger.authorization.kafka.authorizer.RangerKafkaAuthorizer')
                # change kafka-log4j when ranger plugin is installed

                if 'kafka-log4j' in services['configurations'] and 'content' in services['configurations']['kafka-log4j']['properties']:
                    kafkaLog4jContent = services['configurations']['kafka-log4j']['properties']['content']
                    for item in range(len(kafkaLog4jRangerLines)):
                        if kafkaLog4jRangerLines[item]["name"] not in kafkaLog4jContent:
                            kafkaLog4jContent+= '\n' + kafkaLog4jRangerLines[item]["name"] + '=' + kafkaLog4jRangerLines[item]["value"]
                    putKafkaLog4jProperty("content",kafkaLog4jContent)


            else:
                # Kerberized Cluster with Ranger plugin disabled
                if security_enabled and 'kafka-broker' in services['configurations'] and 'authorizer.class.name' in services['configurations']['kafka-broker']['properties'] and \
                                services['configurations']['kafka-broker']['properties']['authorizer.class.name'] == 'org.apache.ranger.authorization.kafka.authorizer.RangerKafkaAuthorizer':
                    putKafkaBrokerProperty("authorizer.class.name", 'kafka.security.auth.SimpleAclAuthorizer')
                # Non-kerberos Cluster with Ranger plugin disabled
                else:
                    putKafkaBrokerAttributes('authorizer.class.name', 'delete', 'true')

        # Non-Kerberos Cluster without Ranger
        elif not security_enabled:
            putKafkaBrokerAttributes('authorizer.class.name', 'delete', 'true')

    def validateKAFKAConfigurations(self, properties, recommendedDefaults, configurations, services, hosts):
        kafka_broker = properties
        validationItems = []

        #Adding Ranger Plugin logic here
        ranger_plugin_properties = self.getSiteProperties(configurations, "ranger-kafka-plugin-properties")
        ranger_plugin_enabled = ranger_plugin_properties['ranger-kafka-plugin-enabled'] if ranger_plugin_properties else 'No'
        prop_name = 'authorizer.class.name'
        prop_val = "org.apache.ranger.authorization.kafka.authorizer.RangerKafkaAuthorizer"
        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        if ("RANGER" in servicesList) and (ranger_plugin_enabled.lower() == 'Yes'.lower()):
            if kafka_broker[prop_name] != prop_val:
                validationItems.append({"config-name": prop_name,
                                        "item": self.getWarnItem(
                                            "If Ranger Kafka Plugin is enabled." \
                                            "{0} needs to be set to {1}".format(prop_name,prop_val))})

        kafka_broker_properties = self.getSiteProperties(configurations, "kafka-broker")
        # Find number of services installed, get them all and find kafka service json obj in them.
        number_services = len(services['services'])
        for each_service in range(0, number_services):
            if services['services'][each_service]['components'][0]['StackServiceComponents']['service_name'] == 'KAFKA':
                num_kakfa_brokers = len(services['services'][each_service]['components'][0]['StackServiceComponents']['hostnames'])
                if int(kafka_broker_properties['offsets.topic.replication.factor']) > num_kakfa_brokers:
                    validationItems.append({"config-name": 'offsets.topic.replication.factor',
                        "item": self.getWarnItem(
                        "offsets.topic.replication.factor={0} is greater than the number of kafka brokers={1}. " \
                        "It is recommended to decrease it or increase the number of kafka brokers." \
                        .format(kafka_broker_properties['offsets.topic.replication.factor'], num_kakfa_brokers))})

        return self.toConfigurationValidationProblems(validationItems, "kafka-broker")

    def validateKafkaRangerPluginConfigurations(self, properties, recommendedDefaults, configurations, services, hosts):
        validationItems = []
        ranger_plugin_properties = self.getSiteProperties(configurations, "ranger-kafka-plugin-properties")
        ranger_plugin_enabled = ranger_plugin_properties['ranger-kafka-plugin-enabled'] if ranger_plugin_properties else 'No'
        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        if ranger_plugin_enabled.lower() == 'yes':
            # ranger-kafka-plugin must be enabled in ranger-env
            ranger_env = self.getServicesSiteProperties(services, 'ranger-env')
            if not ranger_env or not 'ranger-kafka-plugin-enabled' in ranger_env or \
                            ranger_env['ranger-kafka-plugin-enabled'].lower() != 'yes':
                validationItems.append({"config-name": 'ranger-kafka-plugin-enabled',
                                        "item": self.getWarnItem(
                                            "ranger-kafka-plugin-properties/ranger-kafka-plugin-enabled must correspond ranger-env/ranger-kafka-plugin-enabled")})

        if ("RANGER" in servicesList) and (ranger_plugin_enabled.lower() == 'yes') and not 'KERBEROS' in servicesList:
            validationItems.append({"config-name": "ranger-kafka-plugin-enabled",
                                    "item": self.getWarnItem(
                                        "Ranger Kafka plugin should not be enabled in non-kerberos environment.")})

        return self.toConfigurationValidationProblems(validationItems, "ranger-kafka-plugin-properties")

    def validateConfigurationsForSite(self, configurations, recommendedDefaults, services, hosts, siteName, method):
        properties = self.getSiteProperties(configurations, siteName)
        if properties:
            return super(HDF20KAFKAServiceAdvisor, self).validateConfigurationsForSite(configurations, recommendedDefaults, services, hosts, siteName, method)
        else:
            return []


    def getServiceConfigurationsValidationItems(self, configurations, recommendedDefaults, services, hosts):
        siteName = "kafka-broker"
        method = self.validateKAFKAConfigurations
        items = self.validateConfigurationsForSite(configurations, recommendedDefaults, services, hosts, siteName, method)

        siteName = "ranger-kafka-plugin-properties"
        method = self.validateKafkaRangerPluginConfigurations
        items.extend(self.validateConfigurationsForSite(configurations, recommendedDefaults, services, hosts, siteName, method))

        return items
