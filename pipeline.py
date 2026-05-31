# Ana Pipeline - Halusinasyon Tespit ve Onleme Sistemi
# Bicimsel Diller ve Otomatlar dersi - Grup B, Proje 2
#
# Kullanim:
#   python pipeline.py
#
# Gerekli kutuphaneler:
#   pip install spacy rdflib SPARQLWrapper requests
#   python -m spacy download en_core_web_sm
#
# Gerekli dosyalar (ayni klasorde olmali):
#   - ontoloji_v2_final.ttl
#   - wikidata_sozlugu.json
#
# Ollama testi icin:
#   - Ollama kurulu ve calisir olmali (ollama run llama3.2)

import spacy
import json
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, URIRef, Literal
from dfa import DFA

# ── Yuklemeler ──
nlp = spacy.load("en_core_web_sm")

with open("wikidata_sozlugu.json", "r", encoding="utf-8") as f:
    wikidata_idler = json.load(f)

g = Graph()
g.parse("ontoloji_v2_final.ttl", format="turtle")
NS = Namespace("http://nobelproje.org/")

print(f"Sistem hazir! Triple: {len(g)}, Kisi: {len(wikidata_idler)}")


# ── Yardimci Fonksiyonlar ──

def cumleden_dal_bul(cumle):
    """Cumleden Nobel dalini cikar (Physics/Chemistry)"""
    if "Chemistry" in cumle:
        return "chemistry"
    elif "Physics" in cumle:
        return "physics"
    return None


def rdflib_kontrol(ozne, yil):
    """Ontolojide ozneyi arayip wikidataID dondur"""
    for s, p, o in g:
        if str(p) == str(NS.isim) and str(o) == ozne:
            kisi_uri = s
            for s2, p2, o2 in g:
                if s2 == kisi_uri and str(p2) == str(NS.wikidataID):
                    return str(o2)
    return None


def rdflib_nobel_yili(ozne, dal):
    """Ontolojiden direkt Nobel yilini bul (wikidataID gerekmez)"""
    for s, p, o in g:
        if str(p) == str(NS.isim) and str(o) == ozne:
            kisi_uri = s
            for s2, p2, o2 in g:
                if s2 == kisi_uri and str(p2) == str(NS.nobelYili):
                    return str(o2)
    return None


def wikidata_nobel_yili(wikidata_id, dal):
    """Wikidata SPARQL sorgusu ile Nobel yilini bul"""
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


def ollama_cumle_uret(konu, sayi=3):
    """Ollama (Llama 3.2) ile test cumlesi uret"""
    prompt = f'Write exactly {sayi} numbered sentences about {konu} and the Nobel Prize. Every sentence must mention a Nobel Prize year. Each sentence must start with the full name.'
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={'model': 'llama3.2', 'prompt': prompt, 'stream': False}
    )
    return response.json()['response']


# ── Ana Fonksiyonlar ──

def kontrol_et_v2(cumle):
    """
    Cumleyi analiz edip dogrulama karari ver.
    Donus: (ozne, yil, gercek_yil, karar)
    Karar: VERIFIED / SUSPICIOUS / REJECTED / KAPSAM DISI
    """
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

    # Once ontolojiden direkt Nobel yili ara
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


def halusinasyon_onle(cumle):
    """Cumleyi kontrol et, yanlissa duzelt"""
    ozne, yil, gercek_yil, karar = kontrol_et_v2(cumle)
    if karar == "VERIFIED":
        print("VERIFIED  :", cumle)
    elif karar == "SUSPICIOUS" and gercek_yil:
        duzeltilmis = cumle.replace(yil, gercek_yil)
        print("DUZELTILDI:", duzeltilmis)
        print("  (Orijinal:", cumle, ")")
    else:
        print("DOGRULANAMADI:", cumle)


# ── Test ──

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ELLE TEST")
    print("=" * 60)

    test_cumleler = [
        "Albert Einstein won the Nobel Prize in Physics in 1921.",
        "Albert Einstein won the Nobel Prize in Physics in 1925.",
        "Marie Curie won the Nobel Prize in Chemistry in 1911.",
        "Marie Curie won the Nobel Prize in Chemistry in 1906.",
    ]

    for cumle in test_cumleler:
        halusinasyon_onle(cumle)
        print()

    # Ollama testi (Ollama calisiyorsa)
    try:
        print("=" * 60)
        print("OLLAMA TESTI")
        print("=" * 60)
        for konu in ['Albert Einstein', 'Niels Bohr', 'Max Planck']:
            ham = ollama_cumle_uret(konu, 3)
            cumleler = [c.strip() for c in ham.split('\n') if len(c.strip()) > 15]
            cumleler = [c[3:].strip() if len(c) > 2 and c[0].isdigit() and c[1] == '.' else c for c in cumleler]
            cumleler = [c for c in cumleler if not c.startswith('Here are')]
            print(f"\n--- {konu} ---")
            for cumle in cumleler:
                halusinasyon_onle(cumle)
    except:
        print("Ollama calismıyor, Ollama testi atlandi.")
