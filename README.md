### Pre-requisites

1) Install UV

We recommend installing uv globally with pip:

```
pip install uv
```

On some managed MacOS systems an attempt to install Python packages globally causes the below error:
```
This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.
```

The alternatives are:
- Install uv with ```brew install uv```;
- Install uv in a virtualenv (and then make sure that virtualenv is active before using uv);
- Use the ```--break-system-packages``` option: ```pip3 install uv --break-system-packages```;
- If you have conda, install uv in ```$ANACONDA_HOME/bin``` by running ```conda install conda-forge::uv```.

2) Create a virtual environment.
   ```
    python -m venv .venv
    source .venv/bin/activate    # if *nix
    .venv\Scripts\activate       # if Windows  

    (or)
    
    uv venv --python 3.13
    source .venv/bin/activate    # if *nix
    .venv\Scripts\activate       # if Windows
   ```

3) Install Build Tools.
   ```
   pip install setuptools wheel build
   ```

### Build, Install and Run the Python Package

1) Build Distribution Archives.
   ```
   python -m build
   ```

2) Install your package.
     ```
     pip install -e .  # Install in editable mode for development
     (or)
     pip install dist/ria-0.1.0-py3-none-any.whl   # to install from the built wheel:
     ```

3) Run as python script.
     ```
     python <project_root>/ria/ria.py
     ```

4) Run as python module.
     ```
     python -m ria.ria
     ```

5) Run as CLI tool.
     ```
     ria
     ```

### For distribution to others, publish it to the Python Package Index (PyPI)

1) Python Package Index With ```devpi```
```
pip install devpi devpi-server devpi-client
initialize: devpi-init
start server  : devpi-server --host 0.0.0.0 --port 3141
devpi use http://0.0.0.0:3141/
login         : devpi login root --password ''
add index     : devpi index -c dev bases=root/pypi
use index     : devpi use root/dev
upload package: devpi upload dist/*
Uploading to a specific index (if not using devpi use):
                devpi upload --index <user>/<index_name>
e.g.,           devpi upload --index root/dev
```
(or)
```
twine upload --repository-url http://0.0.0.0:3141/root/dev dist/* -u root -p ''
```
(or)
```
twine upload -r devpi dist/* --verbose
vi ~/.pypirc:
[distutils]
index-servers = devpi

[devpi]
repository = http://localhost:3141/root/dev
username = root
```

2) Install package from ```devpi``` Index
```
uvx --index http://0.0.0.0:3141/root/dev/+simple/ ria@latest
uvx --index http://0.0.0.0:3141/root/dev/ ria
uv tool run --index http://0.0.0.0:3141/root/dev/ ria
(or)
export PIP_INDEX_URL=http://localhost:3141/root/dev/
uvx ria
(or)
pip install -i http://localhost:3141/root/pypi/+simple/ your-package-name
e.g., pip install -i http://localhost:3141/root/dev/+simple/ ria --verbose
```
