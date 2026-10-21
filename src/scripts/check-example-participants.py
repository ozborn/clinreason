"""QC: every SOURCE/TARGET named in a contextual example must be permitted by the
association's own has_subject / has_object restriction."""
import xml.etree.ElementTree as ET, re, sys
NS={'rdfs':'http://www.w3.org/2000/01/rdf-schema#','obo':'http://purl.obolibrary.org/obo/','owl':'http://www.w3.org/2002/07/owl#'}
R='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
r=ET.parse('src/ontology/clco-edit.owl').getroot()
lab={}
for ch in r:
    i=(ch.get(R+'about') or '').split('/')[-1]; l=ch.findtext('rdfs:label',None,NS)
    if i and l: lab[i]=l
def nm(x):
    x=(x or '').split('/')[-1]; return lab.get(x,x)
viol=0; checked=0
for ch in r:
    cid=(ch.get(R+'about') or '').split('/')[-1]
    allowed={}
    for s in ch.findall('rdfs:subClassOf',NS):
        rr=s.find('owl:Restriction',NS)
        if rr is None: continue
        p=nm(rr.find('owl:onProperty',NS).get(R+'resource'))
        sv=rr.find('owl:someValuesFrom',NS)
        if sv is None: continue
        if sv.get(R+'resource'): allowed[p]={nm(sv.get(R+'resource'))}
        else:
            u=sv.find('.//owl:unionOf',NS)
            allowed[p]={nm(d.get(R+'about')) for d in u} if u is not None else set()
    if 'has subject' not in allowed and 'has object' not in allowed: continue
    for e in ch.findall('obo:IAO_0000112',NS):
        for ln in (e.text or '').split('\n'):
            for slot,key in (('SOURCE','has subject'),('TARGET','has object')):
                for m in re.finditer(slot+r':\s*"[^"]*"\s*=>\s*([^;=>]+)', ln):
                    t=m.group(1).strip().rstrip('.').strip()
                    if not t or key not in allowed: continue
                    checked+=1
                    if t not in allowed[key]:
                        viol+=1
                        print(f"  {cid} {lab.get(cid)!r}")
                        print(f"     {slot} declared: {sorted(allowed[key])}")
                        print(f"     example says: {t!r}   |  {ln.strip()[:95]}")
print(f"\nchecked {checked} SOURCE/TARGET assignments; {viol} contradict the class's own restriction")
sys.exit(1 if viol else 0)
