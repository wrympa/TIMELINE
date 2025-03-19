import requests

response = requests.get("https://timeline-production-1416.up.railway.app/authAddress")
print(response.json())
response = requests.get("https://timeline-production-1416.up.railway.app/queueAddress")
print(response.json())
response = requests.get("https://timeline-production-1416.up.railway.app/gameManagerAddress")
print(response.json())
