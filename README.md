# Shoggoth Coder (a ChatGPT Plugin)

## Setup
```bash
$ python3 -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt
```

## How it works


## Run

Press the Run button

## Setup Config
Make sure your github SSH keys are in order (i.e. you should be able to clone a repo from your terminal - https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

* OPENAI_API_KEY - OpenAI api key (https://platform.openai.com/account/api-keys)
* gh_username - Github username
* gh_access_token - Classic access token (https://github.com/settings/tokens, make sure to enable Repo scope)
* GIT_SSH_COMMAND='ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no'

Place in .env


