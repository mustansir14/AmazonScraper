import requests

API_KEY = "CkcNsk8r6BcCWfta"

http_proxy = f"http://suli:{API_KEY}@proxy.packetstream.io:31112"
https_proxy = f"http://suli:{API_KEY}@proxy.packetstream.io:31112"
url = "https://ipv4.icanhazip.com"

proxyDict = {
"http" : http_proxy,
"https" : https_proxy,
}

r = requests.get("https://www.amazon.de/gp/bestsellers/ref=zg_bs_unv_0_boost_1", proxies=proxyDict)

print(r.text)