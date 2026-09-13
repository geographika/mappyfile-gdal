# C:\Python313\python.exe -m venv  C:\VirtualEnvs\mappyfile-gdal

C:\VirtualEnvs\mappyfile-gdal\Scripts\activate.ps1
cd D:\GitHub\mappyfile-gdal

pip install -r requirements-dev.txt
pip install -e .

black .
flake8 .
mypy .
pytest

