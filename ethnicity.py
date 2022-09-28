# Tiny script to take a student's race data and change it
# into the format needed for import into the IL.FER field
# Puts the output file on our SFTP server for autocomm into PS

# SQL query from Richard Moeller, all credit to him
# https://groups.io/g/psug-il/message/1483

# importing module
import oracledb  # needed for connection to PowerSchool (oracle database)
import os  # needed to get environment variables
import pysftp  # needed for sftp file upload

un = 'PSNavigator'  # PSNavigator is read only, PS is read/write
# the password for the PSNavigator account
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD')
# the IP address, port, and database name to connect to
cs = os.environ.get('POWERSCHOOL_PROD_DB')

#set up sftp login info
sftpUN = os.environ.get('D118_SFTP_USERNAME')
sftpPW = os.environ.get('D118_SFTP_PASSWORD')
sftpHOST = os.environ.get('D118_SFTP_ADDRESS')
# connection options to use the known_hosts file for key validation
cnopts = pysftp.CnOpts(knownhosts='known_hosts')

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
print("SFTP Username: " + str(sftpUN) + " |SFTP Password: " + str(sftpPW) + " |SFTP Server: " + str(sftpHOST)) #debug so we can see what credentials are being used

# create the connecton to the database
with oracledb.connect(user=un, password=pw, dsn=cs) as con:
    with con.cursor() as cur:  # start an entry cursor
        with open('ethnicity.txt', 'w') as output:  # open the output file
            print("Connection established: " + con.version)
            #SQL Query credit to Richard Moeller https://groups.io/g/psug-il/message/1483
            cur.execute("WITH race AS (SELECT STUDENTID, CASE WHEN COUNT(DISTINCT RACECD)>1 THEN '17' ELSE MAX(RACECD) END AS CODE FROM STUDENTRACE GROUP BY STUDENTID) SELECT stu.STUDENT_NUMBER, ildemo.FER, DECODE(stu.FEDETHNICITY,1,11,race.CODE) FROM students stu INNER JOIN race ON stu.ID = race.STUDENTID LEFT OUTER JOIN S_IL_STU_Demographics_X ildemo ON stu.DCID = ildemo.STUDENTSDCID WHERE stu.ENROLL_STATUS IN (0,-1) AND DECODE(stu.FEDETHNICITY,1,11,race.CODE) <> COALESCE(ildemo.FER,'00')")
            rows = cur.fetchall() #fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
            for student in rows:
                stuID = int(student[0])
                ethnicityCode = int(student[2])
                print(str(stuID) + '\t' + str(ethnicityCode), file=output)

with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
    print('SFTP connection established')
    # print(sftp.pwd)  # debug to show current directory
    # print(sftp.listdir())  # debug to show files and directories in our location
    sftp.chdir('/sftp/ethnicity/')
    # print(sftp.pwd) # debug to show current directory
    # print(sftp.listdir())  # debug to show files and directories in our location
    # upload the file onto the sftp server
    sftp.put('ethnicity.txt')
    print("Ethnicity code file placed on D118 SFTP server")
