@echo ================================
@echo Please keep the cmd window open.
@echo [Server URL for the device] 	ws://10.8.8.8:8001/
@echo [URL to open the browser] 	http://localhost:8082/
@echo ================================

python -m devicebroker --host 10.8.8.8 --port 8001 --webapp-url http://localhost:8082

pause