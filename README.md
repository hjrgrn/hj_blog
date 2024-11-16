# HJBlog


## Description

An explorative blog website written for practing the Flask echosystem, written with a minimal set of Flask plugins.
The application is not complete and is not meant for running into a production environment.


## Installation

The provided configuration files will run the application on the local machine.

On Ubuntu 24.04 based OSes:

```bash
sudo apt install python3-venv
python3.12 -m venv <PATH_TO_ENV>
source <PATH_TO_ENV>/bin/activate
pip install --upgrade pip
# Without [neovim] if you don't use neovim
pip install -e .[neovim,test]
```


## Commands

Running the project in debug mode(don't use this application into production):
```bash
flask --app hjblog:create run --debug
```

Listing the avaible server commands:
```bash
flask --app hjblog:create ls
```

Running the tests:
```bash
pytest
```
