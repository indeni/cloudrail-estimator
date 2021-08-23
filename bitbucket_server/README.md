The code here is used with Bitbucket Server (not Cloud!). It requires Python 3.8 and later. It will connect to the Bitbucket Server API using a username and password. 

The script will connect to your Bitbucker Server, list all repositories, find the ones that have IaC in them,
and count how many users have committed to the relevant repositories over the past X days (90 by default).
If the same user contributed to multiple repositories, they will be counted only once. This script
uses the users' email addresses to achieve this behavior.

IMPORTANT:
This script may be slow, especially in the part where it counts the number of contributors. The reason
is that the Bitbucket Server API does not allow a request to filter by date (for example, last 90 days)
and so the entire history of commits needs to be reviewed. This causes I/O load on the server and 
considerable network traffic.

The output is saved to a CSV file to make it easy to analyze in Excel or a similar application.

## Usage

1. Install Python 3.8 if you don't have it already.

2. Create a venv:
```
python -m venv venv
```

3. Switch into the virtual env:
```
. venv/bin/activate
```

4. Install the required Python requirements:
```
pip install -r requirements.txt
```

5. Run the script:
```
python scan_bitbucket_server.py --server 'https://mybitbucket.server.com/' --username 'myuser' --password 'api_token_or_password'
```