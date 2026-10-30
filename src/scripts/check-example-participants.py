"""QC: every SOURCE/TARGET named in an IAO_0000112 contextual example must be permitted
by the has_subject / has_object restriction its class declares or inherits.

Not covered by the ODK report. Restrictions are inherited along rdfs:subClassOf, so
classes such as has descriptive value, which declare none of their own, are checked
against their parent's.

Exit status is 1 if any example contradicts its restriction.
"""
import xml.etree.ElementTree as ET, re, sys

NS={'rdfs':'http://www.w3.org/2000/01/rdf-schema#','obo':'http://purl.obolibrary.org/obo/',
    'owl':'http://www.w3.org/2002/07/owl#'}
R='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
SRC=sys.argv[1] if len(sys.argv)>1 else 'src/ontology/clco-edit.owl'

root=ET.parse(SRC).getroot()
lab, node = {}, {}
for ch in root:
    i=(ch.get(R+'about') or '').split('/')[-1]
    if not i: continue
    node[i]=ch
    l=ch.findtext('rdfs:label',None,NS)
    if l: lab[i]=l
def nm(x):
    x=(x or '').split('/')[-1]
    return lab.get(x,x)

def declared(cid):
    """has_subject / has_object restrictions asserted directly on cid."""
    out={}
    ch=node.get(cid)
    if ch is None: return out
    for s in ch.findall('rdfs:subClassOf',NS):
        rr=s.find('owl:Restriction',NS)
        if rr is None: continue
        p=nm(rr.find('owl:onProperty',NS).get(R+'resource'))
        sv=rr.find('owl:someValuesFrom',NS)
        if sv is None: continue
        if sv.get(R+'resource'):
            out[p]={nm(sv.get(R+'resource'))}
        else:
            u=sv.find('.//owl:unionOf',NS)
            out[p]={nm(d.get(R+'about')) for d in u} if u is not None else set()
    return out

def effective(cid, seen=None):
    """Restrictions on cid, falling back to the nearest ancestor that declares them."""
    seen=seen or set()
    if cid in seen: return {}
    seen.add(cid)
    out=dict(declared(cid))
    ch=node.get(cid)
    if ch is not None:
        for s in ch.findall('rdfs:subClassOf',NS):
            res=s.get(R+'resource')
            if not res: continue
            for k,v in effective(res.split('/')[-1], seen).items():
                out.setdefault(k,v)          # own restriction wins over inherited
    return out

viol=checked=skipped=0
for cid,ch in node.items():
    if ch.find('owl:deprecated',NS) is not None: continue
    allowed=effective(cid)
    examples=ch.findall('obo:IAO_0000112',NS)
    if not examples: continue
    if 'has subject' not in allowed and 'has object' not in allowed:
        if any('SOURCE:' in (e.text or '') for e in examples): skipped+=1
        continue
    for e in examples:
        for ln in (e.text or '').split('\n'):
            for slot,key in (('SOURCE','has subject'),('TARGET','has object')):
                for m in re.finditer(slot+r':\s*"[^"]*"\s*=>\s*([^;=>]+)', ln):
                    t=m.group(1).strip().rstrip('.').strip()
                    if not t or key not in allowed: continue
                    checked+=1
                    if t not in allowed[key]:
                        viol+=1
                        print(f"  {cid} {lab.get(cid)!r}")
                        print(f"     {slot} allowed: {sorted(allowed[key])}")
                        print(f"     example says: {t!r}   |  {ln.strip()[:95]}")

print(f"\nchecked {checked} SOURCE/TARGET assignments; {viol} contradict the restriction")
if skipped:
    print(f"({skipped} class(es) with examples but no declared or inherited subject/object restriction)")
sys.exit(1 if viol else 0)
