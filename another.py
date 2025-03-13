import requests

response = requests.get("http://127.0.0.1:9090/authAddress")
print(response.json())
response = requests.get("http://127.0.0.1:9090/queueAddress")
print(response.json())
