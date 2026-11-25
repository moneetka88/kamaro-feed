# Prevod skladu KAMARO do Upgates XML (kody N111_<id>_<skupina>), rezerva 2 ks
import os, re, sys, urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
T = os.environ["KAMARO_TOKEN"]
LISTING = "http://kamaro.blaznidohracek.cz/google/%s.xml" % T
AVA = "http://kamaro.blaznidohracek.cz/googleAva/%s.xml" % T
G = "{http://base.google.com/ns/1.0}"
K = G
RESERVE = 2
def items(url):
    with urllib.request.urlopen(url, timeout=300) as r:
        for ev, el in ET.iterparse(r):
            if el.tag == "item":
                yield el
                el.clear()
skup = {}
det = []
csv = ["sku;manufacturer;image;image2;image3;image4;image5;vek;mpn;pohlavi"]
for el in items(LISTING):
    i = (el.findtext(G + "id") or "").strip()
    m = re.search(r"-skup(\d+)\.php", el.findtext(G + "link") or "")
    if i and m:
        skup[i] = m.group(1)
        img = (el.findtext(G + "image_link") or "").strip()
        br = (el.findtext(G + "brand") or "").strip()
        if br.startswith("_"):
            br = ""
        p = "<PRODUCT><CODE>N111_%s_%s</CODE>" % (i, m.group(1))
        if br:
            p += "<MANUFACTURER>%s</MANUFACTURER>" % escape(br)
        if img:
            p += "<IMAGES><IMAGE><URL>%s</URL><MAIN_YES>1</MAIN_YES><LIST_YES>1</LIST_YES></IMAGE></IMAGES>" % escape(img)
        det.append(p + "</PRODUCT>")
        extra = [(x.text or "").strip().replace(";", "%3B") for x in el.findall(G + "additional_image_link")][:4]
        extra += [""] * (4 - len(extra))
        cl = lambda t: (t or "").strip().replace(";", ",")
        csv.append(";".join(["N111_%s_%s" % (i, m.group(1)), cl(br), img.replace(";", "%3B")] + extra + [cl(el.findtext(K + "vek")), cl(el.findtext(G + "mpn")), cl(el.findtext(G + "gender"))]))
print("listing:", len(skup))
if len(skup) < 1000:
    sys.exit("listing feed too small")
ava = {}
for el in items(AVA):
    i = (el.findtext(G + "id") or "").strip()
    q = (el.findtext(G + "inStock") or "0").strip()
    sh = (el.findtext(G + "show") or "1").strip()
    ava[i] = (int(q) if q.lstrip("-").isdigit() else 0, sh != "0")
codes = {"N111_%s_%s" % (i, k) for i, k in skup.items()}
if os.path.exists("codes_seed.txt"):
    codes |= {c.strip() for c in open("codes_seed.txt", encoding="utf-8") if c.strip().startswith("N111_")}
try:
    with urllib.request.urlopen("https://raw.githubusercontent.com/moneetka88/kamaro-feed/feed/codes_known.txt", timeout=60) as r:
        codes |= {c.strip() for c in r.read().decode("utf-8").split() if c.startswith("N111_")}
except Exception as e:
    print("no known codes:", e)
out = ['<?xml version="1.0" encoding="UTF-8"?>', '<PRODUCTS version="2.0.0">']
n = zero = 0
for c in sorted(codes):
    i, k = c[5:].rsplit("_", 1)
    q, shown = ava.get(i, (0, False))
    st = max(q - RESERVE, 0) if (shown and skup.get(i) == k) else 0
    if st == 0:
        zero += 1
    out.append("<PRODUCT><CODE>%s</CODE><STOCK>%s</STOCK></PRODUCT>" % (c, st))
    n += 1
out.append("</PRODUCTS>")
print("output:", n, "zero:", zero)
if n < 1000:
    sys.exit("output too small")
os.makedirs("out", exist_ok=True)
with open("out/kamaro-stock.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
with open("out/kamaro-detail.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(['<?xml version="1.0" encoding="UTF-8"?>', '<PRODUCTS version="2.0.0">'] + det + ["</PRODUCTS>"]))
with open("out/kamaro-base.csv", "w", encoding="utf-8") as f:
    f.write("\n".join(csv))
with open("out/codes_known.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(codes)))
