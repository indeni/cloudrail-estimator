The code here is used with Jenkins. It requires Python 3.8 and later. It will connect to the Jenkins API using a username and 
password. You can also use a token instead of a password (useful especially in cases where SAML is used to authenticate).

To generate an API token:
* Log into Jenkins
* Click on your name at the top right, then Configure.
* Generate an API token and use it as the password parameter for this script.

The script will connect to your Jenkins server, list all jobs and review their Console Output looking for potential usage of 
infrastructure-as-code that is supported by Cloudrail. For those jobs that seem to be using IaC, Cloudrail will attempt to 
calculate how often they run.

The output is saved to a CSV file to make it easy to analyze in Excel or a similar application.