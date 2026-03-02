# -*- coding: utf-8 -*-
"""
Local Windows version of: Final_model_integration_with_location.ipynb

- Stage A (informative): A-text + optional A-image -> fused prob -> threshold
- If informative:
    - Location extraction + geocoding (text-only)
    - Stage B (disaster type): B-text + optional B-image -> fused probs -> final label
- Text is REQUIRED; image is OPTIONAL

MODIFIED:
- Made model loading lazy (init_models()) so DB runner can import safely.
- Added helper to return stage probs needed by DB storage.
"""

import os
import json
import re
import string
import math
import html
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms

import sentencepiece as spm
import ftfy
import emoji as emoji_lib
import contractions

# NLTK (used in dependency checks)
import nltk
from transformers import AutoTokenizer, AutoModelForSequenceClassification  # kept for compatibility


# ============================================================
# 0) Dependency checks (LOCAL-SAFE)
# ============================================================
def ensure_runtime_deps() -> None:
    """
    Local-safe dependency checks:
    - Ensures NLTK resources exist (punkt, stopwords, punkt_tab)
    - Ensures spaCy model exists for location NER (en_core_web_sm)
    - Ensures geopy is importable for geocoding
    """
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)

    for res in ["punkt", "punkt_tab"]:
        try:
            nltk.data.find(f"tokenizers/{res}")
        except LookupError:
            nltk.download(res, quiet=True)

    # spaCy model
    try:
        import spacy  # noqa
        try:
            spacy.load("en_core_web_sm")
        except Exception:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' is missing.\n"
                "Run:\n"
                "  python -m spacy download en_core_web_sm\n"
            )
    except ImportError:
        raise RuntimeError(
            "spaCy is not installed.\n"
            "Install:\n"
            "  pip install spacy\n"
            "Then:\n"
            "  python -m spacy download en_core_web_sm\n"
        )

    # geopy
    try:
        import geopy  # noqa
    except ImportError:
        raise RuntimeError(
            "geopy is not installed.\n"
            "Install:\n"
            "  pip install geopy\n"
        )


ensure_runtime_deps()


# ============================================================
# 0.5) Device
# ============================================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)


# ============================================================
# 1) PATHS (YOUR LOCAL WINDOWS FOLDERS)
# ============================================================
MODELS_BASE = r"D:\F_PROJECT(BackUp)\FINAL\disaster_dashboard_full\models"

A_TEXT_DIR  = os.path.join(MODELS_BASE, "final_task1a_text_custom_transformer_MOD_1")
A_IMAGE_DIR = os.path.join(MODELS_BASE, "custom_task1a_image_fromscratch_v2")

B_TEXT_SAVE_DIR = os.path.join(MODELS_BASE, "task1b_custom_text", "final_custom_transformer_4class")
B_TEXT_SP_DIR = os.path.join(MODELS_BASE, "spm_tokenizer_4class")  # kept (unused)
B_IMAGE_DIR = os.path.join(MODELS_BASE, "task01b_image_research_v2")


# ============================================================
# 2) Common helpers
# ============================================================
def prob_to_confidence_1to10(p: float) -> int:
    p = float(np.clip(p, 0.0, 1.0))
    return int(np.clip(round(p * 9 + 1), 1, 10))


# ============================================================
# 3) TEXT PREPROCESS (Task A)
# ============================================================
def preprocess_text_A(text: str) -> str:
    text = str(text)
    text = ftfy.fix_text(text)
    text = html.unescape(text)
    text = text.lower()

    text = re.sub(r"(http|https)://\S+|www\.\S+", " <URL> ", text)
    text = re.sub(r"\brt\b\s*:?\s*", " ", text)
    text = re.sub(r"@\w+", " <USER> ", text)
    text = text.replace("#", "")

    text = emoji_lib.demojize(text)
    text = contractions.fix(text)

    text = re.sub(r"\b\d+(\.\d+)?\b", " <NUM> ", text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    punct = string.punctuation.replace("!", "").replace("?", "")
    text = re.sub(f"[{re.escape(punct)}]", " ", text)

    tokens = re.findall(r"<url>|<user>|<num>|[a-z_]+|[!?]", text)

    keep_short = {"no", "not", "ok", "us", "im", "we", "i"}
    tokens = [t for t in tokens if (len(t) > 2 or t in keep_short or t in {"<url>", "<user>", "<num>", "!", "?"})]

    text = " ".join(tokens)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ============================================================
# 4) Model definitions (Task A text)
# ============================================================
class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 256, dropout: float = 0.1):
        super().__init__()
        self.drop = nn.Dropout(dropout)

        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)

        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        T = x.size(1)
        x = x + self.pe[:, :T, :]
        return self.drop(x)


class TransformerTextClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        d_model: int,
        n_heads: int,
        n_layers: int,
        dim_ff: int,
        dropout: float,
        max_len: int,
        pad_id: int,
        num_classes: int = 2
    ):
        super().__init__()
        self.max_len = max_len
        self.pad_id = pad_id

        self.emb = nn.Embedding(vocab_size, d_model, padding_idx=pad_id)
        self.pos = PositionalEncoding(d_model, max_len=max_len, dropout=dropout)

        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=dim_ff,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=n_layers)
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, input_ids, attention_mask):
        if input_ids.size(1) > self.max_len:
            input_ids = input_ids[:, :self.max_len]
            attention_mask = attention_mask[:, :self.max_len]

        x = self.emb(input_ids)
        x = self.pos(x)

        key_padding_mask = (attention_mask == 0)
        x = self.encoder(x, src_key_padding_mask=key_padding_mask)

        mask = attention_mask.unsqueeze(-1).float()
        x = x * mask
        denom = mask.sum(dim=1).clamp_min(1.0)
        pooled = x.sum(dim=1) / denom

        return self.classifier(pooled)


# ============================================================
# 5) Task A image model
# ============================================================
class SEBlock_A(nn.Module):
    def __init__(self, ch, r=16):
        super().__init__()
        self.fc1 = nn.Conv2d(ch, max(1, ch // r), 1)
        self.fc2 = nn.Conv2d(max(1, ch // r), ch, 1)

    def forward(self, x):
        s = F.adaptive_avg_pool2d(x, 1)
        s = F.relu(self.fc1(s), inplace=True)
        s = torch.sigmoid(self.fc2(s))
        return x * s


class ResidualBlock_A(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1, drop=0.0):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False)
        self.bn1   = nn.BatchNorm2d(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False)
        self.bn2   = nn.BatchNorm2d(out_ch)
        self.se    = SEBlock_A(out_ch, r=16)
        self.drop  = nn.Dropout2d(drop) if drop > 0 else nn.Identity()

        self.shortcut = nn.Identity()
        if stride != 1 or in_ch != out_ch:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_ch)
            )

    def forward(self, x):
        h = F.relu(self.bn1(self.conv1(x)), inplace=True)
        h = self.drop(h)
        h = self.bn2(self.conv2(h))
        h = self.se(h)
        return F.relu(h + self.shortcut(x), inplace=True)


class AttentionPool2d_A(nn.Module):
    def __init__(self, in_ch):
        super().__init__()
        self.attn = nn.Conv2d(in_ch, 1, 1)

    def forward(self, x):
        a = self.attn(x).flatten(2)
        a = torch.softmax(a, dim=-1)
        xf = x.flatten(2)
        pooled = (xf * a).sum(dim=-1)
        return pooled, a


class DisasterNet_A(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
        )

        self.stage1 = nn.Sequential(
            ResidualBlock_A(32, 64,  stride=2, drop=0.05),
            ResidualBlock_A(64, 64,  stride=1, drop=0.05),
        )
        self.stage2 = nn.Sequential(
            ResidualBlock_A(64, 128, stride=2, drop=0.10),
            ResidualBlock_A(128,128, stride=1, drop=0.10),
        )
        self.stage3 = nn.Sequential(
            ResidualBlock_A(128,256, stride=2, drop=0.15),
            ResidualBlock_A(256,256, stride=1, drop=0.15),
        )
        self.stage4 = nn.Sequential(
            ResidualBlock_A(256,384, stride=2, drop=0.20),
            ResidualBlock_A(384,384, stride=1, drop=0.20),
        )

        self.attn_pool = AttentionPool2d_A(384)
        self.head = nn.Sequential(
            nn.LayerNorm(384),
            nn.Linear(384, 256),
            nn.GELU(),
            nn.Dropout(0.35),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        pooled, _ = self.attn_pool(x)
        return self.head(pooled)


# ============================================================
# 6) Task B image model
# ============================================================
class ConvBNAct_B(nn.Module):
    def __init__(self, in_ch, out_ch, k=3, s=1, p=1, act=nn.SiLU):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, k, s, p, bias=False)
        self.bn = nn.BatchNorm2d(out_ch)
        self.act = act()
    def forward(self, x):
        return self.act(self.bn(self.conv(x)))


class SEBlock_B(nn.Module):
    def __init__(self, ch, r=8):
        super().__init__()
        self.fc1 = nn.Conv2d(ch, ch // r, 1)
        self.fc2 = nn.Conv2d(ch // r, ch, 1)
    def forward(self, x):
        s = F.adaptive_avg_pool2d(x, 1)
        s = F.silu(self.fc1(s))
        s = torch.sigmoid(self.fc2(s))
        return x * s


class ResidualBlock_B(nn.Module):
    def __init__(self, ch, drop=0.1):
        super().__init__()
        self.c1 = ConvBNAct_B(ch, ch, 3, 1, 1)
        self.c2 = nn.Conv2d(ch, ch, 3, 1, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(ch)
        self.se = SEBlock_B(ch)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        h = self.c1(x)
        h = self.bn2(self.c2(h))
        h = self.se(h)
        h = self.drop(h)
        return F.silu(x + h)


class MHSA2D_B(nn.Module):
    def __init__(self, dim, heads=4, attn_drop=0.1, proj_drop=0.1):
        super().__init__()
        self.heads = heads
        self.qkv = nn.Linear(dim, dim * 3, bias=False)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)
        self.scale = (dim // heads) ** -0.5

    def forward(self, x):
        B, C, H, W = x.shape
        t = x.flatten(2).transpose(1, 2)
        qkv = self.qkv(t).reshape(B, -1, 3, self.heads, C // self.heads).permute(2,0,3,1,4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)
        out = (attn @ v).transpose(1,2).reshape(B, -1, C)
        out = self.proj_drop(self.proj(out))
        out = out.transpose(1,2).reshape(B, C, H, W)
        return out


class HybridDisasterNet_B(nn.Module):
    def __init__(self, num_classes=4, width=64, drop=0.2):
        super().__init__()
        self.stem = nn.Sequential(
            ConvBNAct_B(3, width, 3, 2, 1),
            ConvBNAct_B(width, width, 3, 1, 1),
        )
        self.stage1 = nn.Sequential(
            ConvBNAct_B(width, width*2, 3, 2, 1),
            ResidualBlock_B(width*2, drop=drop),
            ResidualBlock_B(width*2, drop=drop),
        )
        self.stage2 = nn.Sequential(
            ConvBNAct_B(width*2, width*4, 3, 2, 1),
            ResidualBlock_B(width*4, drop=drop),
            ResidualBlock_B(width*4, drop=drop),
        )
        self.stage3 = nn.Sequential(
            ConvBNAct_B(width*4, width*6, 3, 2, 1),
            ResidualBlock_B(width*6, drop=drop),
        )

        dim = width * 6
        self.mhsa1 = MHSA2D_B(dim=dim, heads=6)
        self.mhsa2 = MHSA2D_B(dim=dim, heads=6)

        self.norm = nn.BatchNorm2d(dim)
        self.dropout = nn.Dropout(drop)
        self.fc = nn.Linear(dim, num_classes)

    def forward(self, x):
        x = self.stem(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)

        x = x + self.mhsa1(x)
        x = x + self.mhsa2(x)

        x = F.silu(self.norm(x))
        x = F.adaptive_avg_pool2d(x, 1).flatten(1)
        x = self.dropout(x)
        return self.fc(x)


# ============================================================
# 7B) TEXT PREPROCESS (Task B)
# ============================================================
URL_RE = re.compile(r"http\S+|www\S+", re.IGNORECASE)
MULTISPACE_RE = re.compile(r"\s+")
NONASCII_RE = re.compile(r"[^\x00-\x7F]+")

def preprocess_text_B_custom(text: str) -> str:
    text = "" if text is None else str(text)
    text = text.lower()
    text = URL_RE.sub(" ", text)
    text = re.sub(r"\brt\b", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = text.replace("#", "")
    text = emoji_lib.demojize(text)
    text = NONASCII_RE.sub(" ", text)

    punct = string.punctuation.replace(":", "").replace("_", "")
    text = re.sub(f"[{re.escape(punct)}]", " ", text)

    tokens = re.findall(r"[a-z0-9_:\-]+", text)
    text = " ".join(tokens)

    text = MULTISPACE_RE.sub(" ", text).strip()
    return text


# ============================================================
# 7C) Task B Text Model (Custom Transformer)
# ============================================================
class AttnPool(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.w = nn.Linear(d_model, 1)

    def forward(self, h, mask):
        scores = self.w(h).squeeze(-1)
        scores = scores.masked_fill(mask == 0, -1e9)
        alpha = torch.softmax(scores, dim=1)
        pooled = torch.bmm(alpha.unsqueeze(1), h).squeeze(1)
        return pooled, alpha


class DisasterTransformer(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        num_classes: int = 4,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4,
        dim_ff: int = 512,
        dropout: float = 0.2,
        max_len: int = 128,
        pad_id: int = 0,
    ):
        super().__init__()
        self.pad_id = pad_id
        self.emb = nn.Embedding(vocab_size, d_model, padding_idx=pad_id)
        self.pos = PositionalEncoding(d_model, max_len=max_len, dropout=dropout)

        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_ff,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
            norm_first=True
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=num_layers)
        self.pool = AttnPool(d_model)
        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, num_classes)
        )

    def forward(self, x, attn_mask):
        h = self.emb(x)
        h = self.pos(h)

        key_padding_mask = (attn_mask == 0)
        h = self.encoder(h, src_key_padding_mask=key_padding_mask)

        pooled, alpha = self.pool(h, attn_mask)
        logits = self.head(pooled)
        return logits, alpha


# ============================================================
# 8) LOCATION PIPELINE
# ============================================================
_loc_nlp = None
_geolocator = None
_geocode_fn = None
_geocode_cache: Dict[str, Any] = {}

_LOC_PREP_WORDS = {
    "in", "at", "near", "around", "within", "inside", "outside",
    "from", "to", "into", "towards", "toward", "onto", "across"
}
_SMALL_WORDS = {
    "a","an","the","and","or","but","if","then","else","for","nor","so","yet",
    "in","on","at","near","around","within","from","to","into","towards","toward",
    "of","by","with","without","as","is","are","was","were","be","been","being",
    "we","i","you","they","he","she","it","my","our","your","their"
}

def preprocess_text_for_location(text: str) -> str:
    text = str(text)
    text = re.sub(r"(http|https)://\S+|www\.\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#(\w+)", r"\1", text)

    emoji_pattern = re.compile(
        "[" "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF" "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F" "\U0001F780-\U0001F7FF" "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF" "\U0001FA00-\U0001FAFF" "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub(" ", text)

    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    text = re.sub(r"[^A-Za-z0-9\s\.\,\-\']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ensure_spacy_model():
    global _loc_nlp
    if _loc_nlp is not None:
        return
    import spacy
    _loc_nlp = spacy.load("en_core_web_sm")


def _needs_ner_casing_fix(s: str) -> bool:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    upp = sum(1 for c in letters if c.isupper())
    return upp == 0


def _smart_title_for_ner(s: str) -> str:
    parts = re.split(r"(\s+)", s)
    out = []
    for p in parts:
        if not p or p.isspace():
            out.append(p); continue
        w = p.strip()
        if not w:
            out.append(p); continue
        if any(ch.isdigit() for ch in w):
            out.append(p); continue
        lw = w.lower()
        if lw in _SMALL_WORDS:
            out.append(lw)
        else:
            out.append(lw[:1].upper() + lw[1:])
    return "".join(out)


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        x2 = x.strip()
        if not x2:
            continue
        key = x2.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(x2)
    return out


def _extract_locations_rule_based(doc) -> List[str]:
    out: List[str] = []
    for i, tok in enumerate(doc):
        if tok.lower_ in _LOC_PREP_WORDS:
            j = i + 1
            buff = []
            while j < len(doc):
                t = doc[j]
                if t.is_punct:
                    break
                if t.pos_ in {"PROPN", "NOUN"} or (t.text in {"-", "'"}):
                    buff.append(t.text)
                    j += 1
                    continue
                if buff:
                    break
                j += 1
            phrase = " ".join(buff).strip(" ,.-")
            if phrase and len(phrase) >= 3:
                out.append(phrase)

    i = 0
    while i < len(doc):
        if doc[i].pos_ == "PROPN":
            j = i
            buff = []
            while j < len(doc) and len(buff) < 4 and doc[j].pos_ == "PROPN":
                buff.append(doc[j].text)
                j += 1
            phrase = " ".join(buff).strip(" ,.-")
            if phrase and len(phrase) >= 3:
                out.append(phrase)
            i = j
        else:
            i += 1
    return out


def extract_locations_spacy(clean_text: str) -> List[str]:
    _ensure_spacy_model()
    if not isinstance(clean_text, str) or clean_text.strip() == "":
        return []

    candidates: List[str] = []
    doc = _loc_nlp(clean_text)
    candidates += [ent.text for ent in doc.ents if ent.label_ in {"GPE", "LOC", "FAC"}]

    if len(candidates) == 0 and _needs_ner_casing_fix(clean_text):
        ner_text = _smart_title_for_ner(clean_text)
        doc2 = _loc_nlp(ner_text)
        candidates += [ent.text for ent in doc2.ents if ent.label_ in {"GPE", "LOC", "FAC"}]
        candidates += _extract_locations_rule_based(doc2)
    else:
        candidates += _extract_locations_rule_based(doc)

    return _dedupe_keep_order(candidates)


def _ensure_geocoder():
    global _geolocator, _geocode_fn
    if _geocode_fn is not None:
        return
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter

    _geolocator = Nominatim(user_agent="disaster-ner-geocoder")
    _geocode_fn = RateLimiter(_geolocator.geocode, min_delay_seconds=1, swallow_exceptions=True)


def _geocode_query(q: str):
    _ensure_geocoder()
    q = q.strip()
    if not q:
        return None
    if q in _geocode_cache:
        return _geocode_cache[q]
    geo = _geocode_fn(q)
    _geocode_cache[q] = geo
    return geo


def geocode_locations(location_list: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not isinstance(location_list, list):
        return results

    for loc in location_list:
        loc_key = str(loc).strip(" \t\n\r,.-")
        if not loc_key:
            continue

        geo = _geocode_query(loc_key)
        if geo is None:
            geo = _geocode_query(f"{loc_key}, Sri Lanka")

        if geo is not None:
            results.append({
                "name": loc_key,
                "latitude": float(geo.latitude),
                "longitude": float(geo.longitude),
            })
    return results


def infer_location_from_text(text: str) -> Dict[str, Any]:
    clean = preprocess_text_for_location(text)
    candidates = extract_locations_spacy(clean)
    geocoded = geocode_locations(candidates)

    chosen = geocoded[0] if len(geocoded) > 0 else None
    return {
        "text_clean_for_location": clean,
        "candidates": candidates,
        "geocoded_all": geocoded,
        "selected_name": (chosen["name"] if chosen else None),
        "lat": (chosen["latitude"] if chosen else None),
        "lon": (chosen["longitude"] if chosen else None),
    }


# ============================================================
# 9) Loaders + inference
# ============================================================
def load_A_text(model_dir: str):
    cfg_path  = os.path.join(model_dir, "config.json")
    spm_path  = os.path.join(model_dir, "spm_task1a.model")
    w_path    = os.path.join(model_dir, "best_model.pt")
    lm_path   = os.path.join(model_dir, "label_map.json")

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    with open(lm_path, "r", encoding="utf-8") as f:
        lm = json.load(f)

    id2label = {int(k): v for k, v in lm.get("id2label", {}).items()}

    sp = spm.SentencePieceProcessor()
    if not sp.load(spm_path):
        raise RuntimeError(f"Failed to load sentencepiece model: {spm_path}")

    pad_id = int(cfg.get("pad_id", 0))
    max_len = int(cfg["max_len"])
    mcfg = cfg["model"]

    model = TransformerTextClassifier(
        vocab_size=int(cfg["vocab_size"]),
        d_model=int(mcfg["d_model"]),
        n_heads=int(mcfg["n_heads"]),
        n_layers=int(mcfg["n_layers"]),
        dim_ff=int(mcfg["dim_ff"]),
        dropout=float(mcfg["dropout"]),
        max_len=max_len,
        pad_id=pad_id,
        num_classes=2
    ).to(device)

    model.load_state_dict(torch.load(w_path, map_location=device))
    model.eval()

    threshold = float(cfg.get("decision_threshold", 0.5))
    return model, sp, id2label, threshold, cfg


@torch.no_grad()
def infer_A_text(text: str, model, sp, cfg):
    text = preprocess_text_A(text)
    ids = sp.encode_as_ids(text)
    max_len = int(cfg["max_len"])

    ids = ids[:max_len]
    attn = [1] * len(ids)

    pad_id = int(cfg.get("pad_id", 0))
    if len(ids) < max_len:
        pad_n = max_len - len(ids)
        ids = ids + [pad_id] * pad_n
        attn = attn + [0] * pad_n

    input_ids = torch.tensor(ids).unsqueeze(0).to(device)
    attention_mask = torch.tensor(attn).unsqueeze(0).to(device)

    logits = model(input_ids, attention_mask)
    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
    return probs  # [p(not_info), p(info)]


def load_A_image(model_dir: str):
    w_path  = os.path.join(model_dir, "disasternet_v2_fromscratch.pt")
    lm_path = os.path.join(model_dir, "label_map.json")
    cfg_path= os.path.join(model_dir, "config.json")

    with open(lm_path, "r", encoding="utf-8") as f:
        lm = json.load(f)
    id2label = {int(k): v for k, v in lm["id2label"].items()}

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    img_size = int(cfg.get("img_size", 224))
    eval_tfms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])

    model = DisasterNet_A(num_classes=2).to(device)
    model.load_state_dict(torch.load(w_path, map_location=device))
    model.eval()

    return model, id2label, eval_tfms


@torch.no_grad()
def infer_A_image(image_path: str, model, tfms):
    img = Image.open(image_path).convert("RGB")
    x = tfms(img).unsqueeze(0).to(device)
    logits = model(x)
    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
    return probs  # [p(not_info), p(info)]


def _encode_sp_B(sp_local, text: str, max_len: int):
    ids = sp_local.encode(text, out_type=int)
    ids = ids[: max_len - 1] + [sp_local.eos_id()]

    if len(ids) < max_len:
        ids = ids + [sp_local.pad_id()] * (max_len - len(ids))

    attn = [0 if i == sp_local.pad_id() else 1 for i in ids]
    return np.array(ids, dtype=np.int64), np.array(attn, dtype=np.int64)


def load_B_text(save_dir: str, sp_dir_unused: str = None):
    cfg_path = os.path.join(save_dir, "config.json")
    spm_path = os.path.join(save_dir, "spm.model")
    w_path   = os.path.join(save_dir, "model.pt")

    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"config.json not found at: {cfg_path}")
    if not os.path.exists(spm_path):
        raise FileNotFoundError(f"spm.model not found at: {spm_path}")
    if not os.path.exists(w_path):
        raise FileNotFoundError(f"model.pt not found at: {w_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    sp_local = spm.SentencePieceProcessor()
    ok = sp_local.load(spm_path)
    if not ok:
        raise RuntimeError(f"Failed to load sentencepiece model: {spm_path}")

    id2label_raw = cfg.get("id2label", {})
    id2label = {int(k): v for k, v in id2label_raw.items()}

    arch = cfg["arch"]
    max_len = int(cfg["max_len"])
    pad_id = int(sp_local.pad_id())

    model = DisasterTransformer(
        vocab_size=int(sp_local.get_piece_size()),
        num_classes=4,
        d_model=int(arch["d_model"]),
        nhead=int(arch["nhead"]),
        num_layers=int(arch["num_layers"]),
        dim_ff=int(arch["dim_ff"]),
        dropout=float(arch["dropout"]),
        max_len=max_len,
        pad_id=pad_id,
    ).to(device)

    model.load_state_dict(torch.load(w_path, map_location=device))
    model.eval()

    BOS_ID = int(sp_local.bos_id())
    EOS_ID = int(sp_local.eos_id())
    MAX_LEN = max_len

    return model, sp_local, id2label, cfg, BOS_ID, EOS_ID, MAX_LEN


@torch.no_grad()
def infer_B_text(text: str, model, sp_local, BOS_ID_unused, EOS_ID_unused, MAX_LEN: int):
    clean_text = preprocess_text_B_custom(text)
    x, attn = _encode_sp_B(sp_local, clean_text, max_len=MAX_LEN)
    x = torch.tensor(x).unsqueeze(0).to(device)
    attn = torch.tensor(attn).unsqueeze(0).to(device)

    logits, _ = model(x, attn)
    probs = torch.softmax(logits, dim=1).squeeze(0).detach().cpu().numpy()
    return probs


def load_B_image(model_dir: str):
    pkg_path = os.path.join(model_dir, "model_package.json")
    w_path   = os.path.join(model_dir, "student_weights.pt")

    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    id2label = {int(k): v for k, v in pkg["id2label"].items()}

    IMG_SIZE = int(pkg.get("img_size", 224))
    eval_tfms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])

    model = HybridDisasterNet_B(num_classes=4, width=64, drop=0.2).to(device)
    model.load_state_dict(torch.load(w_path, map_location=device))
    model.eval()

    return model, id2label, eval_tfms


@torch.no_grad()
def infer_B_image(image_path: str, model, tfms):
    img = Image.open(image_path).convert("RGB")
    x = tfms(img).unsqueeze(0).to(device)
    logits = model(x)
    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
    return probs


# ============================================================
# 10) Lazy global model cache
# ============================================================
_MODELS_READY = False

A_text_model = None
A_sp = None
A_id2label = None
A_threshold = None
A_text_cfg = None

A_img_model = None
A_img_id2label = None
A_img_tfms = None

B_text_model = None
B_tok = None
B_id2label = None
B_text_cfg = None
B_BOS = None
B_EOS = None
B_MAX = None

B_img_model = None
B_img_id2label = None
B_img_tfms = None


def init_models() -> None:
    """Call once before running pipeline (safe to call multiple times)."""
    global _MODELS_READY
    global A_text_model, A_sp, A_id2label, A_threshold, A_text_cfg
    global A_img_model, A_img_id2label, A_img_tfms
    global B_text_model, B_tok, B_id2label, B_text_cfg, B_BOS, B_EOS, B_MAX
    global B_img_model, B_img_id2label, B_img_tfms

    if _MODELS_READY:
        return

    A_text_model, A_sp, A_id2label, A_threshold, A_text_cfg = load_A_text(A_TEXT_DIR)
    print("Loaded A-text OK")

    A_img_model, A_img_id2label, A_img_tfms = load_A_image(A_IMAGE_DIR)
    print("Loaded A-image OK")

    B_text_model, B_tok, B_id2label, B_text_cfg, B_BOS, B_EOS, B_MAX = load_B_text(B_TEXT_SAVE_DIR, B_TEXT_SP_DIR)
    print("Loaded B-text OK")

    B_img_model, B_img_id2label, B_img_tfms = load_B_image(B_IMAGE_DIR)
    print("Loaded B-image OK")

    print("All models loaded.")
    print("A threshold:", A_threshold)
    print("B labels:", B_id2label)

    _MODELS_READY = True


# ============================================================
# 11) Full pipeline
# ============================================================
def run_full_pipeline(text: str, image_path: str = None) -> Dict[str, Any]:
    """
    text: required (text-only allowed)
    image_path: optional

    Location:
      - ONLY computed if StageA says informative
      - computed from TEXT ONLY
      - always included in output (None fields if unavailable)
    """
    init_models()

    if (text is None) or (str(text).strip() == ""):
        return {"ok": False, "error": "text is required (text-only allowed, image-only not allowed)"}

    has_image = (image_path is not None) and (str(image_path).strip() != "")
    if has_image:
        # If DB has relative paths, try to resolve to absolute if needed:
        image_path = str(image_path)
        if not os.path.isabs(image_path):
            # you can change this base if your images are stored elsewhere
            candidate = os.path.join(os.getcwd(), image_path)
            if os.path.exists(candidate):
                image_path = candidate
        if not os.path.exists(image_path):
            # treat as no image if file missing
            has_image = False
            image_path = None

    # ======================
    # Stage A: Informativeness
    # ======================
    probs_A_text = infer_A_text(text, A_text_model, A_sp, A_text_cfg)
    pA_text_info = float(probs_A_text[1])

    probs_A_img = None
    pA_img_info = None

    if has_image:
        probs_A_img = infer_A_image(image_path, A_img_model, A_img_tfms)
        pA_img_info = float(probs_A_img[1])
        pA_fused_info = (pA_text_info + pA_img_info) / 2.0
    else:
        pA_fused_info = pA_text_info

    is_informative = (pA_fused_info >= A_threshold)

    out: Dict[str, Any] = {
        "ok": True,
        "stageA": {
            "threshold": float(A_threshold),
            "text_prob_informative": pA_text_info,
            "image_prob_informative": pA_img_info,
            "fused_prob_informative": float(pA_fused_info),
            "fused_confidence_1to10": prob_to_confidence_1to10(pA_fused_info),
            "prediction": "informative" if is_informative else "not_informative",
        },
        "location": {
            "text_clean_for_location": None,
            "candidates": [],
            "geocoded_all": [],
            "selected_name": None,
            "lat": None,
            "lon": None,
            "error": None
        }
    }

    if not is_informative:
        out["discarded"] = True
        out["stageB"] = None
        return out

    out["discarded"] = False

    # ======================
    # Location (ONLY after informative; TEXT ONLY)
    # ======================
    try:
        loc_res = infer_location_from_text(text)
        out["location"].update(loc_res)
    except Exception as e:
        out["location"]["error"] = str(e)

    # ======================
    # Stage B: Disaster type
    # ======================
    probs_B_text = infer_B_text(text, B_text_model, B_tok, B_BOS, B_EOS, B_MAX)

    probs_B_img = None
    if has_image:
        probs_B_img = infer_B_image(image_path, B_img_model, B_img_tfms)
        probs_B_fused = (probs_B_text + probs_B_img) / 2.0
    else:
        probs_B_fused = probs_B_text

    pred_id = int(np.argmax(probs_B_fused))
    pred_label = B_id2label.get(pred_id, str(pred_id))
    pred_prob = float(probs_B_fused[pred_id])

    # store per-modality probability for the predicted class too
    b_text_prob_pred = float(probs_B_text[pred_id])
    b_image_prob_pred = (float(probs_B_img[pred_id]) if probs_B_img is not None else None)

    out["stageB"] = {
        "prediction_id": pred_id,
        "prediction_label": pred_label,
        "confidence_prob": pred_prob,
        "confidence_1to10": prob_to_confidence_1to10(pred_prob),
        "b_text_prob_pred": b_text_prob_pred,
        "b_image_prob_pred": b_image_prob_pred,
        "probs_fused": {B_id2label[i]: float(probs_B_fused[i]) for i in range(len(probs_B_fused))},
        "probs_text":  {B_id2label[i]: float(probs_B_text[i])  for i in range(len(probs_B_text))},
        "probs_image": ({B_id2label[i]: float(probs_B_img[i]) for i in range(len(probs_B_img))} if probs_B_img is not None else None)
    }

    return out
