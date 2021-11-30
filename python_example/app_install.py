# import requests module
import requests
from requests.auth import HTTPBasicAuth
import getpass
import json
import time
import sys

# current expected input until i add useful helper and flags:
#
# python3 app_install.py <stack> <app_installer> <file_with_stack_jwt>
#
# python3 app_install.py flash-monkey-02 ../subjective-sample-app_100.tgz stack_jwt.txt
stack=sys.argv[1]
appToInstall=sys.argv[2]


# read stack Java Web Token from file, file defined as arg[3] presently until i can add some better flags to my script
jwt_file=sys.argv[3]
with open(jwt_file,'r') as file:
    stack_jwt = file.read().rstrip()

user = input("Enter splunk.com username:")
print(user)
password = getpass.getpass(prompt='Enter password:',stream=None)
print(password)

# Making a authentication request and get token for appinspect
response = requests.get('https://api.splunk.com/2.0/rest/login/splunk', auth = HTTPBasicAuth(user, password))
response_json=json.loads(response.text)
token=response_json["data"]["token"]


# submitting the app tarball to appinspect
appinspect_uri="https://appinspect.splunk.com/v1/app/validate"
files={'app_package': open(appToInstall,'rb')}
header={"Authorization": "Bearer "+token}
appinspect_response = requests.post(appinspect_uri,headers=header,files=files,data={"included_tags":"private_app"})
# The above tags are for Classic stack , please replace with "cloud,self-service" when using Victoria
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
print(appinspect_status_response.text)

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
    print("Token: "+token)
    print("stack_jwt: "+stack_jwt)
    print("")
    # I am using an internal staging stack, please change URL to admin.splunk.com here when using production stack
    install_uri="https://staging.admin.splunk.com/"+stack+"/adminconfig/v2/apps"
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
