# -*- coding: utf-8 -*-
"""
GPT Halusinasyon Onleme Sistemi - Demo
Bicimsel Diller ve Otomatlar Dersi - Grup B, Proje 2
"""

# ============================================================
# HUCRE 1
# ============================================================
import spacy
import json
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, URIRef, Literal

# spaCy yukle
nlp = spacy.load("en_core_web_sm")

# Wikidata sozlugu yukle
with open("wikidata_sozlugu.json", "r", encoding="utf-8") as f:
    wikidata_idler = json.load(f)
wikidata_idler["Marie Curie"] = "Q7186"

# Ontoloji yukle
g = Graph()
g.parse("ontoloji_v2_final.ttl", format="turtle")
NS = Namespace("http://nobelproje.org/")

print("Hazir!")
print("Kisi sayisi:", len(wikidata_idler))
print("Triple sayisi:", len(g))


# ============================================================
# HUCRE 2
# ============================================================
class DFA:
    def __init__(self):
        self.Q = {'q_start', 'q_verified', 'q_suspicious', 'q_rejected'}
        self.Sigma = {'tam_esleme', 'kismi_esleme', 'esleme_yok'}
        self.q0 = 'q_start'
        self.F = {'q_verified'}
        self.delta = {
    ('q_start', 'tam_esleme'): 'q_verified',
    ('q_start', 'kismi_esleme'): 'q_suspicious',
    ('q_start', 'esleme_yok'): 'q_rejected',
}
        self.mevcut_durum = self.q0

    def gecis(self, giris_sembolu):
        anahtar = (self.mevcut_durum, giris_sembolu)
        if anahtar in self.delta:
            self.mevcut_durum = self.delta[anahtar]
        else:
            self.mevcut_durum = 'q_rejected'
        return self.mevcut_durum

    def calistir(self, sinyal):
        self.mevcut_durum = self.q0
        return self.gecis(sinyal)

    def kabul_ediyor_mu(self):
        return self.mevcut_durum in self.F

dfa = DFA()
print("tam_esleme   ->", dfa.calistir('tam_esleme'))
print("kismi_esleme ->", dfa.calistir('kismi_esleme'))
print("esleme_yok   ->", dfa.calistir('esleme_yok'))

# ============================================================
# HUCRE 3
# ============================================================
def cumleden_dal_bul(cumle):
    if "Chemistry" in cumle:
        return "chemistry"
    elif "Physics" in cumle:
        return "physics"
    return None

def rdflib_kontrol(ozne, yil):
    for s, p, o in g:
        if str(p) == str(NS.isim) and str(o) == ozne:
            kisi_uri = s
            for s2, p2, o2 in g:
                if s2 == kisi_uri and str(p2) == str(NS.wikidataID):
                    return str(o2)
    return None

def rdflib_nobel_yili(ozne, dal):
    for s, p, o in g:
        if str(p) == str(NS.isim) and str(o) == ozne:
            kisi_uri = s
            for s2, p2, o2 in g:
                if s2 == kisi_uri and str(p2) == str(NS.nobelYili):
                    return str(o2)
    return None

def wikidata_nobel_yili(wikidata_id, dal):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.addCustomHttpHeader("User-Agent", "Mozilla/5.0")
    dal_filtre = f'FILTER(CONTAINS(LCASE(?odulAdi), "{dal}"))' if dal else ""
    sorgu = f"""
    SELECT ?yil WHERE {{
      wd:{wikidata_id} p:P166 ?odul_stmt .
      ?odul_stmt ps:P166 ?odul .
      ?odul rdfs:label ?odulAdi .
      FILTER(LANG(?odulAdi) = "en")
      FILTER(CONTAINS(LCASE(?odulAdi), "nobel"))
      {dal_filtre}
      OPTIONAL {{ ?odul_stmt pq:P585 ?tarih . }}
      BIND(YEAR(?tarih) AS ?yil)
    }}
    LIMIT 1
    """
    sparql.setQuery(sorgu)
    sparql.setReturnFormat(JSON)
    try:
        sonuc = sparql.query().convert()
        if sonuc["results"]["bindings"]:
            return sonuc["results"]["bindings"][0]["yil"]["value"]
    except:
        pass
    return None

def kontrol_et_v2(cumle):
    if "Nobel" not in cumle:
        return "", "", None, "KAPSAM DISI"
    doc = nlp(cumle)
    ozne = ""
    yil = ""
    for token in doc:
        if token.dep_ in ["nsubj", "nsubjpass"] and token.text != "who":
                ozne_parcalar = [t.text for t in token.subtree
                     if t.dep_ in ["compound", "nsubj", "nsubjpass", "flat"]]
                ozne = " ".join(ozne_parcalar)
        if token.text.isdigit():
            yil = token.text
    # NER yedek: dep parsing basarisiz olursa PERSON entity kullan
    if not ozne or (ozne and not wikidata_idler.get(ozne) and not rdflib_kontrol(ozne, yil)):
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                ozne = ent.text
                break
    dal = cumleden_dal_bul(cumle)
    # Once rdflib'den direkt Nobel yili ara
    gercek_yil = rdflib_nobel_yili(ozne, dal)
    # Bulamazsa Wikidata'ya sor
    if not gercek_yil:
        wikidata_id = rdflib_kontrol(ozne, yil)
        if not wikidata_id:
            wikidata_id = wikidata_idler.get(ozne)
        if not wikidata_id:
            return ozne, yil, None, "SUSPICIOUS - Kisi tanimiyor"
        gercek_yil = wikidata_nobel_yili(wikidata_id, dal)
    if not gercek_yil:
        return ozne, yil, None, "SUSPICIOUS - Wikidata verisi yok"
    # DFA ile karar
    dfa_instance = DFA()
    if yil == gercek_yil:
       sinyal = "tam_esleme"
    elif yil != gercek_yil and gercek_yil is not None:
       sinyal = "kismi_esleme"
    else:
       sinyal = "esleme_yok"
    karar = dfa_instance.calistir(sinyal)
    karar_map = {
    'q_verified': 'VERIFIED',
    'q_suspicious': 'SUSPICIOUS',
    'q_rejected': 'REJECTED'
}
    karar = karar_map.get(karar, karar)
    return ozne, yil, gercek_yil, karar
print("Fonksiyonlar tanimlandi!")

# ============================================================
# HUCRE 4
# ============================================================
def ollama_cumle_uret(konu, sayi=3):
    prompt = f'Write exactly {sayi} numbered sentences about {konu} and the Nobel Prize. Every sentence must mention a Nobel Prize year. Each sentence must start with the full name.'
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={'model': 'llama3.2', 'prompt': prompt, 'stream': False}
    )
    return response.json()['response']

print("Tanimlandi!")

# ============================================================
# HUCRE 5
# ============================================================
def halusinasyon_onle(cumle):
    ozne, yil, gercek_yil, karar = kontrol_et_v2(cumle)
    
    if karar == "VERIFIED":
        print("VERIFIED  :", cumle)
    elif karar == "SUSPICIOUS" and gercek_yil and yil:
        # Sadece tam kelime olarak yili degistir
        import re
        duzeltilmis = re.sub(r'\b' + yil + r'\b', gercek_yil, cumle)
        print("DUZELTILDI:", duzeltilmis)
        print("  (Orijinal:", cumle, ")")
    else:
        print("DOGRULANAMADI:", cumle)

# ============================================================
# HUCRE 6
# ============================================================
elle_cumleler = [
    "Albert Einstein won the Nobel Prize in Physics in 1921.",
    "Albert Einstein won the Nobel Prize in Physics in 1925.",
    "Marie Curie won the Nobel Prize in Chemistry in 1911.",
    "Marie Curie won the Nobel Prize in Chemistry in 1906.",
    "Ernest Rutherford won the Nobel Prize in Chemistry in 1908.",
    "Ernest Rutherford won the Nobel Prize in Chemistry in 1910.",
    "Max Planck won the Nobel Prize in Physics in 1918.",
    "Max Planck won the Nobel Prize in Physics in 1920.",]
print("ELLE YAZILMIS CUMLELER - TEST SONUCLARI")
print("=" * 60)
elle_sonuclar = []
for cumle in elle_cumleler:
    ozne, yil, gercek_yil, karar = kontrol_et_v2(cumle)
    elle_sonuclar.append({'Cumle': cumle, 'GPT Yili': yil, 'Gercek Yil': gercek_yil, 'Karar': karar})
    print(karar, '|', cumle)
elle_verified = len([s for s in elle_sonuclar if s['Karar'] == 'VERIFIED'])
elle_rejected = len([s for s in elle_sonuclar if s['Karar'] == 'REJECTED'])
elle_suspicious = len([s for s in elle_sonuclar if s['Karar'] == 'SUSPICIOUS'])

print(f"\nVERIFIED: {elle_verified}/8")
print(f"REJECTED: {elle_rejected}/8")
print(f"SUSPICIOUS: {elle_suspicious}/8")

# ============================================================
# HUCRE 7
# ============================================================
from nltk import CFG, ChartParser

grammar = CFG.fromstring("""
    S -> NP VP
    NP -> DET N | N N | N
    VP -> V NP | VP PP
    PP -> P NP | P N
    DET -> 'the'
    N -> 'Prize' | 'Physics' | 'Chemistry' | 'Einstein' | 'Curie'
    V -> 'won'
    P -> 'in'
""")

parser = ChartParser(grammar)
cumle = ['Einstein', 'won', 'the', 'Prize']
print("Parse agaci:")
for tree in parser.parse(cumle):
    tree.pretty_print()

# ============================================================
# HUCRE 8
# ============================================================
test_konulari = ['Albert Einstein', 'Marie Curie', 'Max Planck', 'Ernest Rutherford']
tum_sonuclar = []
for konu in test_konulari:
    print(f"Test ediliyor: {konu}...")
    ham = ollama_cumle_uret(konu, 3)
    cumleler = [c.strip() for c in ham.split('\n') if len(c.strip()) > 15]
    cumleler = [c[3:].strip() if len(c) > 2 and c[0].isdigit() and c[1] == '.' else c for c in cumleler]
    cumleler = [c for c in cumleler if not c.startswith('Here are')]
    for cumle in cumleler:
        ozne, yil, gercek_yil, karar = kontrol_et_v2(cumle)
        tum_sonuclar.append({'Cumle': cumle, 'Ozne': ozne, 'GPT Yili': yil, 'Gercek Yil': gercek_yil, 'Karar': karar})
        print(karar, '|', cumle[:55])
    print("---")
verified = len([s for s in tum_sonuclar if s['Karar'] == 'VERIFIED'])
suspicious = len([s for s in tum_sonuclar if 'SUSPICIOUS' in str(s['Karar'])])
rejected = len([s for s in tum_sonuclar if s['Karar'] == 'REJECTED'])
print(f"\nToplam: {len(tum_sonuclar)}")
print(f"VERIFIED: {verified}")
print(f"SUSPICIOUS: {suspicious}")
print(f"REJECTED: {rejected}")


# ============================================================
# HUCRE 9
# ============================================================
def halusinasyon_onle(cumle):
    ozne, yil, gercek_yil, karar = kontrol_et_v2(cumle)
    if karar == "VERIFIED":
        print("VERIFIED  :", cumle)
    elif karar == "SUSPICIOUS" and gercek_yil:
        duzeltilmis = cumle.replace(yil, gercek_yil)
        print("DUZELTILDI:", duzeltilmis)
        print("  (Orijinal:", cumle, ")")
    else:
        print("DOGRULANAMADI:", cumle)
test_cumleler = [
    "Albert Einstein won the Nobel Prize in Physics in 1921.",
    "Albert Einstein won the Nobel Prize in Physics in 1925.",
    "Marie Curie won the Nobel Prize in Chemistry in 1911.",
    "Marie Curie won the Nobel Prize in Chemistry in 1906.",]
print("=" * 60)
print("HALUSINASYON ONLEME SISTEMI")
print("=" * 60)
for cumle in test_cumleler:
    halusinasyon_onle(cumle)
    print()

# ============================================================
# HUCRE 10
# ============================================================
print("=" * 60)
print("OLLAMA - HALUSINASYON ONLEME SISTEMI")
print("=" * 60)
for konu in ['Albert Einstein', 'Niels Bohr', 'Max Planck']:
    ham = ollama_cumle_uret(konu, 3)
    cumleler = [c.strip() for c in ham.split('\n') if len(c.strip()) > 15]
    cumleler = [c[3:].strip() if len(c) > 2 and c[0].isdigit() and c[1] == '.' else c for c in cumleler]
    cumleler = [c for c in cumleler if not c.startswith('Here are')]
    print(f"\n--- {konu} ---")
    for cumle in cumleler:
        halusinasyon_onle(cumle)

# ============================================================
# HUCRE 11
# ============================================================

