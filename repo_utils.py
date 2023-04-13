import os
import git
from github import Github
from dotenv import load_dotenv
load_dotenv()

gh_username = os.environ.get('gh_username', "<your-username>")
gh_access_token = os.environ.get('gh_access_token', None)

CACHE_DIR = ".cache/repo/"

def https_to_ssh(https_url: str) -> str:
    parts = https_url.split('/')
    repo_owner = parts[-2]
    repo_name = parts[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    ssh_url = f"git@github.com:{repo_owner}/{repo_name}.git"
    return ssh_url


def repo_name_from_url(repo_url):
  repo_name = repo_url.split("/")[-1].replace(".git", "")
  return repo_name


def fork_and_clone_repo(repo_url):
  if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

  repo_name = repo_url.split("/")[-1].replace(".git", "")
  repo_path = os.path.join(CACHE_DIR, repo_name)

  original_owner = repo_url.split("/")[-2]

  if original_owner != gh_username:
    g = Github(gh_access_token)
    original_repo = g.get_user(original_owner).get_repo(repo_name)
    # need to fork and clone
    forked_repo = g.get_user().create_fork(original_repo)
    if not os.path.exists(repo_path):
      git.Repo.clone_from(forked_repo.ssh_url, repo_path)
    else:
      repo = git.Repo(repo_path)
      origin = repo.remotes.origin
      origin.pull()
  else:
    # can just clone for personal repo
    if not os.path.exists(repo_path):
      ssh_url = https_to_ssh(repo_url)
      git.Repo.clone_from(ssh_url, repo_path)
    else:
      repo = git.Repo(repo_path)
      origin = repo.remotes.origin
      origin.pull()
  return True


def clone_repo(repo_url):
  try:
    if not os.path.exists(CACHE_DIR):
      os.makedirs(CACHE_DIR)

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(CACHE_DIR, repo_name)

    if not os.path.exists(repo_path):
      git.Repo.clone_from(repo_url, repo_path)
    else:
      repo = git.Repo(repo_path)
      origin = repo.remotes.origin
      origin.pull()
    return True
  except:
    raise ("Failed to load repo")


def commit_and_push_pr(repo_url, repo_name, commit_message, pr_title, pr_description):
  if (not repo_name) or (not commit_message) or (not pr_title) or (
      not pr_description):
    raise ("You need to include all: commit_message, pr_title, pr_description")

  repo_path = f"{CACHE_DIR}{repo_name}"
  repo = git.Repo(repo_path)

  # Set the Git username and email
  repo.config_writer().set_value("user", "name", "shoggoth-coder").release()
  repo.config_writer().set_value("user", "email",
                                 "shoggoth-coder@gmail.com").release()

  repo.git.add("--all")
  repo.index.commit(commit_message)

  # push changes to remote origin/forked repo
  origin = repo.remote(name="origin")
  origin.push()

  original_owner = repo_url.split("/")[-2]
  if original_owner != gh_username:
    # if not personal repo, create PR
    g = Github(gh_access_token)
    original_repo = g.get_user(original_owner).get_repo(repo_name)
    pull_request = original_repo.create_pull(title=pr_title, body=pr_description, base="main", head=f"{gh_username}:main")

    # Get the pull request URL
    pull_request_url = pull_request.html_url
    return pull_request_url
  else:
    return repo_url


def clear_repo_changes(repo_name):
  repo_path = f"{CACHE_DIR}{repo_name}"
  repo = git.Repo(repo_path)

  # Clear all staged changes
  repo.git.reset("HEAD")

  # Clear all non-staged changes
  repo.git.checkout("--", ".")

  # Reset the repository to the HEAD commit
  repo.git.reset("--hard", "HEAD")

  return True
