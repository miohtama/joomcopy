--------
joomcopy
--------

Copy Joomla! site from a remote server to local development computer.

Features
---------

This script will perform the cumbersome manual tasks of

* Getting remote MySQL dump

* Copying over Joomla! files

* Changing Joomla! config file for local computer

* Loading MySQL dump to a local MySQL database

* Setting Apache virtualhost and /etc/hosts spoofed name for local development

Requirements
--------------

* Remote server has mysqldump installed

* Local computer has SSH, SCP, rsync installed

Usage
------

./joomcopy yourusername@server.
