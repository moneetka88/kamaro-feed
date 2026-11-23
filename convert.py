# Prevod skladu KAMARO do Upgates XML (kody N111_<id>_<skupina>)
import os, re, sys, urllib.request
import xml.etree.ElementTree as ET

T = os.environ["KAMARO_TOKEN"]
LISTING = "http://kamaro.blaznidohracek.cz/google/%s.xml" % T
AVA = "http://kamaro.blaznidohracek.cz/googleAva/%s.xml" % T
G = "{http://base.google.com/ns/1.0}"


def items(url):
    with urllib.request.urlopen(url, timeout=300) as r:
        for ev, el in ET.iterparse(r):
            if el.tag == "item":
                yield el
                el.clear()


skup = {}
for el in items(LISTING):
    i = (el.findtext(G + "id") or "").strip()
    m = re.search(r"-skup(\d+)\.php", el.findtext(G + "link") or "")
    if i and m:
        skup[i] = m.group(1)
print("listing:", len(skup))
if len(skup) < 1000:
    sys.exit("listing feed too small")

out = ['<?xml version="1.0" encoding="UTF-8"?>', '<PRODUCTS version="2.0.0">']
n = 0
for el in items(AVA):
    i = (el.findtext(G + "id") or "").strip()
    if i not in skup:
        continue
    q = (el.findtext(G + "inStock") or "0").strip()
    if not q.lstrip("-").isdigit():
        q = "0"
    out.append("<PRODUCT><CODE>N111_%s_%s</CODE><STOCK>%s</STOCK></PRODUCT>" % (i, skup[i], max(int(q), 0)))
    n += 1
out.append("</PRODUCTS>")
print("output:", n)
if n < 1000:
    sys.exit("output too small")
os.makedirs("out", exist_ok=True)
with open("out/kamaro-stock.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
