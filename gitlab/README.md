The code here is used with GitLab. It requires Python 3.8 and later. It will connect to the GitLab Server API using a private token or oauth (you can use either option, but must use one of them). 

The script will connect to either GitLab.com (if you use that) or your local server, list all projects, find the ones that have IaC in them,
and count how many users have committed to the relevant repositories over the past X days (90 by default).
If the same user contributed to multiple repositories, they will be counted only once. This script
uses the users' email addresses to achieve this behavior. There is no data sent to Indeni/Cloudrail in this script,
it is all executed locally with API calls to the GitLab server.

The output is saved to a CSV file to make it easy to analyze in Excel or a similar application.

NOTE:
If you have many projects accessible to you (which is especially true if you're searching on GitLab.com, as all public 
projects are accessible), use the `--project-search` flag.

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
python scan_gitlab.py --private-token glpat-something
```
OR
```
python scan_gitlab.py --oauth-token something
```
