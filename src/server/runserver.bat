%UserProfile%\Miniconda3\Scripts\activate.bat && ^
conda activate CZ3002 && ^
cd %~dp0 && ^
python manage.py runserver 0.0.0.0:8000
::python manage.py runserver_plus --cert cert.crt 0.0.0.0:8000