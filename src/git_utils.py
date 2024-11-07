import git
import os

REPO_URL = "https://github.com/Undeadxyzz/MPS_Print_Manuals.git"  # Replace with your repository URL
REPO_PATH = os.path.join(os.path.dirname(__file__), "data_repo")  # Path for cloning

def setup_repository():
    if not os.path.exists(REPO_PATH):
        print("Cloning repository...")
        git.Repo.clone_from(REPO_URL, REPO_PATH)
    else:
        print("Pulling latest changes...")
        repo = git.Repo(REPO_PATH)
        repo.remotes.origin.pull()
    print("Repository is up to date.")

def read_file_from_repo(file_path):
    full_path = os.path.join(REPO_PATH, file_path)
    try:
        with open(full_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File {file_path} not found in the repository.")
        return None
