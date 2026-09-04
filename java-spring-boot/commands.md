# Commands

Run the installer in `setup/` from the repository root and select Java (Spring Boot). Setup opens this folder. Run tests after editing the service.
This command builds the latest code and starts and stops the test server automatically.
It also downloads any missing Maven dependencies.

```sh
python3 test.py
```

Check the scaffold only:

```sh
python3 test.py --smoke
```
