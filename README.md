# dfhz_ddp_mpack
<h1>DFHz Demo Data Platform for Ambari</h1>

<b><i> RedHat 7 Centos 7 only.  If you need another operating system reach out privately.</i></b>

#### Install Ambari From MOSGA RPMS:
<pre>wget -O /etc/yum.repos.d/mosga.repo https://makeopensourcegreatagain.com/rpms/mosga.repo
yum install ambari-server ambari-agent -y
ambari-server setup -s
ambari-server start
ambari-agent start</pre>

#### Management Pack Installaion
<pre>ambari-server install-mpack --mpack=https://github.com/steven-dfheinz/dfhz_ddp_mpack/raw/master/ddp-ambari-mpack-0.0.0.4-2.tar.gz --verbose
ambari-server restart</pre>


#### Management Pack Removal
<pre>ambari-server uninstall-mpack --mpack-name=ddp-ambari-mpack
ambari-server restart</pre>

#### Known Issues
 - Sometimes the public repos for HDF/HDP (public-repo-1.hortonworks.com) are slow or do not respond during checks.  Refresh page, skip validation, choose use local repos then choose back to public, refresh page etc.  Make sure "Why is this not selected?" goes away and public repos should persist through install.
- You must install Third Party Tools (hue,elasticsearch,etc) after the base cluster is installed and after executing python command to stop ambari managing user groups:
<pre>python /var/lib/ambari-server/resources/scripts/configs.py -u admin -p admin -n [CLUSTER_NAME] -l [CLUSTER_FQDN] -t 8080 -a set -c cluster-env -k  ignore_groupsusers_create -v true</pre>
**** be sure to get the correct admin credentials, [CLUSTER_NAME], and [CLUSTER_FQDN] for command above
