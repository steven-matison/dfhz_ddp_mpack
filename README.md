# dfhz_ddp_mpack
<h1>DFHz Demo Data Platform for Ambari</h1>


#### Management Pack Installaion
<pre>ambari-server install-mpack --mpack=https://github.com/steven-dfheinz/dfhz_ddp_mpack/raw/master/ddp-ambari-mpack-0.0.0.1-0.tar.gz --verbose
ambari-server restart</pre>


#### Management Pack Removal
<pre>ambari-server uninstall-mpack --mpack-name=ddp-ambari-mpack
ambari-server restart</pre>
