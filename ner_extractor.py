# -*- coding: utf-8 -*-
"""
Type-4 belgelerde SADECE şirket adı çıkarımı.
- NER modeli çalıştırılır (ORG) -> aynı satır tokenlarını birleştir -> başlık/hard-negative & trivial filtrele
- Güçlü aday varsa en iyi skorlu olan döner
- Yoksa birleştirilmiş adayların en iyisi döner
"""

import re
try:
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline as hf_pipeline
    _HF_AVAILABLE = True
except Exception:
    _HF_AVAILABLE = False

# ==================== Model ====================
NER_MODEL = "akdeniz27/mDeBERTa-v3-base-turkish-ner"

# ==================== Yardımcılar ====================
_TR_MAP = str.maketrans({
    "İ":"I","I":"I","ı":"i","ş":"s","Ş":"S","ç":"c","Ç":"C",
    "ğ":"g","Ğ":"G","ü":"u","Ü":"U","ö":"o","Ö":"O",
})
def _norm_tr(s: str) -> str:
    return (s or "").translate(_TR_MAP).upper()

COMPANY_SUFFIX_HINTS = {"LTD","LTD.","ŞTİ","AŞ","A.Ş.","ANONİM","LİMİTED","KOOP","VAKFI","DERNEĞİ","ODASI"}
SECTOR_HINTS = {"TARIM","ZİRAAT","SERACILIK","GIDA","SANAY","TİC","PAZARLAMA","İNŞ","YATIRIM","MÜHENDİSLİK","ENERJİ"}
CERTIFIER_NOISE = {"KONTROL","SERTİFİKASYON","BELGELENDİR"}
HARD_NEGATIVE = {"IYI TARIM UYGULAMALARI","YONETMELIK","SERTIFIKASI","ISO","TS","RESMI GAZETE"}

def _clean(s: str) -> str:
    s = (s or "").replace("##","")
    s = re.sub(r"\s+"," ",s)
    return s.strip(" -–—·•\t\r\n ")

def _is_hard_negative(s: str) -> bool:
    return any(kw in _norm_tr(s) for kw in HARD_NEGATIVE)

def _is_trivial_company_token(s: str) -> bool:
    up = _norm_tr(_clean(s))
    return up in {"SIRKET","SIRKETI","ANONIM","LTD","AS","LIMITED","COMPANY"}

def _line_starts(text: str):
    acc, starts = 0,[]
    for ln in text.splitlines(True):
        starts.append(acc); acc += len(ln)
    return starts

def _offset_to_line(starts, off: int) -> int:
    idx=0
    for i,st in enumerate(starts):
        if st<=off: idx=i
        else: break
    return idx

# ==================== NER birleştirme ====================
def merge_org_tokens_same_line(ents, text):
    starts = _line_starts(text)
    def off2line(off): return _offset_to_line(starts, int(off))

    per_line={}
    for e in ents:
        if (e.get("entity_group") or e.get("entity"))!="ORG": continue
        ln=off2line(e.get("start",0))
        per_line.setdefault(ln,[]).append({
            "s":int(e.get("start",0)),
            "e":int(e.get("end",0)),
            "score":float(e.get("score",0.0)),
            "txt":_clean(e.get("word","")),
        })

    merged=[]
    for ln,items in per_line.items():
        items.sort(key=lambda x:x["s"])
        buf=None
        for it in items:
            if not buf: buf=it; continue
            gap=it["s"]-buf["e"]
            if gap<=2:
                buf["txt"]=(buf["txt"]+" "+it["txt"]).strip()
                buf["e"]=it["e"]
                buf["score"]=max(buf["score"],it["score"])
            else:
                merged.append(buf); buf=it
        if buf: merged.append(buf)

    outs=[]
    for m in merged:
        t=m["txt"]
        if not t or _is_hard_negative(t) or _is_trivial_company_token(t): continue
        outs.append((m["score"],t))

    uniq,seen=[],set()
    for sc,t in sorted(outs,key=lambda x:x[0],reverse=True):
        k=_norm_tr(t)
        if k not in seen:
            seen.add(k); uniq.append((sc,t))
    return uniq

def _rank_org_candidates(org_ents, text):
    merged=merge_org_tokens_same_line(org_ents,text)
    ranked=[]
    for sc,txt in merged:
        up=_norm_tr(txt)
        if not any(s in up for s in COMPANY_SUFFIX_HINTS|SECTOR_HINTS): continue
        score=sc+0.35*(any(s in up for s in COMPANY_SUFFIX_HINTS))+0.2*(any(s in up for s in SECTOR_HINTS))
        ranked.append((score,txt))
    ranked.sort(reverse=True,key=lambda x:x[0])
    return ranked

def _accept_ner_company(txt:str)->bool:
    if not txt: return False
    u=_norm_tr(txt)
    if _is_hard_negative(u): return False
    if any(k in u for k in CERTIFIER_NOISE): return False
    return any(s in u for s in COMPANY_SUFFIX_HINTS)

# ==================== Model yükleme ====================
def _try_load_model(name: str):
    tok=AutoTokenizer.from_pretrained(name)
    mdl=AutoModelForTokenClassification.from_pretrained(name)
    return hf_pipeline("ner", model=mdl, tokenizer=tok, aggregation_strategy="simple")

# ==================== Ana fonksiyon ====================
def extract_name(text: str) -> str:
    text=text or ""
    ner=_try_load_model(NER_MODEL)
    ents=ner(text)

    merged_ranked=_rank_org_candidates(ents,text)
    print("🔎 Birleştirilmiş:",merged_ranked)

    ner_strong=[(sc,t) for (sc,t) in merged_ranked if _accept_ner_company(t)]
    print("✅ Güçlü adaylar:",ner_strong)

    # Tek seçim: güçlü aday varsa en iyisini, yoksa birleştirilmişten en iyisini döndür
    if ner_strong:
        return ner_strong[0][1]
    elif merged_ranked:
        return merged_ranked[0][1]
    return None

# Alias
def extract_company_type4(text: str) -> str:
    return extract_name(text)
