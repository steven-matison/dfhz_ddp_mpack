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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.join(SCRIPT_DIR, '../../../3.0/services/STORM')
PARENT_FILE = os.path.join(SERVICE_DIR, 'service_advisor.py')

try:
    with open(PARENT_FILE, 'rb') as fp:
        service_advisor = imp.load_module('service_advisor', fp, PARENT_FILE, ('.py', 'rb', imp.PY_SOURCE))
except Exception as e:
    traceback.print_exc()
    print "Failed to load parent"

class HDF31STORMServiceAdvisor(service_advisor.HDF30STORMServiceAdvisor):

    def getServiceConfigurationRecommendations(self, configurations, clusterData, services, hosts):
        super(HDF31STORMServiceAdvisor, self).getServiceConfigurationRecommendations(configurations, clusterData, services, hosts)
        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        putStormSiteProperty = self.putProperty(configurations, "storm-site", services)

            # Storm AMS integration
        if 'AMBARI_METRICS' in servicesList:
            putStormSiteProperty('storm.cluster.metrics.consumer.register', '[{"class": "org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsReporter"}]')
            putStormSiteProperty('topology.metrics.consumer.register',
                                 '[{"class": "org.apache.hadoop.metrics2.sink.storm.StormTimelineMetricsSink", '
                                 '"parallelism.hint": 1, '
                                 '"whitelist": ["kafkaOffset\\\..+/", "__complete-latency", "__process-latency", '
                                 '"__execute-latency", '
                                 '"__receive\\\.population$", "__sendqueue\\\.population$", "__execute-count", "__emit-count", '
                                 '"__ack-count", "__fail-count", "memory/heap\\\.usedBytes$", "memory/nonHeap\\\.usedBytes$", '
                                 '"GC/.+\\\.count$", "GC/.+\\\.timeMs$"]}]')
        else:
            putStormSiteProperty('storm.cluster.metrics.consumer.register', 'null')
            putStormSiteProperty('topology.metrics.consumer.register', 'null')


    def validateStormConfigurations(self, properties, recommendedDefaults, configurations, services, hosts):
        parentValidationProblems = super(HDF31STORMServiceAdvisor, self).validateStormConfigurations(properties, recommendedDefaults, configurations, services, hosts)
        validationItems = []

        servicesList = [service["StackServices"]["service_name"] for service in services["services"]]
        # Storm AMS integration
        if 'AMBARI_METRICS' in servicesList:
            if "storm.cluster.metrics.consumer.register" in properties and \
                            'null' in properties.get("storm.cluster.metrics.consumer.register"):

                validationItems.append({"config-name": 'storm.cluster.metrics.consumer.register',
                                        "item": self.getWarnItem(
                                            "Should be set to recommended value to report metrics to Ambari Metrics service.")})

            if "topology.metrics.consumer.register" in properties and \
                            'null' in properties.get("topology.metrics.consumer.register"):

                validationItems.append({"config-name": 'topology.metrics.consumer.register',
                                        "item": self.getWarnItem(
                                            "Should be set to recommended value to report metrics to Ambari Metrics service.")})

        validationProblems = self.toConfigurationValidationProblems(validationItems, "storm-site")
        validationProblems.extend(parentValidationProblems)
        return validationProblems
