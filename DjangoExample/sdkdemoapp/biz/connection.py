from django.conf import settings

import devicebroker.client
import devicebroker.defaults

def open() -> devicebroker.client.Client:
	return devicebroker.client.Client(
		getattr(settings, "DEVICEBROKER_ADDRESS", devicebroker.defaults.DEF_SOCK_NAME)
	)
