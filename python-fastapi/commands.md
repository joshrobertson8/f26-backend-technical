# Commands

Run the installer in `setup/` from the repository root and select Python (FastAPI). Setup opens this folder in the prepared terminal.

Run tests after editing the service. Tests start and stop the server automatically.

```sh
python tests/http_contract.py
```

Check the scaffold only:

```sh
python tests/http_contract.py --smoke
```

Reinstall dependencies if needed:

```sh
python -m pip install -r requirements.txt
```
