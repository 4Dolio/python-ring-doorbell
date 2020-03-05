#!/usr/bin/python3.6
"""
 # For the love of God no one should use my code, this is my first pass at writing python, and this code disgusts even me.
 # This is built to be run in a linux bash shell and has colorized output
 # This could be a "Normal" hourly fetch of up to 120 clips per device, Just incase ask for one more hours worth, if 1 clip per minute.
 # This could crash during a loop cycle and get behind perhaps? So we use timeout to limit the total runtime to 900 or 1800 seconds.
 function RingFetchNewest { if [ ! $1 ] ; then echo Need a BaseDir Passed ; else RR=$1 ; while :;\
  do echo -e "\n\n\n:: $(date) $(uptime) Starting.\n";(cd; timeout 900 ./RingFetch.py $con $pas $RR 120 );\
  echo :: $(date) Finished.;RRdu=$(du -hs $RR/);echo ::: $(date) $RRdu Sleeping;sleep 1800;done ; fi ;} ; export -f RingFetchNewest #Download For 15min every 30min
 # RingFetchNewest /mnt/Ring | grep -v Skipped # do not print if we skipped a ton, but we lose some same line verbosity
 function RingFetchSpecific { if [ ! $1 ] ; then echo Need a BaseDir Passed ; else RR=$1 ; ( cd $RR/2020/ ; for MD in 202001{30..27}.{23..00} ;\
  do id=$(find .|grep $MD|tail -n1|cut -f3 -d\-|cut -f1 -d\.); echo -e ":: $MD\t"$(find .|sort|grep -c $MD)"\t"$id; if [ ! -z $id ] ;\
  then echo :: $(date) Trying older than $id ; (cd; timeout 1800 ./RingFetch.py $con $pas $RR 300 $id ) ; fi;
  echo :: $(date) Finished;RRdu=$(du -hs $RR/);echo ::: $(date) $RRdu Sleeping ; sleep 300 ; done) ;date ; fi ;} ; export -f RingFetchSpecific #For each hour get older than we have locally CatchUp
 # RingFetchSpecific /mnt/Ring | grep -v SkippedNOT # 
 # Still a bit unsure, if a pair of parallel tasks can run, seem to get errors if a second connection is attempted while one is running?
 # oauthlib.oauth2.rfc6749.errors.MissingTokenError: (missing_token) Missing access token parameter.
 function RingRecentDays { export Y=$(date +%Y); export m=$(date +%m); ( cd $1/$Y/ ; for MD in $Y$m$(date +%d -d -1day){23..00} $Y$m$(date +%d -d -2day){23..00} $Y$m$(date +%d -d -3day){23..00} ; do echo $MD ; done ) ;} ; export -f RingRecentDays
 function RingSyncByID   { echo :: $(date) Trying older than $1 ; (cd; timeout 300 ./RingFetch.py $con $pas $2 60 $1 ) ;} ; export -f RingSyncByID
 function RingSyncRecent { MDs=$(RingRecentDays $@); ( cd $1/$Y/;for MD in $MDs;do id=$(find .|grep $MD|tail -n1|cut -f3 -d\-|cut -f1 -d\.); echo -e ":: $MD\t"$(find .|sort|grep -c $MD)"\t"$id
  if [ ! -z $id ] ;then RingSyncByID $id $1 ;fi;done ) ;} ; export -f RingSyncRecent
 function RingSyncLatest { (cd; timeout 300 ./RingFetch.py $con $pas $1 60 )|grep -v Skipped ; echo :: $(date)" # "$(du -hs $1/) ;} ; export -f RingSyncLatest 
 # function RingSync { ;}
 # me@here:~# df -h;(while :; do for Y in 2019 2020 ; do (cd /mnt/Ring/$Y/;echo $(date) $(uptime) - $(du -hsc .|tail -n1); for M in $(ls -1|tail -n2);do cd $M;for D in $(ls -1);do  echo -e ":: $M.$D\t"$(find $D -type f|grep -c mp4)"\t" $(du -h $D|cut -f1) $(ls -lh $D|tail -n1); done;cd ..;done);done;echo;echo;sleep $(( 60*60 * 3 )) ; done ) # Count -n2 Months, sleep 3hours

# Original Pre oauth with python2.7x and <python3.5 are no longer supported: Current PreReqs:
## Need to upgrade from python3.5 to 3.6 Per https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get
## me@here:~$ sudo add-apt-repository ppa:deadsnakes/ppa # python3.6 Per https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get
## me@here:~$ sudo apt-get update ; sudo apt-get install python3.6 curl # curl for 3.6 pip fix
## me@here:~$ curl https://bootstrap.pypa.io/ez_setup.py -o - | sudo python3.6 && sudo python3.6 -m easy_install pip # Fix pip also for 3.6 
## me@here:~$ sudo pip install --upgrade pip # WARNING: You are using pip version 8.1.8/19.3.1/etc; however, version 20.0.1 is available.
## me@here:~$ sudo pip install pytz pathlib ring_doorbell git+https://github.com/tchellomello/python-ring-doorbell@master # Watch for v3.6s
"""

import json
import getpass
import sys
import os
import subprocess
from pathlib import Path
from ring_doorbell import Ring, Auth
from oauthlib.oauth2 import MissingTokenError
from pytz import timezone
MyTimeZone="US/Pacific" # Other examples?

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
#print(bcolors.HEADER + "Header: No active frommets remain. Continue?" + bcolors.ENDC)
#print(bcolors.OKBLUE + "OKBLUE: No active frommets remain. Continue?" + bcolors.ENDC)
#print(bcolors.OKGREEN + "OKGREEN: No active frommets remain. Continue?" + bcolors.ENDC)
#print(bcolors.WARNING + "Warning: No active frommets remain. Continue?" + bcolors.ENDC)
#print(bcolors.FAIL + "FAIL: No active frommets remain. Continue?" + bcolors.ENDC)
#print("This is the name of the script: ", sys.argv[0])
#print("Number of arguments: ", len(sys.argv))
arguments = len(sys.argv) - 1
#print("the script is called with %i arguments" % (arguments))
#print("The arguments are: " , str(sys.argv))

OlderThan=str() # Use for older_than= when fetching event list
if arguments == 5:
    OlderThan=(str(sys.argv[5])) #; print OlderThan
QueueDepth=str(10) # Use for limit= when fetching event list
if arguments >= 4:
    QueueDepth=(str(sys.argv[4])) #; print QueueDepth 
if arguments >= 3:
    BaseDir=(str(sys.argv[3])) # print BaseDir # #basedir="/mnt/Ring"
    password=(str(sys.argv[2])) # UnSafe, Change to read from a file or prompt
    username=(str(sys.argv[1])) # UnSafe, Change to read from a file or prompt
if arguments <= 2: # Require at least the first 3 arguments
    print(bcolors.WARNING + "Need Arguments UserName PassWord BaseDir and optionally QueueDepth and OlderThan etc..." + bcolors.ENDC)
    sys.exit(2) # Just exit now. # Got 2 but need 3 arguments
#print("Trying with " + username + " " + password + " BaseDir=" + BaseDir + " QueueDepth=" + QueueDepth + " OlderThan=" + OlderThan) # Print literall password
print("Trying with " + username + " " + "password" + " BaseDir=" + BaseDir + " QueueDepth=" + QueueDepth + " OlderThan=" + OlderThan) # Mask Password
if not os.path.exists(BaseDir):
    print(bcolors.WARNING + "The BaseDir does not appear to exist, aborting " + BaseDir + bcolors.ENDC)
    sys.exit(2) # Just exit now. # Because the 3rd argument is not a valid filesystem object

# New 2FA capable? oauth Method as of about 20191220
cache_file = Path(".RingFetch.token.cache") # Throw away this file to force authentication again.
def token_updated(token):
    cache_file.write_text(json.dumps(token))
def otp_callback():
    auth_code = input("2FA code: ")
    return auth_code
def main():
    if cache_file.is_file():
        auth = Auth("MyProject/1.0d", json.loads(cache_file.read_text()), token_updated)
    else:
# Comment or Un the following to be prompted or use what we have already set
#        username = input("Username: ")
#        password = getpass.getpass("Password: ")
        auth = Auth("MyProjectShared/1.0d", None, token_updated)
        try:
            auth.fetch_token(username, password)
        except MissingTokenError:
            auth.fetch_token(username, password, otp_callback())
    myring = Ring(auth)
    myring.update_data()			#;print(How To Print All Data)
    devices = myring.devices()			#;print(devices)
    doorbells = devices["doorbots"]		;print(doorbells)
    stickup_cams = devices["stickup_cams"]	#;print(stickup_cams)
    chimes = devices["chimes"]			#;print(chimes)
#    print( "myring.is_connected" ), # Not valid after python2.7
#    print( "myring.is_connected", end = '' )
#    print( myring.is_connected ) # True
## Would be nice to esplicitly test that we got connefcted,
#    p = subprocess.Popen(["sleep", "1"], stdout=subprocess.PIPE); output, err = p.communicate()#; print(output.rstrip(os.linesep)) # Sleep for BreakAbility
#    p = subprocess.Popen(["sleep", "1"], stdout=subprocess.PIPE); output, err = p.communicate()#; print(output.rstrip(os.linesep)) # Sleep for BreakAbility
    for acamera in list(stickup_cams + doorbells):
# limit on dev.account_id = 12345678 and print the Account ID: when connecting?
#    for event in acamera.history(limit=QueueDepth, older_than=6753104150123456789): # ['created_at'] #,'id'] # Older than example
        for event in acamera.history(limit=QueueDepth, older_than=OlderThan): # ['created_at'] #,'id']
#        filename='%s-%s-%s' % (acamera.name.replace(" ","_"), event['created_at'].astimezone(timezone('US/Pacific')).strftime("%Y%m%d.%H%M%S"), event['id']) # from pytz import timezone
# TODO: ... ... Need a new Ignore: state for cameras that match "-Driveway-" for the neighbors cam.
# #Or filter on the Account ID: 12345678 
            camname='%s' % acamera.name.replace(" ","_") # Sanitize Cam Names, of Spaces at least... ... 
            cliptime='%s' % event['created_at'].astimezone(timezone(MyTimeZone)).strftime("%Y%m%d.%H%M%S")
            clipyear='%s' % event['created_at'].astimezone(timezone(MyTimeZone)).strftime("%Y")
            clipmonth='%s' % event['created_at'].astimezone(timezone(MyTimeZone)).strftime("%m")
            clipday='%s' % event['created_at'].astimezone(timezone(MyTimeZone)).strftime("%d")
            clipid='%s' % event['id']
            foldername=BaseDir + "/" + clipyear + "/" + clipmonth + "/" + clipday
            p = subprocess.Popen(["mkdir", "-pv", foldername], stdout=subprocess.PIPE)
            output, err = p.communicate()
#	        print(output.rstrip(os.linesep)) # print the result of creating the container folder YYYY/MM/DD # Prints an empty line if dir already exists
            filename=cliptime + "-" + camname + "-" + clipid
                #print(filename)
            filepath=foldername + "/" + filename + ".mp4"
            print(bcolors.OKBLUE + "Fetchin " + filepath + bcolors.ENDC, end = '')
            sys.stdout.flush() # import sys # Force partial line to be printed
            print("\r", end = '') # Carrage return back to top of line for the results to be rewritten
            if not os.path.exists(filepath): # import os # Test that file does not exist yet
## Would like to esplicitly watch for a ^C BREAK from the parent, sometimes that gets ignored and can not abort.
                if acamera.recording_download(event['id'], filename=filepath):
                    print(bcolors.OKGREEN + "Success" + bcolors.ENDC + bcolors.BOLD, end = '')
#	                subprocess.call(["ls", "-lh", filepath]) # import subprocess # 
#	                print(subprocess.call(["ls", "-lh", filepath])) # import subprocess # Prints ls output and then "Success 0"(Return Code)?
                    p = subprocess.Popen(["ls", "-lh", filepath], stdout=subprocess.PIPE)
                    output, err = p.communicate()
#	                print("*** Running ls -l command ***\n")
#	                print(output), # Does a new line even though we used a comma, otherwise does two new lines, must have a \n within the output
#                    print(output.rstrip(os.linesep))
# This inline comment no longer works from py2.7 to py3.6 # similar to perl chomp to cleanup /r/n
#	                df=os.system("df -h / | grep /") # Not working right?
#	                print(df) # when attempting .rstrip(os.linesep) get error AttributeError: 'int' object has no attribute 'rstrip'
                    print(bcolors.UNDERLINE + bcolors.OKGREEN + "#" + bcolors.ENDC)
#                    print(acamera.recording_url(event['id'])) # Could print this into a filename.lnk instead to keep a shareable link? DEBUG
                else: # acamera.recording_download failed
                    print(bcolors.FAIL + "Failed-" + bcolors.ENDC)
                    print(acamera.recording_url(event['id']))
            else: # os.path.exists so skip
                print(bcolors.WARNING + "Skipped" + bcolors.ENDC)

#### See DebugAttributes
##    dev.update();print('Account ID: %s' % dev.account_id); print('Address:    %s' % dev.address)
##    print('Family:     %s' % dev.family);    print('ID:         %s' % dev.id)
##    print('Name:       %s' % dev.name);      print('Timezone:   %s' % dev.timezone)
##    print('Wifi Name:  %s' % dev.wifi_name); print('Wifi RSSI:  %s' % dev.wifi_signal_strength)
#### See DebugHistory
#### See DebugDownload
#### See CatchupOldEventsDownload
### ----------------------------------------------------------------------------------------------

### See DebugAllDevices
## All devices
#print( myring.devices ) 
### ----------------------------------------------------------------------------------------------

### See DebugAttributes
## Playing with the attributes
#for dev in list(myring.stickup_cams + myring.chimes + myring.doorbells):
#    # refresh data
#    dev.update()
#    print('Account ID: %s' % dev.account_id)
#    print('Address:    %s' % dev.address)
#    print('Family:     %s' % dev.family)
#    print('ID:         %s' % dev.id)
#    print('Name:       %s' % dev.name)
#    print('Timezone:   %s' % dev.timezone)
#    print('Wifi Name:  %s' % dev.wifi_name)
#    print('Wifi RSSI:  %s' % dev.wifi_signal_strength)
### ----------------------------------------------------------------------------------------------

### See DebugHistory
#for doorbell in myring.doorbells: # 'doorbells': [<RingDoorBell: ne353pl Front Door>]
#    # listing the last 15 events of any kind
#    for event in doorbell.history(limit=3):
#        print('Doorbell  %s' % doorbell)
#        print('ID:       %s' % event['id'])
#        print('Kind:     %s' % event['kind'])
#        print('Answered: %s' % event['answered'])
#        print('When:     %s' % event['created_at'])
#        print('--' * 50)
#        # get a event list only the triggered by motion
#        events = doorbell.history(kind='motion')
### ----------------------------------------------------------------------------------------------

### See DebugDownload
#for event in doorbell.history(limit=100, kind='ding'): # ['created_at'] #,'id']
##    print('%s-%s-%s' % (doorbell.name.replace(" ","_"), event['created_at'].strftime("%Y%m%d.%H%M%S"), event['id']) ) # All as one string
##    print('%s %s %s' % (vars(doorbell), event['created_at'].strftime("%Y%m%d.%H%M%S"), event['id']) ) # SPAM ALL of the objects properties

# Need to somehow use this to start a manual recording at specific times, such as Hours/6 ish.
# live_streaming_json
##    Return JSON for live streaming.

if __name__ == "__main__":
    main()
sys.exit(2) # New End of main function, cause the test.py uses it and I suck at python.

#
##