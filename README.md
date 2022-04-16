# GenshinImpact 3rd-party API

> IGS has now been upgraded to the new Genshin 3rd-party API :)
> **Development version, do not use in production environment!**

## Features
  - Use a faster FastAPI to replace frameworks such as Quart used in earlier versions
  - Support for more than just picture generators

## Installation
1. Clone this repo.

  ```shell
  git clone https://github.com/Genshin-bots/GAPI.git
  cd GAPI
  ```

3. Use a virtual environment (optional).

  ```shell
  # Create Virtual Environment
  python -m venv venv
  
  # Activate
  .\venv\Scripts\activate.bat # for Windows Users using cmd
  .\venv\Scripts\activate.ps1 # for Windows Users using powershell
  .\venv\Scripts\activate.sh # for Linux Users
  ```

4. Installation dependencies.

  ```shell
  pip install -r requirements
  ```

6. start!
  
  ```shell
  uvicorn main:igs
  ```
  **Note**: you can use `--host` to specify the listening IP address, and `-- port` to specify the listening port.
