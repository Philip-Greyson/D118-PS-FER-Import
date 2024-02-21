# D118-PS-FER-Import

Script to take a student's race data in PowerSchool, and translate it into the codes required for the Illinois FER field. Uses a great SQL script done by Richard Moeller found [here](https://groups.io/g/psug-il/message/1483), massive credit to him, I just packaged it up into a python script so it could output to a file daily and be import into PowerSchool via AutoComm.

## Overview

The script is pretty short and sweet, and basically just repackages the data from Richard Moeller's SQL query and outputs it to a .txt file in tab delimited format which is then uploaded to our local SFTP server. This is then used to import into the relevant field in PowerSchool via AutoComm import.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- D118_SFTP_USERNAME
- D118_SFTP_PASSWORD
- D118_SFTP_ADDRESS

These are fairly self explanatory, and just relate to the usernames, passwords, and host IP/URLs for PowerSchool and the local SFTP server. If you wish to directly edit the script and include these credentials or to use other environment variable names, you can.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

**As part of the pysftp connection to the output SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

You will also need a SFTP server running and accessible that is able to have files written to it in the directory /sftp/ethnicity/ or you will need to customize the script (see below). That setup is a bit out of the scope of this readme.
In order to import the information into PowerSchool, a scheduled AutoComm job should be setup, that uses the managed connection to your SFTP server, and imports into student_number, and the IL demographics FER field, using tab as a field delimiter, LF as the record delimiter with the UTF-8 character set.

## Customization

This is a pretty specific basic script for our district based on what is needed for the IL demographics FER field, and is likely going to be different for other states or schools requiring a different SQL query. If you are in IL and can use it "as is", the only thing you might want to change:

- `OUTPUT_FILE_NAME` and `OUTPUT_FILE_DIRECTORY`define the file name and directory on the SFTP server that the file will be exported to. These combined will make up the path for the AutoComm import.
