# dfhz_ddp_mpack
<h1>DFHz Demo Data Platform for Ambari</h1>


#### Management Pack Installaion
<pre>ambari-server install-mpack --mpack=https://github.com/steven-dfheinz/dfhz_ddp_mpack/raw/master/ddp-ambari-mpack-0.0.0.1-0.tar.gz --verbose
ambari-server restart</pre>


#### Management Pack Removal
<pre>aambari-server uninstall-mpack --mpack-name=ddp-ambari-mpack
ambari-server restart</pre>

#### HDP 3.x Status
- Currently working on a stack recommendations issue.
- There is a current bug in User Group Management for HDP 3.x.  The work around is the following python command before installing Custom Services
<pre>python /var/lib/ambari-server/resources/scripts/configs.py -u admin -p admin -n [CLUSTER_NAME] -l [CLUSTER_FQDN] -t 8080 -a set -c cluster-env -k  ignore_groupsusers_create -v true</pre>
**** be sure to get the correct [CLUSTER_NAME] and [CLUSTER_FQDN] for command above
