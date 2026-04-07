@echo ================================
@echo Please keep the cmd window open.
@echo [URL to open the browser] 	http://localhost:8082/
@echo ================================

:: add PYTHONPATH environment variable PYTHONPATH="<path to SDK>/packages"
:: ex:	PYTHONPATH=C:\D\Shared\zTFS\SDK\WebSocketSDK\WebSocketSDK_Python\packages

python manage.py runserver localhost:8082 --settings=demosite.settings.development

pause