# test_embeddings.py
import requests, json
url = "http://altheia.gruporeyes.org:9080/v1/embeddings"
payload = {
  "input": ["hola mundo", "probando embeddings"],
  "model": "nvidia/nv-embedqa-e5-v5",
  "input_type": "query",
  "encoding_format": "float",
  "truncate": "NONE",
  "user": "altheia"
}
r = requests.post(url, json=payload, headers={"accept":"application/json","Content-Type":"application/json"})
print(r.status_code)
print(json.dumps(r.json(), indent=2)[:1200])
