#!/usr/bin/python
import sys
import os
import re
import pwd
import syslog
import time
import paramiko
# import tarfile
import StringIO
import hashlib
# ----- Global variables declaration ---------------------------
SERVER_LIST = "client_hosts"
DEST_DIR = "~/Ubuntu/task1/DEST"
DEST_DIR = os.path.expanduser(DEST_DIR)
LOG_FILE = "datacopy.py.log"
REMOTE_BACKUP = '~/backup.tar.gz'
REMOTE_BACKUP = os.path.expanduser(REMOTE_BACKUP)
LOCAL_BACKUP = DEST_DIR + "/" + os.path.basename(REMOTE_BACKUP)
LOCAL_BACKUP = os.path.expanduser(LOCAL_BACKUP)
SSH_ID_RSA = "~/.ssh/id_rsa_srv"
EXEC_TIME_LIMIT = 60*5
SCRIPT_FOLDER = os.path.dirname(sys.argv[0])
SERVER_LIST = SCRIPT_FOLDER + "/" + SERVER_LIST
ERROR_MESSAGE = ""
LOG_FILE = SCRIPT_FOLDER+"/"+LOG_FILE
SCRIPT = os.path.basename(sys.argv[0])
RUN_HELP = "Run command like this: \r\n"+SCRIPT+" /path_to_file/file_name or \
    \r\n"+SCRIPT+" /path_to_folder/folder_name"
regexp = {'hostPort': re.compile('^[0-9a-zA-z.-]+:[0-9]{1,5}\s*$'),
          'host': re.compile('^[0-9a-zA-z.-]+\s*$'),
          'commentLine': re.compile('^[#;].*')}


class HostList:
    def __init__(self, path):
        if (os.path.exists(path)):
            self.dir = os.path.dirname(path)
            self.file = os.path.basename(path)
            self.path = path
            self.hostset = set([])
            with open(self.path) as listFile:
                for line in listFile:
                    line = line[:-1] if line[-1] == os.linesep else line
                    if regexp['host'].match(line):
                        line = line[:-1] if line[-1] == '.' else line
                        self.hostset.add(Host(line, 22))
                    elif regexp['hostPort'].match(line):
                        line = line.split(':')
                        line[0] = line[0][:-1] if line[0][-1] == '.' else line[0]
                        self.hostset.add(Host(line[0], line[1]))
        else:
            print_log("Provides path" + path + "does not exist.")
            print_log("Please verify.")
            print_log("HostList object is empty")

    def __str__(self):
        s = "Host list is a unordered set created based on "
        s += os.path.abspath(self.path) + os.linesep
        s += "It is represented with:" + os.linesep
        for host in self.hostset:
            s += host.__str__() + os.linesep
        return s

    def exists(self):
        return os.path.exists(self.path)
#        return os.access(self.path, os.F_OK)

    def isReadable(self):
        return os.access(self.path, os.R_OK)


class Host:
    def __init__(self, address, port=22):
        self.port = port
        self.address = address
        self.chan = None
        self.ssh_client = paramiko.SSHClient()
        self.sftp = None
        self.isConnected = False

    def openChannel(self):
        self.chan = self.transport.open_session()

    def __str__(self):
        return self.address + ":" + str(self.port)

    def getKey(self, key_file_name):
        f = open(os.path.expanduser(key_file_name), 'r')
        s = f.read()
        keyfile = StringIO.StringIO(s)
        return paramiko.RSAKey.from_private_key(keyfile)

    def sshClose(self):
        if (self.isConnected):
            self.ssh_client.close()
            self.sftp.close()
            print_log("SSH connection has been closed.")

    def isConnectableViaSSH(self):
        if not self.isConnected:
            self.sshConnect()
        if self.isConnected:
            data = self.execRemoteCommand('echo OK')
            self.sshClose()
            if (data[:2] == "OK"):
                return True
            else:
                return False
        else:
            return False

    def sshConnect(self):
        if not self.isConnected:
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            key = self.getKey(SSH_ID_RSA)
            try:
                self.ssh_client.connect(self.address,
                                        port=self.port,
                                        username=pwd.getpwuid(os.getuid())[0],
                                        pkey=key,
                                        timeout=5)
                self.transport = self.ssh_client.get_transport()
                self.sftp = self.transport.open_sftp_client()
                self.isConnected = True
                print_log("SSH connection has been established.")
                return True
            except (paramiko.BadHostKeyException, paramiko.AuthenticationException,
                    paramiko.ssh_exception.NoValidConnectionsError) as e:
                print_log(e.strerror)
                return False
        else:
            return True

    def execRemoteCommand(self, command):
        if self.isConnected:
            self.openChannel()
            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                return stdout.read() + stderr.read()
            except (paramiko.SSHException) as e:
                print_log("SSH error({0}): {1}".format(e.errno, e.strerror))
        else:
            print_log("The host ssh channel is not opened.")
            return False

    def remoteFileExists(self, file):
        if (self.isConnected):
            self.openChannel()
            try:
                self.sftp.stat(file)
                return True
            except IOError as e:
                print_log(e.strerror)
                return False
        else:
            print_log("The host is not connected via SSH.")
            return False

    def copyRemoteFile(self, filename):
        if self.remoteFileExists(filename):
            tar_res = False
            command = "sudo tar -czpf " + REMOTE_BACKUP + ' ' + \
                      filename + " > /dev/null && echo ok"
            tar_res = self.execRemoteCommand(command)
            if (tar_res[:2] == "ok"):
                print_log("Reamote backup file " + REMOTE_BACKUP + " created.")
                self.openChannel()
                fileExists(LOCAL_BACKUP)
                local_file_data = open(LOCAL_BACKUP, "rb").read()
                remote_file_data = self.sftp.open(REMOTE_BACKUP).read()
                self.sftp.get(remote_file_data, local_file_data, callback=None)
                if fileExists(LOCAL_BACKUP):
                    self.openChannel()
                    md1 = self.getRemoteFileMD5Hash(REMOTE_BACKUP)
                    md2 = hashlib.md5(LOCAL_BACKUP).hexdigest()
                    if (md1 == md2):
                        print_log("Bachup file transferred SUCCESSFULLY.")
                        return True
                    else:
                        print_log("Remote backup file hash differs from local one.")
                        print_log("It is recommended to run backup procedure again for the host.")
                        return False
                else:
                    print_log("An Error occured while transferring a bachup archive file")
                    print_log("Try retransfer it manually")
                    return False
        else:
            return False

    def getRemoteFileMD5Hash(self, filename):
        if (self.isConnected):
            sftpFile = paramiko.sftp_file.SFTPFile(self.sftp,
                                                   filename,
                                                   mode='r',
                                                   bufsize=-1)
            return sftpFile.check("md5")
        else:
            print_log("Could not get remote file hash...")
            return None


# ---- Helper functions definition ----------------------------
def print_log(message):
    if os.path.isfile(LOG_FILE) and os.access(LOG_FILE, os.R_OK):
        log_file = open(LOG_FILE, "a+")
        for line in message.split(os.linesep):
            log_file.write(time.strftime("%c %Z %Y") + " [" +
                           SCRIPT + "] " + line + "\n")
        log_file.close
    else:
        syslog.syslog("[" + SCRIPT + "]" + message)
        print message


def fileExists(file):
    # Check if file exists if not creates it otherwise truncates.
    if (not os.path.isfile(file)):
        try:
            open(file, 'a').close()
        except IOError as ioe:
            print_log("I/O error({0}): {1}".format(ioe.errno, ioe.strerror))
            return False
    else:
        open(file, 'w').close()
        return True
# ---- Initial verifications  ---------------------------------
# Check if there were commandline arguments provided
if (len(sys.argv) == 1):
    print_log(os.linesep + "Please provide source file/folder as a command \
              line agrument" + os.linesep + RUN_HELP + os.linesep +
              "Aborting." + os.linesep)
    sys.exit(1)

# Check if there were more than one commandline arguments provided
if (len(sys.argv) > 2):
    print_log(os.linesep + "Please provide source file/folder as a command \
line agrument" + os.linesep + RUN_HELP + os.linesep + "Aborting." + os.linesep)
    sys.exit(1)

# Check if logfile exists if not creates it otherwise truncates.
fileExists(LOG_FILE)
paramiko.util.log_to_file(LOG_FILE + ".1")
# Chenk if the destination folder exists, if not creates new one
if not os.path.isdir(DEST_DIR):
    try:
        os.makedirs(DEST_DIR)
    except OSError as ioe:
        print "I/O error({0}): {1}".format(ioe.errno, ioe.strerror)
        print_log("Destination folder can not be created. Check permissions.")
        sys.exit(3)

# ---- main Body goes here ------------------------------------
initTime = time.time()
hostList = HostList(SERVER_LIST)
if (len(hostList.hostset) > 0):
    i = 0
    for host in hostList.hostset:
        i += 1
        mesg = "===> Processing host [{0:0" + str(len(str(len(hostList.hostset)))) + "d}"
        mesg = mesg.format(i)
        mesg += "/" + '{0:d}'.format(len(hostList.hostset))
        mesg += "] " + host.address + ":" + str(host.port)
        print_log(mesg)
        host.sshConnect()
        if host.isConnected:
            result = False
            result = host.copyRemoteFile(sys.argv[1])
            print result
#             while not result:
#                 if (time.time()-initTime > EXEC_TIME_LIMIT):
#                     print_log("Execution time exceded provided time limit of" +
#                               EXEC_TIME_LIMIT + " seconds." + os.linesep +
#                               "Abotring." + os.linesep)
#                     sys.exit(10)
        else:
            print_log("Aborting.")
        host.sshClose()
