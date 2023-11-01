import requests
import re
import pandas as pd
import streamlit as st
from io import BytesIO

# Set your Personal Access Token here
token = "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"

# Helper function to fetch data
def fetch_data(url):
    headers = {
        "Authorization": f"token {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# Function to calculate the percentage of pull requests that were ultimately merged
def calculate_merged_pr_percentage(owner, repo_name):
    pulls_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
    pulls_data = fetch_data(pulls_url)
    if not pulls_data:
        return None

    merged_pr_count = 0
    total_pr_count = len(pulls_data)

    for pull in pulls_data:
        if 'merged' in pull and pull['merged']:
            merged_pr_count += 1

    if total_pr_count > 0:
        return (merged_pr_count / total_pr_count) * 100
    else:
        return 0

# Function to calculate the frequency of commits in all repos by the user
def calculate_commit_frequency(username):
    events_url = f"https://api.github.com/users/{username}/events"
    events_data = fetch_data(events_url)
    if not events_data:
        return None

    commit_count = 0

    for event in events_data:
        if event['type'] == 'PushEvent':
            commit_count += len(event['payload']['commits'])

    return commit_count

# Function to calculate the sum of forks and stars of the repos the user has contributed to
def calculate_forks_and_stars(username):
    user_contributions_url = f"https://api.github.com/users/{username}/events"
    user_contributions_data = fetch_data(user_contributions_url)
    if not user_contributions_data:
        return None

    forks_count = 0
    stars_count = 0

    for contribution in user_contributions_data:
        repo_url = contribution['repo']['url']
        repo_data = fetch_data(repo_url)
        if repo_data:
            forks_count += repo_data['forks']
            stars_count += repo_data['stargazers_count']

    return forks_count, stars_count

# Function to calculate the number of organizations the user is part of
def calculate_organization_count(username):
    orgs_url = f"https://api.github.com/users/{username}/orgs"
    orgs_data = fetch_data(orgs_url)
    if orgs_data:
        return len(orgs_data)
    return 0

# Function to collect contributor data
def collect_contributors_data(owner, repo_name):
    contributors_url = f"https://api.github.com/repos/{owner}/{repo_name}/contributors"
    contributors = fetch_data(contributors_url)
    if not contributors:
        st.error("Error: Unable to fetch contributors data.")
        return []

    contributor_data_list = []

    for contributor in contributors:
        contributor_login = contributor['login']
        contributor_url = f"https://api.github.com/users/{contributor_login}"
        contributor_data = fetch_data(contributor_url)
        if contributor_data:
            contributor_info = {
                "Contributor": contributor_data['login'],
                "Name": contributor_data['name'],
                "Followers": contributor_data['followers'],
                "Following": contributor_data['following'],
                "Public Repositories": contributor_data['public_repos'],
                "Contributions to Repository": contributor['contributions']
            }


            commit_frequency = calculate_commit_frequency(contributor_login)
            if commit_frequency is not None:
                contributor_info["Commit Frequency (All Repos)"] = commit_frequency

            forks_and_stars = calculate_forks_and_stars(contributor_login)
            if forks_and_stars is not None:
                forks_count, stars_count = forks_and_stars
                contributor_info["Total Forks of Repos Contributed To"] = forks_count
                contributor_info["Total Stars of Repos Contributed To"] = stars_count

            organization_count = calculate_organization_count(contributor_login)
            if organization_count is not None:
                contributor_info["Number of Organizations"] = organization_count

            contributor_data_list.append(contributor_info)
        else:
            st.warning(f"Error: Unable to fetch data for contributor {contributor_login}")

    return contributor_data_list

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# Streamlit app
def main():
    st.title("REPO SENTINEL 🤖")
    st.sidebar.write("This is Repo Sentinel, our guardian in the OSS environment")

    # Prompt the user to input the GitHub repository URL
    repository_url = st.text_input("Enter the GitHub repository URL (e.g., https://github.com/owner/repo):")

    if st.button("Search"):
        # Extract the owner's username and repository name from the URL
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', repository_url)
        if not match:
            st.error("Invalid GitHub repository URL. Please provide a valid URL.")
            return

        owner = match.group(1)
        repo_name = match.group(2)

        contributors_data = collect_contributors_data(owner, repo_name)

        if contributors_data:
            st.write("Contributors Information:")
            df = pd.DataFrame(contributors_data)
            st.dataframe(df)

            # Provide a download button for the Excel file
            excel_file_name = f'downloads/{repo_name}_contributors_data.xlsx'
            excel_data = to_excel(df)
            st.download_button(label='📥 Download Excel File',data=excel_data,key=excel_file_name,file_name=excel_file_name)

if __name__ == "__main__":
    main()
