#!/usr/bin/python
import sys
import os
import pwd
import syslog
import time
import paramiko
import StringIO

# ----- Global variables declaration ---------------------------
SERVER_LIST = "client_hosts"
DEST_DIR = "~/Ubuntu/task1/DEST"
LOG_FILE = "datacopyd.py.log"
SSH_ID_RSA = "~/.ssh/id_rsa_srv"
EXEC_TIME_LIMIT = 60*5
SCRIPT_FOLDER = os.path.dirname(sys.argv[0])
SERVER_LIST = SCRIPT_FOLDER + "/" + SERVER_LIST
ERROR_MESSAGE = ""
EXIT_CODE = 0
LOG_FILE = SCRIPT_FOLDER+"/"+LOG_FILE
SCRIPT = os.path.basename(sys.argv[0])
RUN_HELP = "Run command like this: \r\n"+SCRIPT+" /path_to_file/file_name or \
    \r\n"+SCRIPT+" /path_to_folder/folder_name"


class ConfigFile:
    def __init__(self, path):
        if (os.path.exists(path)):
            self.dir = os.path.dirname(path)
            self.file = os.path.basename(path)
            self.path = path

        else:
            print_log("Provides path" + path + "does not exist.")
            print_log("Please verify.")
            print_log("ConfigFile object is empty")

    def __str__(self):
        print self.dir+"/"+self.file

    def exists(self):
        return os.path.exists(self.path)
#        return os.access(self.path, os.F_OK)

    def isReadable(self):
        return os.access(self.path, os.R_OK)


class Host:
    def __init__(self, address, port=22):
        self.port = port
        self.host = address
        self.ssh_client = paramiko.SSHClient()

    def __str__(self):
        print self.host + ":" + self.port

    def getKey(self, key_file_name):
        f = open(os.path.expanduser(key_file_name), 'r')
        s = f.read()
        keyfile = StringIO.StringIO(s)
        return paramiko.RSAKey.from_private_key(keyfile)

    def sshClose(self):
        self.ssh_client.close()

    def isConnactable(self):
            self.sshConnect()
            data = self.execRemoteCommand('echo OK')
            self.sshClose()
            if (data[:2] == "OK"):
                return True
            else:
                return False

    def sshConnect(self):
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = self.getKey(SSH_ID_RSA)
        try:
            self.ssh_client.connect(self.host,
                                    port=self.port,
                                    username=pwd.getpwuid(os.getuid())[0],
                                    pkey=key)
        except paramiko.BadHostKeyException:
            print 'BadHostKeyException'
        except paramiko.AuthenticationException:
            print 'AuthenticationException'

    def execRemoteCommand(self, command):
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        return stdout.read() + stderr.read()


# ---- Helper functions definition ----------------------------
def print_log(message):
    if os.path.isfile(LOG_FILE) and os.access(LOG_FILE, os.R_OK):
        log_file = open(LOG_FILE, "a+")
        for line in message.split('\r\n'):
            log_file.write(time.strftime("%a %b %d %c %Z %Y") + " [" +
                           SCRIPT + "] " + line + "\n")
        log_file.close
    else:
        syslog.syslog("[" + SCRIPT + "]" + message)
        print message

# ---- Initial verifications  ---------------------------------
# Check if there were commandline arguments provided
if (len(sys.argv) == 1):
    print "\r\nPlease provide source file/folder as a command \
line agrument \r\n" + RUN_HELP + "\r\nAborting.\r\n"
    sys.exit(1)
# Check if logfile exists if not creates it otherwise truncates.
if not os.path.isfile(LOG_FILE):
    try:
        open(LOG_FILE, 'a').close()
    except IOError as ioe:
        print "I/O error({0}): {1}".format(ioe.errno, ioe.strerror)
else:
    open(LOG_FILE, 'w').close()
# Chenk if the destination folder exists, if not creates new one
if not os.path.isdir(DEST_DIR):
    try:
        os.makedirs(DEST_DIR)
    except OSError as e:
        print "I/O error({0}): {1}".format(ioe.errno, ioe.strerror)
        print_log("Destination folder can not be created. Check permissions.")
        sys.exit(3)

# ---- main Body goes here ------------------------------------
