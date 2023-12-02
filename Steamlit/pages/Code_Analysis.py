import os
import subprocess
import requests
import json
import streamlit as st
import shutil

# Streamlit App
st.title("GitHub Repo Analysis with Bandit")

# Input for GitHub repository URL
github_repo_url = st.text_input("Enter GitHub repository URL:")

# Button to initiate analysis
if st.button("Run Analysis"):
    # Parse GitHub repository information
    try:
        username, repo_name = github_repo_url.split("/")[-2:]
    except ValueError:
        st.error("Invalid GitHub repository URL. Please provide a valid URL.")
        st.stop()

    # Fetch GitHub repository information
    api_url = f'https://api.github.com/repos/{username}/{repo_name}'
    response = requests.get(api_url)

    if response.status_code == 200:
        repo_info = response.json()

        # Clone the repository
        local_repo_folder = 'cloned_repo'
        clone_url = repo_info['clone_url']
        subprocess.run(["git", "clone", clone_url, local_repo_folder], check=True)

        # Perform Bandit analysis
        bandit_output_file = 'bandit_results.json'
        bandit_process = subprocess.run(["bandit", "-r", local_repo_folder, "-f", "json", "-o", bandit_output_file])

        if bandit_process.returncode != 0:
            st.success("Repository cloned successfully.")
            st.success("Bandit analysis completed.")

            # Provide a download link for the Bandit results
            with open(bandit_output_file, 'rb') as file:
                bandit_results_data = file.read()

            st.download_button(
                label="Download Bandit Results",
                data=bandit_results_data,
                file_name=bandit_output_file,
                key='bandit_results_download',
            )

            # Button to remove the cloned repository
            if st.button("Remove Cloned Repository"):
                shutil.rmtree(local_repo_folder)
                st.info("Cloned repository removed.")
        else:
            st.error(f"Error during Bandit analysis. Bandit returned non-zero exit status {bandit_process.returncode}")

    else:
        st.error(f"Failed to fetch repository information. Status code: {response.status_code}")
