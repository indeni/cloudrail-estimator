from argparse import ArgumentParser
import stashy
import pprint
import re
import datetime

parser = ArgumentParser()
parser.add_argument("-s", "--server", dest="server", required=True,
                    help="The Bitbucket Server host URL, formatted as https://hostname:port", metavar="SERVER")
parser.add_argument("-u", "--username", dest="username", required=True,
                    help="The username to log into the Bitbucket Server with.")
parser.add_argument("-p", "--password", dest="password", required=True,
                    help="The password to log into the Bitbucket Server with.")
parser.add_argument("-o", "--output-file", dest="csv_output_file_path", default="cloudrail_bitbucket_contributors_estimate.csv",
                    help="The path to a CSV file where the results will be written, in addition to the stdout.")
parser.add_argument("-d", "--days-to-look-back", dest="days_lookback", default=90,
                    help="The number of days to look back for users in the git history.")
args = parser.parse_args()

# Make sure we can write to the CSV file
with open(args.csv_output_file_path, 'w') as f:
    f.write("repo_name,number_of_contributors\n")

server = stashy.connect(args.server, args.username, args.password)

print('Iterating over all projects')
projects_found = {}
repos_found = 0
pp = pprint.PrettyPrinter()

for project in server.projects.list():

    project_key = project['key']
    print(f'Project {project_key}: Iterating over all repositories...')
    projects_found[project_key] = {}

    for repo in server.projects[project_key].repos.list():
        repo_slug = repo['slug']
        print(f'Project {project_key}: Repo {repo_slug}: Looking for IaC...')

        for file in server.projects[project_key].repos[repo_slug].files():
            if file.endswith(".tf"):
                projects_found[project_key][repo_slug] = {}
                repos_found += 1
                print(f'Found Terraform file in this repo.')
                break

print(f"Found {repos_found} repos using IaC supported by Cloudrail")
print()

days_lookback = args.days_lookback
print(f"Looking through the last {days_lookback} days of commits for each of the repos to see how many authors were involved")

now = datetime.datetime.now()
oldest_timestamp = now - datetime.timedelta(days=days_lookback)
for project_key in projects_found:
    for repo_slug in projects_found[project_key]:
        commit_count = 0
        commits_within_timeframe = 0
        print(f'Project {project_key}: Repo {repo_slug}: Reviewing commit history...', end = "\r")

        default_branch_latest_commit = server.projects[project_key].repos[repo_slug].default_branch['latestCommit']
        for commit in server.projects[project_key].repos[repo_slug].commits(until=default_branch_latest_commit):
            commit_count += 1
            print(f'\rProject {project_key}: Repo {repo_slug}: Reviewing commit history... {commit_count} commits reviewed', end = "\r")
            timestamp = commit['authorTimestamp']
            if timestamp > oldest_timestamp.timestamp() * 1000:
                commits_within_timeframe += 1
                committer_email = commit.get('committer', {}).get('emailAddress', None)
                if committer_email:
                    projects_found[project_key][repo_slug][committer_email] = 'yes'

            # Bitbucket Server doesn't allow us to filter by date, so we need to iterate over all the commits.
            # However, this can take a very long time for large/busy repos. So instead, we'll cut off at some point.
            if commit_count > 3000:
                # If the majority of commits are ones within our timeframe, we continue. The moment
                # it isn't anymore, we stop.
                if (commits_within_timeframe * 1.0) / commit_count < 0.5:
                    break

        print() # Clear the last row that we keep writing over

        repo_committers = len(projects_found[project_key][repo_slug])
        print(f'Project {project_key}: Repo {repo_slug}: Found {repo_committers} committers...')
        with open(args.csv_output_file_path, 'a') as f:
            f.write(f"{project_key}/{repo_slug},{repo_committers}\n")
print()

print("Deduping list of committers across the repos mentioned...")
uniq_committers = set()
for project_key in projects_found:
    for repo_slug in projects_found[project_key]:
        for committer in projects_found[project_key][repo_slug]:
            uniq_committers.add(committer)

print(f"Scan complete! Found {len(uniq_committers)} unique committers in repositories with IaC. Results also in CSV: {args.csv_output_file_path}")
