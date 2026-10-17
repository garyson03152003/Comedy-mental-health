"""Query CDC WONDER mortality databases (national-level, the only level the API allows).

Builds the request from the database's own HTML form defaults, then overrides a few fields.
Usage: python3 src/wonder.py D176 out.csv [group_by2]
"""
import sys, re, html, requests
from html.parser import HTMLParser
import pandas as pd

URL = "https://wonder.cdc.gov/controller/datarequest/{}"
SUICIDE_113 = "GR113-124"  # ICD-10 113 cause list: Intentional self-harm (X60-X84, Y87.0, *U03)

class Form(HTMLParser):
    """Collect default values of all inputs/selects in the WONDER request form."""
    def __init__(self):
        super().__init__(); self.vals = {}; self.sel = None; self.sel_vals = []; self.first = None
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "input" and a.get("name"):
            t = a.get("type", "text")
            if t in ("radio", "checkbox"):
                if "checked" in a: self.vals.setdefault(a["name"], []).append(a.get("value", "on"))
            elif t != "submit":
                self.vals[a["name"]] = [a.get("value", "")]
        elif tag == "select":
            self.sel, self.sel_vals, self.first = a.get("name"), [], None
        elif tag == "option" and self.sel:
            if self.first is None: self.first = a.get("value")
            if "selected" in a: self.sel_vals.append(a.get("value"))
    def handle_endtag(self, tag):
        if tag == "select" and self.sel:
            self.vals[self.sel] = self.sel_vals or ([self.first] if self.first is not None else [])
            self.sel = None

def query(db, by=("V1-level2",), extra=None):
    s = requests.Session()
    form = s.post(URL.format(db), data={"stage": "about", "action-I Agree": "I Agree"}, timeout=300).text
    f = Form(); f.feed(form); p = f.vals
    p = {k: v for k, v in p.items() if not k.startswith("action-")}
    for i in range(1, 6):
        p[f"B_{i}"] = [f"{db}.{by[i-1]}" if i <= len(by) else "*None*"]
    p[f"V_{db}.V4"] = [SUICIDE_113]
    p[f"O_ucd"] = [f"{db}.V4"]
    p["O_show_totals"] = ["false"]; p["O_javascript"] = ["off"]
    for v in ("V13", "V15", "V16", "V26"):  # multiple-cause finders: leave unrestricted
        if f"O_{v}_fmode" not in p:
            continue
        p[f"O_{v}_fmode"] = ["freg"]; p[f"V_{db}.{v}"] = [""]; p[f"V_{db}.{v}_AND"] = [""]
    p.update(extra or {})
    xml = "<request-parameters>" + "".join(
        f"<parameter><name>{html.escape(k)}</name>" + "".join(f"<value>{html.escape(x or '')}</value>" for x in v) + "</parameter>"
        for k, v in p.items()) + "</request-parameters>"
    r = s.post(URL.format(db), data={"request_xml": xml, "accept_datause_restrictions": "true"}, timeout=600)
    rows = re.findall(r"<r>(.*?)</r>", r.text, re.S)
    if not rows:
        raise RuntimeError(re.findall(r"<message>(.*?)</message>", r.text)[:5] or r.text[:500])
    out = []
    for row in rows:
        cells = re.findall(r'<c (?:l|v)="([^"]*)"', row)
        out.append(cells)
    return pd.DataFrame(out)

if __name__ == "__main__":
    db, path = sys.argv[1], sys.argv[2]
    by = ("V1-level2",) + tuple(sys.argv[3:])
    df = query(db, by)
    df.to_csv(path, index=False); print(df.head(), len(df))
