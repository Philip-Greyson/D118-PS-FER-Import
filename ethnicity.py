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

with open ('ethnicityLog.txt', 'w') as log:
    # create the connecton to the database
    with oracledb.connect(user=un, password=pw, dsn=cs) as con:
        with con.cursor() as cur:  # start an entry cursor
            with open('ethnicity.txt', 'w') as output:  # open the output file
                print("Connection established: " + con.version)
                #SQL Query credit to Richard Moeller https://groups.io/g/psug-il/message/1483
                cur.execute("WITH race AS \
                (SELECT STUDENTID, CASE WHEN COUNT(DISTINCT RACECD)>1 THEN '17' ELSE MAX(RACECD) END AS CODE FROM STUDENTRACE GROUP BY STUDENTID) \
                SELECT \
                    stu.STUDENT_NUMBER, ildemo.FER, DECODE(stu.FEDETHNICITY,1,11,race.CODE) \
                FROM \
                    students stu \
                    INNER JOIN race \
                        ON stu.ID = race.STUDENTID \
                    LEFT OUTER JOIN S_IL_STU_Demographics_X ildemo \
                        ON stu.DCID = ildemo.STUDENTSDCID \
                WHERE \
                    stu.ENROLL_STATUS IN (0,-1)")
                    # AND DECODE(stu.FEDETHNICITY,1,11,race.CODE) <> COALESCE(ildemo.FER,'00')")  # this makes it so it only includes them if they have a different value than what it should be.
                rows = cur.fetchall() #fetchall() is used to fetch all records from result set and store the data from the query into the rows variable

                # RECREATION OF SCRIPT BELOW BUT BROKEN OUT FOR BETTER TROUBLESHOOTING
                # cur.execute("SELECT STUDENTID, CASE WHEN COUNT(DISTINCT RACECD)>1 THEN '17' ELSE MAX(RACECD) END AS CODE FROM STUDENTRACE GROUP BY STUDENTID") # get each entry in the studentrace table, grouped by studentid. If they have more than one entry, they get code 17 otherwise they get the racecd code
                # studentRaces = cur.fetchall()
                # # print(studentRaces)
                # for student in studentRaces:
                #     try:
                #         stuID = int(student[0]) if student[0] else ''
                #         stuRaceCode = int(student[1]) if student[1] else ''# get the race code that will be used as their new FER code
                #         # take the studentID from above and find the matching students student_number, their federal ethnicity flag, and their current FER code
                #         cur.execute(f"SELECT students.student_number, students.fedethnicity, s_il_stu_demographics_x.fer, students.enroll_status FROM students INNER JOIN s_il_stu_demographics_x ON students.dcid = s_il_stu_demographics_x.studentsdcid WHERE students.id = {stuID}")
                #         rows = cur.fetchall()
                #         if rows:
                #             # print(rows)
                #             stuNumber = int(rows[0][0]) if rows[0][0] else ''# get the actual student number/id
                #             ethnicityFlag = int(rows[0][1]) if rows[0][1] else ''# get their federal ethnicity flag
                #             fer = int(rows[0][2]) if rows[0][2] else ''# get the current FER code
                #             enroll = int(rows[0][3]) if rows[0][1] else '' # get their enrollment status
                #             # print(f'StuNum: {stuNumber} | FER: {fer} | Race Code: {stuRaceCode} | Ethnicity: {ethnicityFlag} | StuID: {stuID}')
                #             if ethnicityFlag == 1:
                #                 ethnicityCode = 11 # if they are marked as hispanic from the ethnicity flag they get code 11
                #             else:
                #                 ethnicityCode = stuRaceCode
                #             # print(f'Flag: {ethnicityFlag} - {type(ethnicityFlag)} - Code: {ethnicityCode} - {type(ethnicityCode)}')
                #             if (enroll == -1 or enroll == 0) and (fer != ethnicityCode): # if they are pre-registerd or currently enrolled and the new code does not match their current FER entry
                #                 print(f'ACTION: Changing {stuNumber} from code {fer} to {ethnicityCode}')
                #         else:
                #             print(f'WARNING: No student entry found for ID {stuID}')
                #     except Exception as er:
                #         print(f'ERROR on student id {student[0]}: {er}')
                
                # print(rows)
                for student in rows:
                    try:
                        stuID = int(student[0])
                        ethnicityCode = int(student[2])
                        print(f'{stuID} \t {ethnicityCode}', file=output)
                        print(f'RESULT- ID:{stuID} | Current FER: {student[1]} | New Code: {ethnicityCode}', file=log)
                    except Exception as er:
                        print(f'ERROR on {student[0]} - {er}')
                        print(f'ERROR on {student[0]} - {er}', file=log)

    with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
        print('SFTP connection established')
        # print(sftp.pwd)  # debug to show current directory
        # print(sftp.listdir())  # debug to show files and directories in our location
        sftp.chdir('/sftp/ethnicity/')
        # print(sftp.pwd) # debug to show current directory
        # print(sftp.listdir())  # debug to show files and directories in our location
        # upload the file onto the sftp server
        sftp.put('ethnicity.txt')
        print("ACTION: Ethnicity code file placed on D118 SFTP server")
        print("ACTION: Ethnicity code file placed on D118 SFTP server", file=log)
