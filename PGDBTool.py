import os
import sys
from PyQt4 import QtGui, QtCore, uic
from pprint import pprint
import time
import datetime
import string
import random
import subprocess
import pexpect

# OS Agnostic file current directory of script
curdir = os.path.dirname(os.path.abspath(__file__))
budir = os.path.join(curdir, "Backup")
tmpdir = os.path.join(curdir, "tmp")
server_list_file = curdir + "/server_list.txt"

# ALTERNATE METHOD OS Agnostic file current directory of script
# curdir = str(os.path.dirname(os.path.realpath(__file__)))
#
# Load the UI settings
curdir_form_class = curdir + "/mainwindow.ui"
form_class = uic.loadUiType(curdir_form_class)[0]

# Used to convert file lists to an array, var is typically a string ("src" or "dest")
def server_file_to_array():
    str_file_list = str(open(server_list_file).read())
    server_list_array = str_file_list.split("\n")
    return server_list_array

server_list_array = server_file_to_array()

class MainWindow(QtGui.QMainWindow, form_class):
    # Initialize t\he main window
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.update_servere_lists(server_list_array)
        ## Begin Copy Tab
        self.Copy_Btn_ServerAdd.clicked.connect(self.Copy_AddServerList)
        # Setup the 'Source DB Name = Destination DB Name' checkbox
        self.Copy_Line_DestDB.setEnabled(False)
        self.Copy_Check_DBSameName.stateChanged.connect(self.Check_DBNames)
        self.Copy_Line_SrcDB.textChanged.connect(self.DestDBUpdate)
        # Set the run button
        self.Copy_Btn_RunCopy.clicked.connect(self.CopyDB)
        ## End Copy Tab
        ## Begin Backup Tab
        self.Backup_Btn_ServerAdd.clicked.connect(self.Backup_AddServerList)
        self.Backup_Btn_RunBackup.clicked.connect(self.BackupDB)
        ## End Backup Tab
        ## Begin Restore Tab
        self.Restore_Btn_File.clicked.connect(self.selectFile)
        self.Restore_Btn_ServerAdd.clicked.connect(self.Restore_AddServerList)
        self.Restore_Btn_RunRestore.clicked.connect(self.RestoreDB)
        ## End Restore Tab

    
    def selectFile(self):
        self.Restore_Line_File.setText(QtGui.QFileDialog.getOpenFileName())
    
    # Variables fed to this function will be outputed in the Txt_Status field
    def update_status(self, var):
        self.Txt_Status.append(str(var))
        self.Txt_Status.repaint()
        time.sleep(.5)

    def get_time(self):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%Hh-%Mm-%Ss')
        return st
    
    # Appends a line of text to the target file, then repopulates the list based on the new file
    # This should allow multiple users to append servers simultaneously.
    def update_servere_lists(self,  server_list_array):
        self.Copy_list_Src.clear()
        self.Copy_list_Dest.clear()
        self.Backup_list_Src.clear()
        self.Restore_list_Dest.clear()
        self.Copy_list_Src.addItems(server_list_array)
        self.Copy_list_Dest.addItems(server_list_array)
        self.Backup_list_Src.addItems(server_list_array)
        self.Restore_list_Dest.addItems(server_list_array)
    
    def Copy_AddServerList(self):
        server_new = str(self.Copy_Line_ServerAdd.text())
        if len(server_new) > 0:
            with open(server_list_file, "a") as myfile:
                txt_append = ("\n" + server_new)
                myfile.write(txt_append)
            server_list_array = server_file_to_array()
            self.update_servere_lists(server_list_array)
        else:
            self.update_status("Please enter a server address in the adjacent box")

    def Backup_AddServerList(self):
        server_new = str(self.Backup_Line_ServerAdd.text())
        if len(server_new) > 0:
            with open(server_list_file, "a") as myfile:
                txt_append = ("\n" + server_new)
                myfile.write(txt_append)
            server_list_array = server_file_to_array()
            self.update_servere_lists(server_list_array)
        else:
            self.update_status("Please enter a server address in the adjacent box")

    def Restore_AddServerList(self):
        server_new = str(self.Restore_Line_ServerAdd.text())
        if len(server_new) > 0:
            with open(server_list_file, "a") as myfile:
                txt_append = ("\n" + server_new)
                myfile.write(txt_append)
            server_list_array = server_file_to_array()
            self.update_servere_lists(server_list_array)
        else:
            self.update_status("Please enter a server address in the adjacent box")

    def Check_DBNames(self):
        if self.Copy_Check_DBSameName.isChecked() == True:
            self.Copy_Line_DestDB.setEnabled(False)
            self.DestDBUpdate() # Call a function to update the destination db name if the box becomes checked
        else:
            self.Copy_Line_DestDB.setEnabled(True)

    # Update the Destination DB field to the Source DB Field, under the right conditions and when triggered
    def DestDBUpdate(self):
        if self.Copy_Check_DBSameName.isChecked() == True:
            new_text = str(self.Copy_Line_SrcDB.text())
            self.Copy_Line_DestDB.setText(new_text)      

    # Interract with the pg_dump command, supply password and check for faulure
    def auth_dump(self, child, pw):
        try:
            self.update_status("Initiating connection with host")
            child.expect('Password:', timeout=7)
            child.sendline(pw + "\n")
        except:
            self.update_status("ERROR: Could not connect to host.")
            return "failed"
        try:
            child.expect (['%',pexpect.EOF])
            print child.before
            if "password authentication failed" in child.before:
                self.update_status("ERROR: Authentication failed")
                return "failed"
            else:
                self.update_status("SUCCESS.  Database saved to sql file")
                return "success"
        except:
            self.update_status("An unknown error has occured")
            return "failed"

    # Interract with createdb command, supply password and check for failure
    def auth_create(self, child, pw):
        try:
            self.update_status("Initiating connection with host")
            child.expect("Password", timeout=7)
            child.sendline(pw + "\n")
        except:
            self.update_status("ERROR: Could not connect to host.")
            return "failed"
        try:
            child.expect (['%',pexpect.EOF])                                     
            if "Password" in child.before:
                self.update_status("ERROR: Authentication failed")
                return "failed"
            elif "already exists" in child.before:
                self.update_status("ERROR: That database already exists")
                return "failed"
            else:
                self.update_status("SUCCESS: Template database created")
                return "success"
        except:
            self.update_status("An unknown error has occured")
            return "failed"
      
    def auth_pop(self, child, pw):
        try:
            self.update_status("Initiating connection with host")
            child.expect("[Pp]assword", timeout=7)
            child.sendline(pw + "\n")
        except:
            self.update_status("ERROR: Could not connect to host.")
            return "failed"
        try:
            child.expect (['%',pexpect.EOF])                                     
            if "Password" in child.before:
                self.update_status("ERROR: Authentication failed")
                return "failed"
            elif "failed" in child.before:
                self.update_status("ERROR: Authentication failed")
                return "failed"
            else:
                self.update_status("SUCCESS: Template database populated")
                return "success"
        except:
            self.update_status("An unknown error has occured")
            return "failed"

    def get_dump_cmd(self, src_host, src_acc, copyfile, src_db):
        dump_cmd = "pg_dump --host=%s --username=%s -b -o -O -f %s %s" % (src_host, src_acc, copyfile, src_db)
        return dump_cmd
    
    def get_create_cmd(self, dest_host, dest_acc, dest_db):
        create_cmd = "createdb --host=%s --username=%s -E UTF8 -T template0 %s" % (dest_host, dest_acc, dest_db)
        return create_cmd
    
    def get_pop_cmd(self, dest_host, dest_acc, copyfile, dest_db):
        pop_cmd = "psql -q --host=%s --username=%s -f %s %s" % (dest_host, dest_acc, copyfile, dest_db)
        return pop_cmd
    
    def check_sql_file(self, sqlfile):
        if os.path.isfile(sqlfile) == True:
            self.update_status("SQL file has been saved to " + sqlfile)
        else:
            self.update_status("SQL copy of the database has failed to save")
    
    # Copies database when the button is pressed, based on user inputed variables
    def CopyDB(self):
        src_acc = str(self.Copy_Line_SrcAcc.text()) # Get value for source username, check if empty
        if len(src_acc) == 0:
            self.update_status("No source account entered.  Copy process will not run.")
            return
        src_pass = str(self.Copy_Line_SrcPass.text()) # Get value for source pass, check if empty
        if len(src_pass) == 0:
            self.update_status("No source password entered.  Copy process will not run.")
            return
        try: # Get value for source server, check if no selection
            src_host = str(self.Copy_list_Src.currentItem().text())
        except AttributeError:
            self.update_status("No source server selected.  Copy proccess will not run")
            return
        src_db = str(self.Copy_Line_SrcDB.text()) # Get value for source db, check if empty
        if len(src_db) == 0:
            self.update_status("No source database entered.  Copy process will not run.")
            return
        dest_acc = str(self.Copy_Line_DestAcc.text()) # Get value for destination account, check if empty
        if len(dest_acc) == 0:
            self.update_status("No destination account entered.  Copy process will not run.")
            return
        dest_pass = str(self.Copy_Line_DestPass.text()) # Get value for destination password, check if empty
        if len(dest_pass) == 0:
            self.update_status("No destination password entered.  Copy process will not run.")
            return
        try: # Get value for destination server, check if no selection
            dest_host = str(self.Copy_list_Dest.currentItem().text())
        except AttributeError:
            self.update_status("No destination server selected.  Copy proccess will not run")
            return
        dest_db = str(self.Copy_Line_DestDB.text()) # Get value for destination db, check if empty
        if len(dest_db) == 0:
            self.update_status("No destination database entered.  Copy process will not run.")
            return
        self.update_status("\n\n--- BEGINNING COPY PROCESS ---")
        st = self.get_time()
        copyfile = os.path.join(budir, "%s_%s_%s.sql" % (src_db, st, src_host))
        # pg_dump command
        self.update_status("\n--- Copying database into sql file ---")
        dump_cmd = self.get_dump_cmd(src_host, src_acc, copyfile, src_db)
        childdump = pexpect.spawn(dump_cmd)
        result_dump = self.auth_dump(childdump, src_pass)
        if result_dump == "failed":
            self.update_status("Copy halted")
            return      
        # createdb command
        self.update_status("\n--- Creating the template database ---")
        create_cmd = self.get_create_cmd(dest_host, dest_acc, dest_db)
        childcreate = pexpect.spawn(create_cmd)
        result_create = self.auth_create(childcreate, dest_pass)
        if result_create == "failed":
            self.update_status("Copy halted")
            return
        # psql command to import sql file data into empty database
        self.update_status("\n--- Populating template database with SQL file ---")
        pop_cmd = self.get_pop_cmd(dest_host, dest_acc, copyfile, dest_db)
        childpop = pexpect.spawn(pop_cmd)
        result_pop = self.auth_pop(childpop, dest_pass)
        if result_pop == "failed":
            self.update_status("Copy halted")
            return
        self.update_status("COPY PROCESS FINISHED")
      
    def BackupDB(self):
        src_acc = str(self.Backup_Line_SrcAcc.text()) # Get value for source username, check if empty
        if len(src_acc) == 0:
            self.update_status("No source account entered.  Backup process will not run.")
            return
        src_pass = str(self.Backup_Line_SrcPass.text()) # Get value for source pass, check if empty
        if len(src_pass) == 0:
            self.update_status("No source password entered.  Backup process will not run.")
            return
        try: # Get value for source server, check if no selection
            src_host = str(self.Backup_list_Src.currentItem().text())
        except AttributeError:
            self.update_status("No source server selected.  Backup proccess will not run")
            return
        src_db = str(self.Backup_Line_SrcDB.text()) # Get value for source db, check if empty
        if len(src_db) == 0:
            self.update_status("No source database entered.  Backup process will not run.")
            return
        self.update_status("\n\n--- BEGINNING BACKUP PROCESS ---")
        st = self.get_time()
        backupfile = os.path.join(budir, "%s_%s_%s.sql" % (src_db, st, src_host))
        self.update_status("\n--- Copying database into sql file ---")
        dump_cmd = self.get_dump_cmd(src_host, src_acc, backupfile, src_db)
        childdump = pexpect.spawn(dump_cmd)
        result_dump = self.auth_dump(childdump, src_pass)
        self.update_status("Backup created at: \n" + backupfile)
        if result_dump == "failed":
            self.update_status("Copy halted")
            return
        self.update_status("BACKUP PROCESS FINISHED")
        
    def RestoreDB(self):
        dest_acc = str(self.Restore_Line_DestAcc.text()) # Get value for destination account, check if empty
        if len(dest_acc) == 0:
            self.update_status("No destination account entered.  Restore process will not run.")
            return
        dest_pass = str(self.Restore_Line_DestPass.text()) # Get value for destination password, check if empty
        if len(dest_pass) == 0:
            self.update_status("No destination password entered.  Restore process will not run.")
            return
        try: # Get value for destination server, check if no selection
            dest_host = str(self.Restore_list_Dest.currentItem().text())
        except AttributeError:
            self.update_status("No destination server selected.  Restore proccess will not run")
            return
        dest_db = str(self.Restore_Line_DestDB.text()) # Get value for destination db, check if empty
        if len(dest_db) == 0:
            self.update_status("No destination database entered.  Restore process will not run.")
            return
        restorefile = str(self.Restore_Line_File.text()) # Get value for destination db, check if empty
        if len(restorefile) == 0:
            self.update_status("No input file entered.  Restore process will not run.")
            return
        self.update_status("\n\n--- BEGINNING RESTORE PROCESS ---")
        # createdb command
        self.update_status("\n--- Creating the template database ---")
        create_cmd = self.get_create_cmd(dest_host, dest_acc, dest_db)
        childcreate = pexpect.spawn(create_cmd)
        result_create = self.auth_create(childcreate, dest_pass)
        if result_create == "failed":
            self.update_status("Restore halted")
            return
        # psql command to import sql file data into empty database
        self.update_status("\n--- Populating template database with SQL file ---")
        pop_cmd = self.get_pop_cmd(dest_host, dest_acc, restorefile, dest_db)
        childpop = pexpect.spawn(pop_cmd)
        result_pop = self.auth_pop(childpop, dest_pass)
        if result_pop == "failed":
            self.update_status("Restore halted")
            return
        self.update_status("RESTORE PROCESS FINISHED")



	

app = QtGui.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
