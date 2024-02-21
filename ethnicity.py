"""Script to take student race data and output format needed for IL.FER field to a file for import into PowerSchool.

https://github.com/Philip-Greyson/D118-PS-FER-Import


SQL query from Richard Moeller, all credit to him: https://groups.io/g/psug-il/message/1483
Outputs the result of the SQL to a file and uploads it to our local SFTP server for import into PowerSchool.

needs oracledb: pip install oracledb --upgrade
needs pysftp: pip install pysftp --upgrade
"""

# importing module
import datetime  # used to get current date for course info
import os  # needed to get environment variables
from datetime import *

import oracledb  # needed for connection to PowerSchool (oracle database)
import pysftp  # needed for sftp file upload

DB_UN = os.environ.get('POWERSCHOOL_READ_USER')  # username for read-only database user
DB_PW = os.environ.get('POWERSCHOOL_DB_PASSWORD')  # the password for the database account
DB_CS = os.environ.get('POWERSCHOOL_PROD_DB')  # the IP address, port, and database name to connect to

#set up sftp login info
SFTP_UN = os.environ.get('D118_SFTP_USERNAME')  # username for the d118 sftp server
SFTP_PW = os.environ.get('D118_SFTP_PASSWORD')  # password for the d118 sftp server
SFTP_HOST = os.environ.get('D118_SFTP_ADDRESS')  # ip address/URL for the d118 sftp server
CNOPTS = pysftp.CnOpts(knownhosts='known_hosts')  # connection options to use the known_hosts file for key validation

OUTPUT_FILE_NAME = 'ethnicity.txt'
OUTPUT_FILE_DIRECTORY = '/sftp/ethnicity/'

print(f"Database Username: {DB_UN} |Password: {DB_PW} |Server: {DB_CS}")  # debug so we can see where oracle is trying to connect to/with
print(f'SFTP Username: {SFTP_UN} | SFTP Password: {SFTP_PW} | SFTP Server: {SFTP_HOST}')  # debug so we can see what info sftp connection is using


if __name__ == '__main__':  # main file execution
    with open ('ethnicityLog.txt', 'w') as log:
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with open('ethnicity.txt', 'w') as output:  # open the output file
            # create the connecton to the database
            try:
                with oracledb.connect(user=DB_UN, password=DB_PW, dsn=DB_CS) as con:
                    with con.cursor() as cur:  # start an entry cursor
                        print(f'INFO: Connection established to PS database on version: {con.version}')
                        print(f'INFO: Connection established to PS database on version: {con.version}', file=log)
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
                        rows = cur.fetchall()  # fetchall() is used to fetch all records from result set and store the data from the query into the rows variable

                        # print(rows)
                        for student in rows:
                            try:
                                stuID = int(student[0])
                                ethnicityCode = int(student[2])
                                print(f'{stuID}\t{ethnicityCode}', file=output)
                                print(f'RESULT- ID:{stuID} | Current FER: {student[1]} | New Code: {ethnicityCode}', file=log)
                            except Exception as er:
                                print(f'ERROR while processing student {student[0]}: {er}')
                                print(f'ERROR while processing student {student[0]}: {er}', file=log)
            except Exception as er:
                print(f'ERROR while connecting to PowerSchool or doing query: {er}')
                print(f'ERROR while connecting to PowerSchool or doing query: {er}', file=log)
        try:
            with pysftp.Connection(SFTP_HOST, username=SFTP_UN, password=SFTP_PW, cnopts=CNOPTS) as sftp:
                print(f'INFO: SFTP connection to D118 at {SFTP_HOST} successfully established')
                print(f'INFO: SFTP connection to D118 at {SFTP_HOST} successfully established', file=log)
                # print(sftp.pwd)  # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                sftp.chdir(OUTPUT_FILE_DIRECTORY)
                # print(sftp.pwd) # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                # upload the file onto the sftp server
                sftp.put(OUTPUT_FILE_NAME)
                print("INFO: Ethnicity code file placed on D118 SFTP server")
                print("INFO: Ethnicity code file placed on D118 SFTP server", file=log)
        except Exception as er:
                print(f'ERROR while connecting to D118 SFTP server: {er}')
                print(f'ERROR while connecting to D118 SFTP server: {er}', file=log)

        endTime = datetime.now()
        endTime = endTime.strftime('%H:%M:%S')
        print(f'INFO: Execution ended at {endTime}')
        print(f'INFO: Execution ended at {endTime}', file=log)
