import streamlit as st
from github import Github, GithubException
import os
import base64
import pandas as pd

DB_FILENAME = "resume_matcher.db"

def get_github_client():
    if "github" not in st.secrets:
        msg = "❌ GitHub Token not found in secrets.toml"
        print(msg)
        st.error(msg)
        return None, None

    token = st.secrets["github"]["token"]
    repo_name = st.secrets["github"]["repo_name"]

    g = Github(token)
    try:
        repo = g.get_repo(repo_name)
        return g, repo
    except Exception as e:
        msg = f"❌ Could not access repo '{repo_name}': {e}"
        print(msg)
        st.error(msg)
        return None, None

def pull_db():
    """Download DB from GitHub to local file (Supports >1MB files)"""
    print("🔄 Attempting to pull DB from GitHub...")
    _, repo = get_github_client()
    if not repo: return False

    try:
        # 1. Get file metadata
        contents = repo.get_contents(DB_FILENAME)
        file_data = None

        # 2. Check if content is directly available (Small files < 1MB)
        if contents.content:
            print(f"📦 File found (Size: {contents.size} bytes). Strategy: Direct Base64.")
            file_data = base64.b64decode(contents.content)

        # 3. If content is missing, it's a large file (> 1MB). Use Blob API.
        else:
            print(f"📦 File found (Size: {contents.size} bytes). Strategy: Git Blob API.")
            blob = repo.get_git_blob(contents.sha)
            file_data = base64.b64decode(blob.content)

        # 4. Write to disk
        if file_data:
            with open(DB_FILENAME, "wb") as f:
                f.write(file_data)
            print("✅ DB Pulled Successfully!")
            return True
        else:
            print("❌ Error: Downloaded content was empty.")
            return False

    except GithubException as e:
        if e.status == 404:
            print("ℹ️ DB file not found in GitHub repo. Using local/fresh DB.")
            return False
        else:
            print(f"❌ Error pulling DB: {e}")
            st.error(f"Error pulling DB: {e}")
            return False

def push_db():
    """Upload local DB to GitHub (Create or Update)"""
    print("⬆️ Attempting to push DB to GitHub...")
    if not os.path.exists(DB_FILENAME):
        st.warning("No local database found to save.")
        return False

    _, repo = get_github_client()
    if not repo: return False

    # Read binary content
    with open(DB_FILENAME, "rb") as f:
        content = f.read()

    try:
        # Check if file exists to decide between create or update
        try:
            contents = repo.get_contents(DB_FILENAME)
            # Update existing file
            repo.update_file(contents.path, f"Update DB: {pd.Timestamp.now()}", content, contents.sha)
            print("✅ DB Updated Successfully!")
        except GithubException as e:
            if e.status == 404:
                # Create new file
                repo.create_file(DB_FILENAME, "Initial DB Commit", content)
                print("✅ New DB Created in GitHub!")
            else:
                raise e

        return True
    except Exception as e:
        print(f"❌ Error pushing DB: {e}")
        st.error(f"Error pushing DB: {e}")
        return False
