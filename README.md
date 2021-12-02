# acs-example
Examples on how ACS can be used to manage configuration and deploy apps to Splunk Cloud
# Basic Python App Install Example
Python Script: app_install.py
This python script takes a bunch of args, run with -h to check them all...
This python script submits the app to appinspect, and if the app passes appinspect it will attempt to install the app on the specified cloud stack.
If the app fails appinspect then it will write the failure report out to a json file in the same directory as the app, subject to write permissions.

Example Usage:
python3 app_install.py --stack flash-monkey-02 --token stack_jwt.txt --username someuser@splunk.com --classic ../subjective-sample-app_102.tgz