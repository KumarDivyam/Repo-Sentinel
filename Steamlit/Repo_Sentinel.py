import requests
import re
import pandas as pd
import streamlit as st
from io import BytesIO
import time

# Set your Personal Access Token here
token = ""

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

            organization_count = calculate_organization_count(
                contributor_login)
            if organization_count is not None:
                contributor_info["Number of Organizations"] = organization_count

            contributor_data_list.append(contributor_info)
        else:
            st.warning(
                f"Error: Unable to fetch data for contributor {contributor_login}")

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
    st.set_page_config(
        page_title='REPO SENTINEL', page_icon='computer')
    hide_st_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_st_style, unsafe_allow_html=True)
    st.write(
        '<style>div.block-container{padding-top:0rem;}</style>', unsafe_allow_html=True)

    style = "<style>h2 {text-align:;}</style>"
    st.markdown(style, unsafe_allow_html=True)
    st.columns(3)[1].header("REPO SENTINEL 🤖")
    st.divider()
    st.markdown('#####')
    st.subheader('About our Tool')
    st.markdown(f'''
        ######
            Repo Sentinel Web App :
            Repo Sentinel serves as a vital guardian, fortifying the integrity and security 
            of open-source repositories, empowering users, and safeguarding the OSS 
            ecosystem.This tool empowers users and organizations to make informed choices 
            when engaging with OSS, thereby enhancing the overall robustness of the
            open-source ecosystem.
        ''', unsafe_allow_html=True)
    st.divider()

    st.subheader('Test your Repository here ⬇️')
    st.sidebar.write(
        "This is Repo Sentinel, our guardian in the OSS environment")

    # Prompt the user to input the GitHub repository URL
    repository_url = st.text_input(
        "Enter the GitHub repository URL (e.g., https://github.com/owner/repo):")

    # if st.button("Search"):
    #     # Extract the owner's username and repository name from the URL
    #     match = re.match(r'https://github.com/([^/]+)/([^/]+)', repository_url)
    #     if not match:
    #         st.error("Invalid GitHub repository URL. Please provide a valid URL.")
    #         return

    #     owner = match.group(1)
    #     repo_name = match.group(2)

    #     contributors_data = collect_contributors_data(owner, repo_name)

    #     if contributors_data:
    #         st.write("Contributors Information:")
    #         df = pd.DataFrame(contributors_data)
    #         st.dataframe(df)

    #         # Provide a download button for the Excel file
    #         excel_file_name = f'downloads/{repo_name}_contributors_data.xlsx'
    #         excel_data = to_excel(df)
    #         st.download_button(label='📥 Download Excel File', data=excel_data,
    #                            key=excel_file_name, file_name=excel_file_name)

    if st.button("Search"):
        # Extract the owner's username and repository name from the URL
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', repository_url)
        if not match:
            st.error("Invalid GitHub repository URL. Please provide a valid URL.")
            return

        owner = match.group(1)
        repo_name = match.group(2)

    # Add progress bar
        progress_text = "Fetching contributors data. Please wait."
        my_bar = st.progress(0, text=progress_text)

        contributors_data = collect_contributors_data(owner, repo_name)
        
        if contributors_data:
            # Update progress bar after data is fetched
            my_bar.text("Processing data...")
            my_bar.progress(50)

            st.write("Contributors Information:")
            df = pd.DataFrame(contributors_data)
            st.dataframe(df)

        # Provide a download button for the Excel file
        excel_file_name = f'downloads/{repo_name}_contributors_data.xlsx'
        excel_data = to_excel(df)
        st.download_button(label='📥 Download Excel File', data=excel_data,
                           key=excel_file_name, file_name=excel_file_name)

    # Complete progress bar
        my_bar.text("Operation complete.")
        my_bar.progress(100)
        time.sleep(1)
        my_bar.empty()

    st.divider()
    st.markdown('#####')
    st.subheader('Limitations')
    st.markdown(f'''    
            <ul>
            
            • GitHub API rate limits and potential API changes could impact the project's 
              data retrieval capabilities.
            • Reliance on the mentioned parameters as the sole contributor for validation 
              factors may not account for the quality or security of contributions.
            • The accuracy of vulnerability detection using Bandit may depend on the quality 
              of code analysis rules and the context of the project.
        </ul>
        ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
