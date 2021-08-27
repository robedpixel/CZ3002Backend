%UserProfile%\Miniconda3\Scripts\activate.bat && ^
conda activate CZ3002 && ^
cd %~dp0 && ^
python manage.py runserver_plus --cert cert.crt