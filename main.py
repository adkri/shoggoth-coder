import json
import os
import requests

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware


from shoggoth_coder.repo_utils import repo_name_from_url, commit_and_push_pr, clear_repo_changes, fork_and_clone_repo
from shoggoth_coder.repo_embedder.embedder import create_repo_embedding, search_repo_embeddings

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_repo = ""
active_repo_url = ""


class RepoContext:
  pass


class StagingArea:
  files = []



@app.get("/search_github_repo")
async def search_github_repo(query: str):
  url = f"https://api.github.com/search/repositories?q={query}"
  response = requests.get(url)
  if response.status_code == 200:
    results = response.json()["items"]
    resp = []
    for result in results:
      resp.append(result["html_url"])
    return {"repos": resp}
  else:
    raise HTTPException(status_code=404, detail="Could not search for repo")


@app.get("/select_and_load_repo")
async def select_and_load_repo(repo_url: str):
  print("We got the repo url", repo_url)
  clone_success = fork_and_clone_repo(repo_url)
  if clone_success:
    global active_repo
    global active_repo_url
    active_repo = repo_name_from_url(repo_url)
    active_repo_url = repo_url
    print("Set active repo to: ", active_repo)

  print(f"Generate relevant embeddings for repo: {active_repo}")
  create_repo_embedding(active_repo, f".cache/repo/{active_repo}")
  metadata = search_repo_embeddings("main", active_repo)
  return {
    "message": "This repo has been succesfully loaded and is now active",
    "metadata": "Some entrypoint files in repo: \n" + metadata
  }

@app.get("/search_file_metadata_in_repo")
async def search_file_metadata_in_repo(query_keywords: str):
  """
  Does an embeddings search on repo based on query keywords to retrieve top_k relevant files metadata
  """
  if active_repo == "":
    raise HTTPException(
      status_code=404,
      detail="No repo has been loaded yet. Try selecting a repo first.")
  
  metadata = search_repo_embeddings(query_keywords, active_repo)
  return {"results": metadata}


@app.get("/load_contents_from_repo_file")
async def load_contents_from_repo_file(file_path: str):
  if active_repo == "":
    raise HTTPException(
      status_code=404,
      detail="No repo has been loaded yet. Try selecting a repo first.")
  path_in_repo_cache = f".cache/repo/{file_path}"
  if not os.path.exists(path_in_repo_cache):
    raise HTTPException(
      status_code=404,
      detail=
      "Could not find file. Make sure the repo name is included in the prefix and try again."
    )
  with open(path_in_repo_cache, "r") as f:
    contents = f.read()
  return {"file_path": file_path, "file_contents": contents}


@app.post("/update_contents_in_repo_file")
async def update_contents_in_repo_file(file_path: str, updated_code: str):
  """
  Update the contents of file with new code.
  """
  print("path", file_path)
  print("updated_code", updated_code)
  if active_repo == "":
    raise HTTPException(
      status_code=404,
      detail="No repo has been loaded yet. Try selecting a repo first.")
  path_in_repo_cache = f".cache/repo/{file_path}"
  if not os.path.exists(path_in_repo_cache):
    raise HTTPException(
      status_code=404,
      detail=
      "Could not find file. Make sure the repo name is included in the prefix and try again."
    )
  with open(path_in_repo_cache, "w") as f:
    f.write(updated_code)

  return {"file_path": file_path, "message": "Successfully updated the file!"}


@app.post("/commit_changes_and_create_pr")
async def commit_changes_and_create_pr(commit_message: str, pr_title: str,
                                       pr_description: str):
  """
  Commit the changes to the git repo, and create and submit a pull request.
  """
  if active_repo == "":
    raise HTTPException(
      status_code=404,
      detail="No repo has been loaded yet. Try selecting a repo first.")
  pr_url = commit_and_push_pr(active_repo_url, active_repo, commit_message, pr_title,
                              pr_description)
  return {
    "message": "Pull request has been successfully created.",
    "pull_request_url": pr_url
  }


@app.post("/reset_all_repo_changes")
async def reset_all_repo_changes():
  """
  Resets all changes made to the active repo
  """
  clear_repo_changes(active_repo)
  return {
    "message": "Successfully cleared the active repo.",
    "active_repo": active_repo
  }


@app.get("/")
async def hello_world():
  return ""


@app.get("/logo.png")
async def plugin_logo():
  return FileResponse('logo.png')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest(request: Request):
  host = request.headers['host']
  with open("ai-plugin.json") as f:
    text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
  return JSONResponse(content=json.loads(text))


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="127.0.0.1", port=5003)

