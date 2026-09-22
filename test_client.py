import requests

url = "http://localhost:8000/analyze"
params = {
    "algo": "binary_search",
    "step": 100,
    "n_max": 5000
}

response = requests.get(url, params=params)
print("Status Code:", response.status_code)
data = response.json()
print("Algorithm:", data.get("algo"))
print("Local Path:", data.get("local_path"))
print("Base64 Image:", data.get("image_base64", "")[:100] + "...")
print("Base64 URL:", data.get("image_url", ""))