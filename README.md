
#### Add from zabbix_agentd.conf "UserParameter" in zabbix_agentd.conf zabbix_agent:
- **github**/zabbix_agentd.conf

#### Import zabbix template:

- **github**/Template Lsi RAID Controller.xml


#### Copy bash script:

- **github**/lsi-raid.sh in /opt/zabbix/lsi-raid.sh

#### Chmod and Chown
- chmod -R 750 /etc/zabbix/
- chown -R root:zabbix /etc/zabbix/

#### Check bash script(Out json):
- ```/etc/zabbix/adaptec-raid.sh lld ad```

#### Add from zabbix_agentd.conf "UserParameter" in zabbix_agentd.conf zabbix_agent:
- **github**/zabbix_agentd.conf

#### Add in /etc/sudoers
zabbix ALL=(root) NOPASSWD: /etc/zabbix/lsi-raid.sh

#### Import zabbix template:
- **github**/Template Lsi RAID Controller.xml

<br/>
