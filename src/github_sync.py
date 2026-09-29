import os
import base64
import requests
import streamlit as st

def push_to_github(file_path: str, repo_name: str = "GuntherTheeChampion/dashboard-rrjabar", branch: str = "main"):
    """
    Pushes a local file to the GitHub repository using the GitHub REST API.
    Does not require PyGithub.
    """
    if not hasattr(st, "secrets") or "github" not in st.secrets or "token" not in st.secrets["github"]:
        # If no token is configured, skip gracefully (e.g. for local dev)
        return
        
    github_token = st.secrets["github"]["token"]
    
    # Calculate the relative path in the repo
    repo_path = file_path
    if os.path.isabs(file_path):
        try:
            # Assumes Streamlit runs from the root of the repository
            repo_path = os.path.relpath(file_path, os.getcwd()).replace("\\", "/")
        except Exception:
            repo_path = os.path.basename(file_path)
    
    url = f"https://api.github.com/repos/{repo_name}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Read the local file
    try:
        with open(file_path, "rb") as f:
            content_bytes = f.read()
            encoded_content = base64.b64encode(content_bytes).decode("utf-8")
    except Exception as e:
        print(f"Failed to read file for GitHub sync: {e}")
        return

    # 2. Check if the file already exists to get its SHA
    sha = None
    try:
        response = requests.get(url, headers=headers, params={"ref": branch}, timeout=10)
        if response.status_code == 200:
            sha = response.json().get("sha")
    except Exception:
        pass
        
    # 3. Create or Update the file
    data = {
        "message": f"Auto-sync {os.path.basename(repo_path)} from Streamlit Cloud",
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        data["sha"] = sha
        
    try:
        res = requests.put(url, headers=headers, json=data, timeout=10)
        if res.status_code in (200, 201):
            print(f"Successfully synced {repo_path} to GitHub!")
        else:
            print(f"Failed to sync {repo_path}: {res.text}")
    except Exception as e:
        print(f"Exception during GitHub sync: {e}")
