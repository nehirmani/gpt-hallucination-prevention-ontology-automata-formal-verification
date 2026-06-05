# GPT Halüsinasyonlarının Önlenmesi : Ontoloji Tabanlı ve Otomata Destekli Biçimsel Doğrulama Sistemi

> **Biçimsel Diller ve Otomatlar Dersi — Grup B, 2. Proje Grubu**  
> Eskişehir Osmangazi Üniversitesi — Bilgisayar Mühendisliği

---

## Ekip

| İsim | Rol |
|------|-----|
| Nehir Mani | Proje Yöneticisi |
| Semiha Berra Açıkgöz | PDA Tasarımı |
| Anıl Akyürek | Ontoloji Geliştirme |
| Dilara Sunaç | Pipeline ve DFA/CFG İmplementasyonu |

---

## Proje Hakkında

Bu proje, GPT gibi büyük dil modellerinin ürettiği **halüsinasyonları (yanlış bilgileri)** tespit edip düzeltmeyi amaçlar. Çalışma alanı olarak **1901–2000 yılları arasında Nobel ödülü kazanan Fizik ve Kimya bilim insanları** seçilmiştir.

### Sistem Akışı

```
LLM cümle üretir
      ↓
spaCy ile özne/yıl çıkarılır
      ↓
Ontoloji + Wikidata ile doğrulanır
      ↓
DFA karar verir → VERIFIED / SUSPICIOUS / REJECTED
```

---

## Kurulum

```bash
pip install spacy rdflib SPARQLWrapper requests nltk
python -m spacy download en_core_web_sm
```

Ollama ile test için [ollama.ai](https://ollama.ai) adresinden Ollama kurulup aşağıdaki komut çalıştırılmalıdır:

```bash
ollama run llama3.2
```

---

## Çalıştırma

```bash
python pipeline.py
```

---

## Dosya Yapısı

| Dosya | Açıklama |
|-------|----------|
| `dfa.py` | DFA sınıfı (5-demet tanımlı deterministik sonlu otomat) |
| `cfg_parser.py` | CFG gramer kuralları ve NLTK parser |
| `pipeline.py` | Ana pipeline (`kontrol_et_v2`, `halusinasyon_onle`, Ollama entegrasyonu) |
| `ontoloji_v2_final.ttl` | Nobel kazananları ontolojisi (574 triple, 135 kişi) |
| `wikidata_sozlugu.json` | İsim → Wikidata ID eşleme sözlüğü |
| `spacy_FİNAL_demo.ipynb` | Jupyter Notebook — demo versiyonu (tüm kodlar ve test sonuçları) |
| `pda.jff` | PDA tasarımı (JFLAP formatında) |

---

## Ders Kavramları

- **DFA** — Doğrulama kararı: `tam_esleme → q_verified`, `kismi_esleme → q_suspicious`
- **CFG** — Cümle yapısı analizi: `S → NP VP`, `NP → N N`, ...
- **Ontoloji (RDF)** — Nobel kazananları bilgi grafiği
