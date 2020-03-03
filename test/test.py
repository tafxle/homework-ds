import json
import urllib.request

API_ROOT = "http://web:80/api/v1/"

products = [
    {
        "id": 32,
        "name": "Car model",
        "category": "toys"
    }, {
        "id": 5,
        "name": "Guitar",
        "category": "personal"
    }
]

urllib.request.urlopen(API_ROOT + "ping")

resp = urllib.request.urlopen(API_ROOT + "products/list")
for e in json.load(resp):
    req = urllib.request.Request(
        API_ROOT + "product/" + str(e['id']),
        method='DELETE')
    assert urllib.request.urlopen(req).getcode() == 204

for e in products:
    req = urllib.request.Request(
        API_ROOT + "product/" + str(e['id']),
        data=json.dumps(e).encode(),
        headers={'Content-type': 'application/json'},
        method='PUT')
    assert urllib.request.urlopen(req).getcode() == 204


req = urllib.request.Request(
    API_ROOT + "product/" + str(products[0]['id']),
    data=json.dumps(products[0]).encode(),
    headers={'Content-type': 'application/json'},
    method='POST')

try:
    conn = urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    assert e.code == 409
else:
    assert False

req = urllib.request.urlopen(API_ROOT + "product/" + str(products[0]['id']))
req = json.load(req)
assert req == products[0]

req = urllib.request.urlopen(API_ROOT + "products/list")
# order is strict
assert json.load(req) == products

req = urllib.request.urlopen(API_ROOT + "products/list?query=model")
assert json.load(req) == products[:1]

req = urllib.request.urlopen(API_ROOT + "products/list?category=toys")
assert json.load(req) == products[:1]

req = urllib.request.urlopen(API_ROOT + "products/list?page=2&per_page=1")
assert json.load(req) == products[1:]

req = urllib.request.Request(API_ROOT + "product/" + str(products[1]['id']), method='DELETE')
assert urllib.request.urlopen(req).getcode() == 204

products[0]["name"] = "Toy car"
req = urllib.request.Request(
    API_ROOT + "product/" + str(products[0]['id']),
    data=json.dumps(products[0]).encode(),
    headers={'Content-type': 'application/json'},
    method='PUT')
assert urllib.request.urlopen(req).getcode() == 204

req = urllib.request.urlopen(API_ROOT + "products/list")
assert json.load(req) == products[:1]

print("All tests passed!")
