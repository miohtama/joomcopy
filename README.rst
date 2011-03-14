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

Syntax::

        joomcopy [SCP path to remote Joomla! installation] [target directory]


Example::

        ./joomcopy yourusername@server.com:/path/to/joomla .

*target directory* defaults to *.*

Configuration options
=======================

Remote Joomla! configuration.php is rewritten for local computer.
You can override any options from it.

TODO: How.

File copy
===============

rsync command is used to copy the remote Joomla! files to local host.
The copy is incremental, so it is faster after the first run.

MySQL
======

MySQL database is dropped and reloaded from a remote dump on every run.
Currently master localhost MySQL account credentials are hardcoded in the file.

Apache
=======

Apache virtualhost file is created for Ubuntu/Debian. This file
is also configured to /etc/hosts, so that you can use
a spoofed domain name to access the instance.

The virtual host server name is the same as the database name.

So if you have Joomla! database ``myjoomla``, you can access the virtual host 
locally::

        http://myjoomla

Other
------

This script is still pretty much under development.

Author
------

Mikko Ohtamaa <mikko at mfabrik dot com>

http://twitter.com/moo9000
