import requests
for ep, q in (("label", 'openfda.generic_name:"clozapine"'), ("enforcement", 'openfda.generic_name:"metformin"')):
    r = requests.get(f"https://api.fda.gov/drug/{ep}.json", params={"search": q, "limit": 1}, timeout=30)
    print(ep, "HTTP", r.status_code, "resultados:", r.json().get("meta", {}).get("results", {}).get("total"))
