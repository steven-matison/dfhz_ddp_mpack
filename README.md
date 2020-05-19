# dfhz_ddp_mpack
<h1>DFHz Demo Data Platform for Ambari</h1>

#### Install Ambari From MOSGA RPMS:
<pre>yum install https://makeopensourcegreatagain.com/rpms/ambari-server-2.7.5.0-0.x86_64.rpm -y
yum install https://makeopensourcegreatagain.com/rpms/ambari-agent-2.7.5.0-0.x86_64.rpm -y
ambari-server setup -s</pre>

#### Management Pack Installaion
<pre>ambari-server install-mpack --mpack=https://github.com/steven-dfheinz/dfhz_ddp_mpack/raw/master/ddp-ambari-mpack-0.0.0.2-0.tar.gz --verbose
ambari-server restart</pre>


#### Management Pack Removal
<pre>ambari-server uninstall-mpack --mpack-name=ddp-ambari-mpack
ambari-server restart</pre>
