#!/usr/bin/env python3
# make_chunk_all.py — ultra-simple, multi-formats
# 1) Place this script on your machine.
# 2) cd DANS le dossier à indexer (ex: images/ ou zips/).
# 3) Exécute:  python make_chunk_all.py --url-prefix /images/        (ou /zips/, /videos/, etc.)
#    (ajoute --recursive pour parcourir les sous-dossiers)
# 4) Le script écrit chunk.json avec un *tableau d'items* prêt à coller dans "items" de manifest.json.
#
# Aucun package externe requis. Fonctionne sous Python 3.8+.
#
# Catégories produites (compatibles avec ta page HTML):
#   pdf, image, video, audio, zip, md, script, other
#
# Exemples:
#   cd ./pdfs && python make_chunk_all.py --url-prefix /pdfs/
#   cd ./images && python make_chunk_all.py --url-prefix /images/ --recursive
#   cd ./zips && python make_chunk_all.py --url-prefix /zips/ --include *.zip,*.7z
#
import argparse, os, json, time, re, fnmatch
from pathlib import Path

# --- Mapping extension -> type (limiter volontairement aux catégories supportées par ta page) ---
TYPE_BY_EXT = {
    # documents
    ".pdf":"pdf", ".md":"md", ".markdown":"md", ".txt":"md", ".rtf":"md",
    # images
    ".png":"image", ".jpg":"image", ".jpeg":"image", ".gif":"image", ".webp":"image", ".svg":"image", ".bmp":"image",
    # vidéos
    ".mp4":"video", ".webm":"video", ".mov":"video", ".mkv":"video", ".avi":"video",
    # audio
    ".mp3":"audio", ".ogg":"audio", ".wav":"audio", ".flac":"audio", ".m4a":"audio",
    # archives / packs
    ".zip":"zip", ".7z":"zip", ".rar":"zip", ".tar":"zip", ".gz":"zip", ".xz":"zip",
    # scripts / code (catégorisés en 'script' pour ton UI)
    ".sh":"script", ".py":"script", ".js":"script", ".ts":"script", ".lua":"script", ".rb":"script", ".php":"script",
    ".bat":"script", ".ps1":"script", ".pl":"script", ".go":"script", ".rs":"script", ".c":"script", ".cpp":"script",
    ".java":"script", ".cs":"script", ".html":"script", ".css":"script", ".scss":"script", ".json":"script", ".xml":"script",
    ".yml":"script", ".yaml":"script", ".ini":"script"
    # Tout le reste tombera en 'other'
}

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "-", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "item"

def human_title_from_filename(stem: str) -> str:
    s = stem.replace("_", " ")
    s = re.sub(r"[-]+", " ", s)
    return " ".join(w[:1].upper() + w[1:] if w else w for w in s.split())

def detect_type(p: Path) -> str:
    return TYPE_BY_EXT.get(p.suffix.lower(), "other")

def match_any(name: str, patterns):
    if not patterns: return True
    for pat in patterns:
        if fnmatch.fnmatch(name, pat): return True
    return False

def main():
    ap = argparse.ArgumentParser(description="Créer un chunk JSON multi-formats pour manifest.json.")
    ap.add_argument("--url-prefix", default="/", help="Préfixe d'URL à prépendre (ex: /pdfs/, /images/).")
    ap.add_argument("--out", default="chunk.json", help="Nom du fichier de sortie.")
    ap.add_argument("--recursive", action="store_true", help="Inclure aussi les sous-dossiers.")
    ap.add_argument("--include", default="", help="Patterns à inclure (ex: '*.pdf,*.png'). Vide = tout.")
    ap.add_argument("--exclude", default="", help="Patterns à exclure (ex: '*.tmp,*.part').")
    ap.add_argument("--add-type-tag", action="store_true", help="Ajoute le type comme tag (ex: ['pdf']).")
    ap.add_argument("--extra-tag", default="", help="Tag additionnel pour tous les items (ex: 'catalogue').")
    args = ap.parse_args()

    here = Path(".").resolve()
    files = []
    if args.recursive:
        files = [p for p in here.rglob("*") if p.is_file()]
    else:
        files = [p for p in here.iterdir() if p.is_file()]

    inc = [s.strip() for s in args.include.split(",") if s.strip()]
    exc = [s.strip() for s in args.exclude.split(",") if s.strip()]

    items = []
    for p in sorted(files, key=lambda x: x.name.lower()):
        name = p.name
        # Filtrage include/exclude (sur le nom relatif)
        if inc and not match_any(name, inc): 
            continue
        if exc and match_any(name, exc):
            continue

        t = detect_type(p)
        st = p.stat()
        rel_name = p.name if not args.recursive else str(p.relative_to(here)).replace("\\","/")
        url = (args.url_prefix.rstrip("/") + "/" + rel_name).replace("//","/")
        if not url.startswith("/"):
            url = "/" + url

        tags = []
        if args.add_type_tag:
            tags.append(t)
        if args.extra_tag:
            tags.append(args.extra_tag)

        item = {
            "id": slugify(p.stem),
            "title": human_title_from_filename(p.stem),
            "description": "",
            "note": "",
            "url": url,
            "type": t,
            "size": st.st_size,
            "tags": tags,
            "created": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime))
        }
        items.append(item)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"OK: wrote {args.out} with {len(items)} items.")
    print("→ Ouvre ce fichier et colle le tableau dans 'items' de ton manifest.json.")
    print("Astuce: utilise --add-type-tag pour avoir automatiquement ['image'], ['video'], etc.")

if __name__ == "__main__":
    main()
