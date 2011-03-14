#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

        Copy remote Joomla! site to local host over SSH.

        This script is designed for local development purposes only and
        is not security safe for doing any kind of production deploments.

"""

__author__ = "Mikko Ohtamaa <mikko@mfabrik.com>"
__license__ = "BSD"
__docformat__ = "epytext"

import re
import os, sys

# SCP path to the Joomla installation
source_path = None # All components together as one string
ssh_user = None
ssh_server = None
ssh_path = None

# The target where we will dump the Joomla
# Note: Must be absolute path, as this is used by Apache configs also
target_path = os.getcwd()

# Copy all Joomla! files (False to copy only configuration.php)
copy_all_files = True

# Create Apache virtual host entry (Ubuntu/Debian only) - needs sudo
create_vhost = True

#remote_tmp_folder = "/tmp"

# What values we are interested in, need to mutate in Joomla! configuration.php.
remote_config_items = {
        #  MySQL credentials
        "db" : None,
        "password" : None,
        "user" : None
}

# Local defaults for overridden Joomla! config values.
# Local configuration.php will have values from this dict, overriding the remote configuration.php
# Useful for database accounts, SMTP settings etc. which could be computer specific.
# If no local overrides available, use ones from the remote.
local_config_items = {

}

# MySQL config items needed for MySQL admin access
mysql_master_settings = {
        "user" : "root",
        "password" : "admin"
}

# Apache configuration file template for hooking up the new instance with Apache
VIRTUALHOST_TEMPLATE = """
<VirtualHost *:80>
	ServerAdmin webmaster@localhost

	DocumentRoot %(target_path)s

	<Directory />
		Options FollowSymLinks
		AllowOverride None
	</Directory>

	<Directory %(target_path)s>
		Options Indexes FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	</Directory>

	ErrorLog ${APACHE_LOG_DIR}/%(instance_name)s.error.log

	# Possible values include: debug, info, notice, warn, error, crit,
	# alert, emerg.
	LogLevel debug

	CustomLog ${APACHE_LOG_DIR}/%(instance_name)s combined

</VirtualHost>
"""

class Fail(Exception):
        """ Our wonderful exception """


def split_ssh_target(target):
        """
        Split SSH command line target parameter to parts.
        """
        try:
                user, remote = target.split("@")
        except:
                raise Fail("SSH missing user spec:" + target)

        try:
                server, path = remote.split(":")
        except:
                raise Fail("SSH path/server cannot be figured out: %s, %s" % (target, remote))

        return user, server, path



def sexec(command, fail=True):
        """ Locally execute a command.

        Custom exec wrapper.
        """
        val = os.system(command)        
        if val != 0 and fail:
                raise Fail("Failed to execute command %s" % command)

def sudoexec(command, fail=True):
        """ Execute command with local root priviledges.

        """

        command = "sudo -S " + command
        print "Need sudo priviledges to execute:" + command      
        val = os.system(command)        
        if val != 0 and fail:
                raise Fail("Failed to execute command %s" % command)


def rexec(command, fail=True):
        """ Remote exec a command over SSH """

def scp(source, target):
        """ Run SCP.
        """
        
        # Use Max. compression level
        # http://blog.mfabrik.com/2011/03/02/scp-file-copy-with-on-line-compression/
        sexec("scp -C -o CompressionLevel=9 -r %s %s" % (source, target))

def rsync(source, target):
        """ Run rsync copy.

        rsync -a copies only modified files and keeps the modified timestamp intact.
        """
                
        # Don't mind about rsync errors - they often happen when n00b Joomla!
        # devs edit files as root, messing up the UNIX file perms 
        sexec("rsync --compress-level=9 -av %s/* %s" % (source, target), fail=False)
      
def copy_config(path):
        """
        Remote copy configuration.

        @param path: Remote path to Joomla! installation
        """

        copied = os.path.join(target_path, "configuration.php.remote")

        scp(path + "/configuration.php", copied)
        return copied

def copy_files(path):
        """ Copy Joomla! files from the remote site to a local.

        Make copy of a Joomla! config.
        
        @param path: Remote path to Joomla! installation        
        """
        scp(path, target_path)

def mutate_config(config_file, output_file):
        """ Parse the configuration.php and extract some information out of it
        to the local variables.

        Output a version with our local configuration variables.

        @raise Fail: If we don't speak PHP well enough

        @param config_file: local path to a configuration.php
        """        


        input = open(config_file, "rt")
        output = open(output_file, "wt")


        def parse_config(line):
            """ Parse Joomla! configuration.php line """

                        
            parts = re.split("[$'=;]", line)
            # print parts
            # ['var ', 'lifetime ', ' ', '999', '', '']

            if len(parts) < 4 or parts[1] == "":
                raise Fail("Could not parse configuration.php line %s" % line)                
                
            return parts[1].strip(), parts[3]

        def output_config_value(key, value):
            print >> output, "\t var $%s = '%s'"% (key, value)


        for line in input:

                managed = False

                for item in remote_config_items.keys():
                        # Our super duper PHP parser -
                        # this will be part needing most bugfixes
                        line = line.strip()
                        if line == "":
                                continue
                        if line.startswith("<?php") or line.startswith("?>"):
                                continue

                        if line.startswith("//"):
                                continue

                        if line.startswith("class") or line.startswith("}"):
                                continue

                        key, value = parse_config(line)
                        remote_config_items[key] = value

                        if key in local_config_items:
                                value = local_config_items[key]
                        output_config_value(key, value)
                        local_config_items[key] = value
                                        
                        managed = True
                        break

                if not managed:
                        # Pass the line through unmodified
                        print >> output, line 
                                

        input.close()
        output.close()
        
def process_config(remote_config_copy):
        """ 

        @param remote_config_copy: A path to a copied remot configuration.php
        """
        target = os.path.join(target_path, "configuration.php")
        mutate_config(remote_config_copy, target)

def check_mysql_dump(input):
        """ See if MySQL dump looks ok """

        f = open(input, "rt")
        ok = False
        for line in f:
           # Marker string must be present in the file
           if "DROP TABLE" in line:
                ok = True
                break                

        f.close()
        if not ok:
                raise Fail("Looks like MySQL dump output is not good:" + input)
        

def dump_remote_mysql():
        """ Dump the remote MySQL database.

        Run remote pipe, so that SSH outputs the mysqldump output to our popen()
        which then writes it to a file.

        @return: Local path to MySQL dump file
        """     

        # Prepare string template variables
        opts = remote_config_items.copy()
        opts["source_path"] = source_path
        opts["dump_file"] = "dump.sql"        
        opts["ssh_server"] = ssh_server
        opts["ssh_user"] = ssh_user
           
        template = 'ssh %(ssh_user)s@%(ssh_server)s -C -o CompressionLevel=9 mysqldump -u%(user)s --password="%(password)s" --add-drop-table %(db)s > %(dump_file)s'
        cmd = template % opts
        print "Executing MySQL dump command:" + cmd

        value = os.system(cmd)
        if value != 0:
                raise Fail("Failed to execute:" + cmd)

        # Check that dump contents look ok
        return opts["dump_file"]

def exec_mysql(cmd, connect_database):
        """ Execute a local MySQL shell command 

        TODO: Add stop on errors / ignore errors

        @param cmd: MySQL shell command to run

        @param connect_database: Set to true if the command is meant to run in the context of existing database
        """

        if connect_database:        
                opts = local_config_items.copy()
        else:
                opts = mysql_master_settings.copy()
        
        opts["command"] = cmd
        opts["database_string"] = "-D%(db)s" % opts if connect_database else ""
        template = 'mysql -u%(user)s --password="%(password)s" %(database_string)s -e "%(command)s"' % opts
        cmd = template % opts
        print "Executing MySQL command:" + cmd
        val = os.system(cmd)
        
                                
def create_local_database(dump_file):
        """ Load remote file to a local database. """
        
        # Reconstruct the database
        exec_mysql("drop database %s" % local_config_items["db"], connect_database=False)
        exec_mysql("create database %s" % local_config_items["db"], connect_database=False)
        exec_mysql("GRANT ALL ON %(db)s.* TO '%(user)s'@'localhost' identified by '%(password)s';" % local_config_items, connect_database=False)

        # Load dump into MySQL
        exec_mysql("source %s" % dump_file, connect_database=True)


def create_apache_vhost():
     """ Create apache virtual host config file (Ubuntu/Debian).

     TODO: Make possible to override instance - currently database name is used.
     """
     opts = local_config_items.copy()
     opts["instance_name"] = opts["db"] 
     opts["target_path"] = target_path
     opts["virtualhost_config_file"] = os.path.join(target_path, "virtualhost.conf")

        
     # Create vhost file as a local user
     output = VIRTUALHOST_TEMPLATE % opts
     f = open(opts["virtualhost_config_file"], "wt")
     print >> f, output
     f.close()

     # Copy vhost file to the system config
     target_vhost_file = "/etc/apache2/sites-enabled/%s" % opts["instance_name"]

     sudoexec("cp %s %s" % (opts["virtualhost_config_file"], target_vhost_file))
     sudoexec("apache2ctl graceful") # Restart apache

def create_etc_hosts_entry():
        """
        Make /etc/hosts spoofed domain name, so that we can access the instance directly from the browser.

        Check if the entry already exists in which case skip the manipulation.
        """        

        opts = local_config_items.copy()
        opts["instance_name"] = opts["db"] 
        
        # Check if have added this line already to /etc/hosts
        found = False
        for line in open("/etc/hosts"):
                if opts["instance_name"] in line:
                        found = True
                        break

        if not found:
             # Need some magic with escaping all shell quotes
             # http://www.soundunreason.com/InkWell/?p=1946
             cmd = """sudo -S sh -c 'echo "127.0.0.1 %(instance_name)s" >> /etc/hosts'""" % opts
             val = os.system(cmd)                
             if val > 0:
                raise Fail("Could not exec sudo command:" + cmd)

def fix_permissions():
        """ Fix file permissions for apache.

        TODO: Think about adding the www-data user to have rights to read local user files here. HOW?
        """
        sudoexec("chmod -R a+rwx %s" % target_path)                        

def main():
        global source_path

        print "Usage: joomcopy.py yourusername@server.com:~/folder"

        source_path = sys.argv[1]
        if source_path.endswith("/"):
                source_path = source_path[0:-1]

        global ssh_user, ssh_server, ssh_path
        ssh_user, ssh_server, ssh_path = split_ssh_target(source_path)

        # Copy Joomla! tree
        if copy_all_files:
            rsync(source_path, target_path)

        # Copy and manipulate Joomla! configuration file
        remote_config_copy = copy_config(source_path)
        process_config(remote_config_copy)
        
        # Copy and load MySQL database (credentials read from the config file above)
        dump_file = dump_remote_mysql()
        check_mysql_dump(dump_file)
        create_local_database(dump_file)

        if create_vhost:
            create_apache_vhost()
            create_etc_hosts_entry()      
            fix_permissions()                          
        
if __name__ == "__main__":
        main()

