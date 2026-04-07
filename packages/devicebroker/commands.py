from typing import Final

# Commands to load balancer to worker
CLIENT_CONNECTED        : Final[int]    = 1
MESSAGE_FROM_CLIENT     : Final[int]    = 2
CLIENT_DISCONNECTED     : Final[int]    = 3

# Commands from worker to load balancer
ASSIGN_DEVICE_ID        : Final[int]    = 101
SEND_MESSAGE_TO_CLIENT  : Final[int]    = 102
RESPONSE_FROM_DEVICE    : Final[int]    = 103

# Commands from application to load balancer
FIND_DEVICE_BY_ID       : Final[int]    = 201
SEND_AND_RECEIVE        : Final[int]    = 202
GET_ALL_ONLINE_DEVICES  : Final[int]    = 203
GET_CONNECTION_INFO     : Final[int]    = 204
