import json, urllib.request, numpy as np
BASE = "http://localhost:8000"

def req(method, path, token=None, body=None):
    r = urllib.request.Request(BASE + path, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(r, data=data, timeout=60) as resp:
        return json.loads(resp.read().decode())

def raw(method, path, token=None, body=None):
    try:
        return req(method, path, token, body)
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:500]}

tok = req("POST", "/auth/login", body={"email": "demo@bottleneck.com", "password": "demo1234"})["access_token"]
sites = raw("GET", "/sites/", token=tok)
print("GET /sites/ ->", json.dumps(sites)[:200] if not isinstance(sites, list) else f"list of {len(sites)}")

if isinstance(sites, list):
    all_ok = True
    for s in sites:
        f = raw("GET", f"/api/forecast/{s['id']}", token=tok)
        if "_error" in f:
            print(s["name"], "forecast error:", f)
            all_ok = False
            continue
        p10, p50, p90 = np.array(f["forecast"]["p10"]), np.array(f["forecast"]["p50"]), np.array(f["forecast"]["p90"])
        ok = (np.all(p10 - 1e-9 <= p50) & np.all(p50 - 1e-9 <= p90)
              & np.all(p10 >= -1e-9) & np.all(p90 <= s["capacity_kw"] + 1e-9))
        all_ok = all_ok and ok
        print(f"{s['name']:<24} {s['site_type']:<6} model={f['model_type']:<24} bands_ok={ok} max_p50={np.max(p50):.1f}")
    print("ALL OK:", all_ok, f"({len(sites)} sites)")