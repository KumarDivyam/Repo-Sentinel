import os
import subprocess
import requests
import json
from github import Github
import streamlit as st

# Streamlit app title
st.title("_:blue[Repo]_ _:red[Sentinel]_ 🤖")

# Streamlit user input section
st.header("User Input")

# User inputs
token = st.text_input("GitHub Personal Access Token", type="password")
username = st.text_input("GitHub Username", value="divypathak")
repo_name = st.text_input("GitHub Repository Name", value="Python_project")
clone_directory = st.text_input("Clone Directory", value="Clone Repos/")

# Streamlit function to fetch repository info
def fetch_repository_info(username, repo_name, token):
    api_url = f'https://api.github.com/repos/{username}/{repo_name}'
    headers = {'Authorization': f'token {token}'}
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        st.error(f'Failed to fetch repository info with status code: {response.status_code}')
        st.stop()

    return response.json()

# Streamlit function to clone repository
def clone_repository(repo_data, clone_directory):
    os.makedirs(clone_directory, exist_ok=True)
    os.chdir(clone_directory)
    repo_url = repo_data['clone_url']
    os.system(f'git clone {repo_url}')
    os.chdir(repo_data['name'])

# Streamlit function to perform dependency scanning
def perform_dependency_scanning():
    safety_command = 'safety check --full-report'
    subprocess.run(safety_command, shell=True)

# Streamlit function to perform static code analysis
def perform_static_code_analysis():
    bandit_command = 'bandit -r .'
    subprocess.run(bandit_command, shell=True)

# Streamlit function to detect and print languages
def detect_and_print_languages(username, repo_name, token):
    github = Github(token)
    repo = github.get_repo(f'{username}/{repo_name}')
    languages = repo.get_languages()

    total_bytes = sum(languages.values())
    st.text('\nDetected Languages (Normalized):')
    for language, bytes_count in languages.items():
        percentage = (bytes_count / total_bytes) * 100
        st.text(f'{language}: {percentage:.2f}%')

# Streamlit function to remove cloned repository
def remove_cloned_repository(repo_name):
    user_input = st.selectbox("Do you want to remove the cloned repository?", ('Yes', 'No'))
    if user_input == 'Yes':
        os.chdir('..')
        if os.name == 'posix':  # Check if the OS is Unix-like (Linux or macOS)
            os.system(f'rm -rf {repo_name}')
        elif os.name == 'nt':  # Check if the OS is Windows
            os.system(f'rmdir /s /q {repo_name}')

# Streamlit button to trigger the analysis
if st.button("Analyze Repository"):
    # Check if any of the required inputs are empty
    if not token or not username or not repo_name or not clone_directory:
        st.warning("Please provide all required input values.")
    else:
        repo_data = fetch_repository_info(username, repo_name, token)
        clone_repository(repo_data, clone_directory)
        perform_dependency_scanning()
        perform_static_code_analysis()
        detect_and_print_languages(username, repo_name, token)

        # Ask user whether to remove the cloned repository
        remove_cloned_repository(repo_name)
