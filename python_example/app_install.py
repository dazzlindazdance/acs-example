# import requests module
from os import error
import requests
from requests.auth import HTTPBasicAuth
import getpass
import json
import time
import sys
import argparse

import argparse
parser = argparse.ArgumentParser()

parser.add_argument("-s","--stack",type=str,help="Please Specify the stack your jwt relates to that you wish to install the app on.")
parser.add_argument("-t","--token",type=str,help="Please Specify the file containing the jwt that will allow you to install the app.")
parser.add_argument("-u","--username",type=str,help="Please Specify the Splunk.com username for authentication to appinspect, you will be prompted for the password.")
parser.add_argument("--staging", help="Flag to pass if this is a Splunk Cloud Staging Stack [Internal Use Only]", action="store_true")
parser.add_argument("--classic",help="Pass this flag if you are installing to a Splunk Cloud Classic Stack",action="store_true")
parser.add_argument("app_targz",type=str,help="The app you wish to vet and install")
args = parser.parse_args()

if args.stack:
    stack=args.stack
else:
    print("Stack Not Specified.")

if args.token:
    jwt_file=args.token
    # read stack Java Web Token from file, file defined as arg[3] presently until i can add some better flags to my script
    with open(jwt_file,'r') as file:
        stack_jwt = file.read().rstrip()
else:
    print("Token file not specified.")

if args.staging:
    acs_uri = "staging.admin.splunk.com"
    print("We will attempt to install the app to an internal staging stack of Splunk Cloud")
else:
    acs_uri = "admin.splunk.com"

if args.classic:
    appinspect_tags="private_app"
else:
    appinspect_tags="cloud,self-service"


if args.app_targz:
    appToInstall = args.app_targz
else:
    print("App not specified.")

if args.username:
    user = args.username
    password = getpass.getpass(prompt='Enter splunk.com password:',stream=None)
else:
    print("username not specified.")

# Making a authentication request and get token for appinspect
response = requests.get('https://api.splunk.com/2.0/rest/login/splunk', auth = HTTPBasicAuth(user, password))
response_json=json.loads(response.text)
if response_json["data"]["token"]:
    token=response_json["data"]["token"]
else:
    print("Probably an authentication error. Did you enter the right password?")


# submitting the app tarball to appinspect
appinspect_uri="https://appinspect.splunk.com/v1/app/validate"
files={'app_package': open(appToInstall,'rb')}
header={"Authorization": "Bearer "+token}
appinspect_response = requests.post(appinspect_uri,headers=header,files=files,data={"included_tags":appinspect_tags})
appinspect_response_json=json.loads(appinspect_response.text)

# grabbing status uri
appinspect_status=appinspect_response_json["links"][0]["href"]
appinspect_report=appinspect_response_json["links"][1]["href"]

# status check loop
appinspect_status_response = requests.get("https://appinspect.splunk.com"+appinspect_status,headers=header)
appinspect_status_json = json.loads(appinspect_status_response.text)

while appinspect_status_json["status"]=="PROCESSING":
    print("appinspect is currently processing vetting... [Sleeping for 30 seconds]")
    time.sleep(30)
    appinspect_status_response = requests.get("https://appinspect.splunk.com"+appinspect_status,headers=header)
    appinspect_status_json = json.loads(appinspect_status_response.text)
#print(appinspect_status_response.text)

# not it's been inspected we can work out what to do next...
if appinspect_status_json["status"]=="SUCCESS" and appinspect_status_json["info"]["failure"]>0:
    appinspect_report_response = requests.get("https://appinspect.splunk.com"+appinspect_report,headers=header)
    appinspect_report_json = json.loads(appinspect_report_response.text)
    # need to make the failure report write out to file as it overloads terminal buffer as too long...
    with open(appToInstall+"_failure_report.json",'w') as f:
        json.dump(appinspect_report_json,f)
        print("Failure Report written to: "+appToInstall+"_failure_report.json")
elif appinspect_status_json["status"]=="SUCCESS" and appinspect_status_json["info"]["failure"]==0:
    print("Starting Install...")
    #print("Token: "+token)
    #print("stack_jwt: "+stack_jwt)
    print("")
    # I am using an internal staging stack, please change URL to admin.splunk.com here when using production stack
    install_uri="https://"+acs_uri+"/"+stack+"/adminconfig/v2/apps"
    files={'package': open(appToInstall,'rb')}
    payload={'token':token}
    header={"Authorization": "Bearer "+stack_jwt,"ACS-Legal-Ack":"Y"}
    appinstall_response = requests.post(install_uri,headers=header,files=files,data=payload)
    appinstall_response_json=json.loads(appinstall_response.text)
    print(appinstall_response.text)
    # expected result 
    # {"label":"sample data","name":"subjective_sample_app1","package":"subjective_sample_app1-1.0.0.tar.gz","status":"installed","version":"1.0.0"}
    
else:
    print("To DO crap out here")
    #this is just going to be an escape incase we don't match on the above conditions, maybe remediated with error handling when i get that far...
