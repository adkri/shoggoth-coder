# Shoggoth Coder (a ChatGPT Plugin)

Shoggoth Coder is a coding assistant plugin for ChatGPT that enables you to search for and load repositories on GitHub. You can chat with gpt about the codebase and locate relevant sections that you want to modify. Then simply leverage gpt to write the changes for you and submit a PR.

## Setup
```bash
$ python3 -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt
$ cp .env.example .env
```

## Setup Config
We need to setup your github credentials properly so you can fork, clone, and push to your repo.

Make sure your github SSH keys are in order (i.e. you should be able to clone a repo from your terminal - https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

* OPENAI_API_KEY - OpenAI api key (https://platform.openai.com/account/api-keys)
* gh_username - Github username
* gh_access_token - Classic access token (https://github.com/settings/tokens, make sure to enable Repo scope)
* GIT_SSH_COMMAND='ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no'
  - This is the path to your ssh key used in github, if you're using a different one, use that instead

Place in .env

## Run
```bash
$ source venv/bin/activate
$ python3 main.py
```

## How it works
- You can start by searching for a repo on github (eg. "look up the babyagi repo")
- Select and have it load a repo 
  - This will fork/clone the repo and create embeddings for the repo
- Chat with gpt to explore the codebase
- Find relevant parts in codebase, and have it pull the file (eg. "find the code that deals with monitoring")
- Modify the code by requesting gpt, and update the code
- Request gpt to commit and submit a PR

Currently only supports Python and has limited support for javascript. 
Also, due to the limited context window, it struggles with long files.


## TODO
- Use regex matching on js files to find functions, classes, etc
  - same for other languages
- Better explanation of code
  - kick off background process to summarize repo at file level, module level, etc
- Editing large files
  - maintain active buffer of current file
  - add an "/edit-line" api for chatGPT
    - interface is edit(file, line, text, num_lines, type=insert|replace)
  - peek file to see if it's too large, and if so, ask GPT to edit only sections with "/edit-line"
