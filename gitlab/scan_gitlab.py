from argparse import ArgumentParser
import pprint
import re
import datetime
import gitlab

parser = ArgumentParser()
parser.add_argument("-s", "--server", dest="server", 
                    help="The GitLab server URL, formatted as https://hostname:port", metavar="SERVER", default="https://gitlab.com")
parser.add_argument("-u", "--private-token", dest="private_token",
                    help="The private token to log into GitLab with.")
parser.add_argument("-p", "--oauth-token", dest="oauth_token",
                    help="The oauth token to log into GitLab with.")
parser.add_argument("-o", "--output-file", dest="csv_output_file_path", default="cloudrail_gitlab_contributors_estimate.csv",
                    help="The path to a CSV file where the results will be written, in addition to the stdout.")
parser.add_argument("-d", "--days-to-look-back", dest="days_lookback", default=90,
                    help="The number of days to look back for users in the git history.")
parser.add_argument("-f", "--project-search", dest="project_search",
                    help="Use a GitLab-supported search criteria to focus only on specific projects.")
args = parser.parse_args()

# Make sure we can write to the CSV file
with open(args.csv_output_file_path, 'w') as f:
    f.write("repo_name,number_of_contributors\n")

if args.private_token:
    gl = gitlab.Gitlab(args.server, private_token=args.private_token)
elif args.oauth_token:
    gl = gitlab.Gitlab(args.server, oauth_token=args.oauth_token)
else:
    print('This script is designed for authenticated login. Please provide either --private-token or --oauth-token.')
    exit(1)

if args.project_search:
    print('Iterating over projects matching the search criteria')
else:
    print('Iterating over all projects. This may result in a large list, consider using --project-search.')
projects_found = {}
repos_found = 0
pp = pprint.PrettyPrinter()
project_key_to_id = {}

for project in gl.projects.list(search=args.project_search, membership=True, as_list=False):

    project_key = project.name_with_namespace
    project_key_to_id[project_key] = project.get_id()
    print(f'Project {project_key}: Looking for IaC in the repo...')

    for file in project.repository_tree(recursive=True, as_list=False):
        if file['name'].endswith(".tf"):
            projects_found[project_key] = {}
            print(f'Found Terraform file in this repo.')
            break

print(f"Found {len(projects_found)} projects using IaC supported by Cloudrail")
print()

days_lookback = int(args.days_lookback)
print(f"Looking through the last {days_lookback} days of commits for each of the repos to see how many authors were involved")

now = datetime.datetime.now()
oldest_timestamp = now - datetime.timedelta(days=days_lookback)

for project_key in projects_found:
    commit_count = 0
    commits_within_timeframe = 0
    print(f'Project {project_key}: Reviewing commit history...', end = "\r")

    for commit in gl.projects.get(project_key_to_id[project_key]).commits.list(since=oldest_timestamp, as_list=False):
        commit_count += 1
        print(f'\rProject {project_key}: Reviewing commit history... {commit_count} commits reviewed', end = "\r")
        committer_email = commit.attributes['author_email']
        if committer_email:
            projects_found[project_key][committer_email] = 'yes'

    print() # Clear the last row that we keep writing over

    repo_committers = len(projects_found[project_key])
    print(f'Project {project_key}: Found {repo_committers} committers...')
    with open(args.csv_output_file_path, 'a') as f:
        f.write(f"{project_key},{repo_committers}\n")
print()

print("Deduping list of committers across the repos mentioned...")
uniq_committers = set()
for project_key in projects_found:
    for committer in projects_found[project_key]:
        uniq_committers.add(committer)

print(f"Scan complete! Found {len(uniq_committers)} unique committers in repositories with IaC. Results also in CSV: {args.csv_output_file_path}")
