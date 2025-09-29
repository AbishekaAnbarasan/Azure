import requests

url = "https://api.openrouteservice.org/v2/directions/driving-car"
headers = {
    "Authorization": "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjgwZWFhYzEyNWZkZjRjMzliNTc1YzA1ZjJjNzc5ZGUxIiwiaCI6Im11cm11cjY0In0=",  # Replace with your real API key
    "Content-Type": "application/json"
}
body = {
    "coordinates": [[80.275, 13.0827], [80.283, 13.05]]
}

resp = requests.post(url, headers=headers, json=body)
print(resp.json())
