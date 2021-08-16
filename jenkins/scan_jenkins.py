from argparse import ArgumentParser
import jenkins
import pprint
import re

parser = ArgumentParser()
parser.add_argument("-s", "--server", dest="server", required=True,
                    help="The Jenkins host URL, formatted as https://hostname:port", metavar="SERVER")
parser.add_argument("-u", "--username", dest="username", required=True,
                    help="The username to log into the Jenkins server with.")
parser.add_argument("-p", "--password", dest="password", required=True,
                    help="The password (or API token) to log into the Jenkins server with.")
parser.add_argument("-o", "--output-file", dest="csv_output_file_path", default="cloudrail_jenkins_jobs_estimate.csv",
                    help="The path to a CSV file where the results will be written, in addition to the stdout.")
args = parser.parse_args()

# Make sure we can write to the CSV file
with open(args.csv_output_file_path, 'w') as f:
    f.write("job_name,history_in_ms,build_count,annualized\n")

server = jenkins.Jenkins(args.server, args.username, args.password)
user = server.get_whoami()
version = server.get_version()
print('Verified %s connected to Jenkins v%s' % (user['fullName'], version))

print('Scanning for jobs with the use of terraform in them...')
jobs_with_cloudrail_supported_iac = {}
re_terraform_tools = re.compile("(terraform|terratest|terragrunt)")

for job in server.get_jobs(folder_depth=None):
    job_name = job['fullname']
    print(f"Job {job_name}: scanning builds' console outputs for terraform")

    builds_reviewed = 0
    for build in server.get_job_info(job_name).get('builds', {}):
        console_output = server.get_build_console_output(job_name, build['number'])
        if (re_terraform_tools.search(console_output)):
            print(f'Job {job_name}: uses terraform')
            jobs_with_cloudrail_supported_iac[job_name] = {}
            break
        
        # Stop after a few builds
        builds_reviewed += 1
        if builds_reviewed >= 3:
            print(f'Job {job_name}: stopped looking for terraform after {builds_reviewed} latest builds analyzed, assuming job doesn\'t use terraform')
            break
print(f"Found {len(jobs_with_cloudrail_supported_iac)} jobs using IaC supported by Cloudrail")
print()

print("Estimating builds per year...")
total_annualized = 0
for job_name in jobs_with_cloudrail_supported_iac:
    job_info = server.get_job_info(name=job_name, depth=0, fetch_all_builds=True)
    job_builds = job_info['builds']
    latest_build_number = job_builds[0]['number']
    oldest_build_number = job_builds[-1]['number']

    latest_build_timestamp = server.get_build_info(job_name, latest_build_number)['timestamp']
    oldest_build_timestamp = server.get_build_info(job_name, oldest_build_number)['timestamp']

    history_in_ms = latest_build_timestamp - oldest_build_timestamp
    history_in_days = history_in_ms / 1000 / 60 / 60 / 24
    history_build_count = len(job_builds)

    annualized_build_count = (365 * 24 * 60 * 60 * 100 / history_in_ms * history_build_count) if history_in_ms > 0 else 0

    if history_in_days < 30:
        print(f'Job {job_name}: WARNING: Have less than 30 days of build history for job')
    
    print(f'Job {job_name}: Based on {round(history_in_days, 1)} days of data, estimating {round(annualized_build_count, 3)} Cloudrail executions per year for this job')
    with open(args.csv_output_file_path, 'a') as f:
        f.write(f"{job_name},{history_in_ms},{history_build_count},{annualized_build_count}\n")

    total_annualized += annualized_build_count


print(f"Scan complete! For {args.server} estimating {round(total_annualized, 0)} executions of Cloudrail per year. Results also in CSV: {args.csv_output_file_path}")
