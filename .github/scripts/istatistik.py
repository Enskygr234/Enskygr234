"""Profil için neon temalı istatistik ve dil kartları çizer (dış servis gerektirmez).

Çıktı: dist/istatistik.svg (açık repo, yıldız, katkı, commit, yayın)
       dist/diller.svg (en çok kullanılan diller, açık repolardaki kod baytına göre)

Kullanım: python istatistik.py
  REPOLAR="a,b,c" ortam değişkeni verilirse kullanıcı listesi yerine bu repolar okunur.
Veri alınamazsa eski kartlar olduğu gibi bırakılır.
"""
import json
import os
import re
import urllib.request

KULLANICI = "Enskygr234"
CIKTI = "dist"

DIL_RENK = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26", "CSS": "#663399",
    "Python": "#3572A5", "Java": "#b07219", "Kotlin": "#A97BFF", "C#": "#178600",
    "C++": "#f34b7d", "C": "#555555", "Shell": "#89e051", "PowerShell": "#012456",
    "GDScript": "#355570", "Dart": "#00B4AB", "Vue": "#41b883", "Batchfile": "#C1F12E",
    "ShaderLab": "#222c37", "HLSL": "#aace60", "GLSL": "#5686a5", "Lua": "#000080",
}
GIZLE = {"Batchfile", "Procfile", "Dockerfile", "Makefile"}

# Neon tema: siyah / koyu lacivert zemin, neon mavi ve mor vurgular
T = {"zemin1": "#070c1c", "zemin2": "#03050c", "kutu": "#0b1328", "kutu_kenar": "#18244a",
     "yazi": "#e6edf7", "soluk": "#7d8aa6", "mavi": "#00d4ff", "mor": "#a855f7", "ray": "#111a33"}


def api(yol):
    basliklar = {"Accept": "application/vnd.github+json", "User-Agent": "profil-istatistik"}
    if os.environ.get("GITHUB_TOKEN"):
        basliklar["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    url = yol if yol.startswith("http") else "https://api.github.com/" + yol
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=basliklar), timeout=30) as c:
            return json.load(c)
    except Exception as hata:
        print("API olmadı:", yol, hata)
        return None


def graphql(sorgu, degiskenler):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    istek = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": sorgu, "variables": degiskenler}).encode(),
        headers={"Authorization": "Bearer " + token, "User-Agent": "profil-istatistik",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=30) as c:
            return json.load(c).get("data")
    except Exception as hata:
        print("GraphQL olmadı:", hata)
        return None


def repolari_al():
    adlar = [a.strip() for a in os.environ.get("REPOLAR", "").split(",") if a.strip()]
    if adlar:
        return [r for r in (api(f"repos/{KULLANICI}/{a}") for a in adlar) if r]
    repolar, sayfa = [], 1
    while True:
        parca = api(f"users/{KULLANICI}/repos?per_page=100&type=owner&page={sayfa}")
        if not parca:
            break
        repolar += parca
        if len(parca) < 100:
            break
        sayfa += 1
    return repolar


def katki_al():
    veri = graphql("""query($u:String!){user(login:$u){contributionsCollection{
        totalCommitContributions restrictedContributionsCount
        contributionCalendar{totalContributions}}}}""", {"u": KULLANICI})
    if veri and veri.get("user"):
        k = veri["user"]["contributionsCollection"]
        return k["contributionCalendar"]["totalContributions"], k["totalCommitContributions"] + k["restrictedContributionsCount"]
    # Yedek: karlı katkı grafiğindeki toplamı oku
    try:
        with open(os.path.join(CIKTI, "kar-koyu.svg"), encoding="utf-8") as f:
            m = re.search(r"Son bir yılda ([\d.,]+) katkı", f.read())
            if m:
                return int(re.sub(r"\D", "", m.group(1))), None
    except OSError:
        pass
    return None, None


def yayin_sayisi():
    toplam, sayfa = 0, 1
    while True:
        parca = api(f"repos/{KULLANICI}/winter-browser-releases/releases?per_page=100&page={sayfa}")
        if not parca:
            break
        toplam += sum(1 for y in parca if not y.get("draft"))
        if len(parca) < 100:
            break
        sayfa += 1
    return toplam or None


def diller(repolar):
    toplam = {}
    for r in repolar:
        if r.get("fork") or r.get("archived"):
            continue
        for dil, bayt in (api(f"repos/{KULLANICI}/{r['name']}/languages") or {}).items():
            if dil not in GIZLE:
                toplam[dil] = toplam.get(dil, 0) + bayt
    hepsi = sum(toplam.values())
    if not hepsi:
        return [], None
    sirali = sorted(toplam.items(), key=lambda x: -x[1])
    ilk = [(d, b / hepsi) for d, b in sirali[:6]]
    kalan = 1 - sum(o for _, o in ilk)
    if kalan > 0.005:
        ilk.append(("Diğer", kalan))
    return ilk, len(toplam)


def sayi(n):
    return "—" if n is None else f"{n:,}".replace(",", ".")


def _ust(G, Y, etiket, baslik, alt):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {G} {Y}" width="{G}" height="{Y}" role="img" aria-label="{etiket}">',
        f"""<defs>
<linearGradient id="z" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{T['zemin1']}"/><stop offset="1" stop-color="{T['zemin2']}"/></linearGradient>
<linearGradient id="n" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{T['mavi']}"/><stop offset="1" stop-color="{T['mor']}"/></linearGradient>
<linearGradient id="kn" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{T['mavi']}" stop-opacity=".6"/><stop offset=".5" stop-color="{T['kutu_kenar']}"/><stop offset="1" stop-color="{T['mor']}" stop-opacity=".6"/></linearGradient>
<radialGradient id="isik" cx="0" cy="0" r="1"><stop offset="0" stop-color="{T['mavi']}" stop-opacity=".22"/><stop offset="1" stop-color="{T['mavi']}" stop-opacity="0"/></radialGradient>
<radialGradient id="isik2" cx="1" cy="1" r="1"><stop offset="0" stop-color="{T['mor']}" stop-opacity=".20"/><stop offset="1" stop-color="{T['mor']}" stop-opacity="0"/></radialGradient>
<clipPath id="k"><rect width="{G}" height="{Y}" rx="16"/></clipPath>
</defs>
<style>
text{{font-family:'Segoe UI',Inter,-apple-system,system-ui,Roboto,Helvetica,Arial,sans-serif}}
.m{{font-family:'JetBrains Mono','Fira Code',Consolas,'SF Mono',Menlo,monospace}}
.bs{{font-size:19px;font-weight:700;fill:{T['yazi']}}}
.alt{{font-size:12.5px;fill:{T['soluk']}}}
.dg{{font-size:31px;font-weight:800}}
.et{{font-size:14px;fill:{T['soluk']}}}
.dl{{font-size:15px;fill:{T['yazi']};font-weight:600}}
.yz{{font-size:14px;fill:{T['soluk']};font-variant-numeric:tabular-nums}}
.gir{{opacity:0;animation:g .8s ease-out forwards}}
@keyframes g{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.bar{{transform-box:fill-box;transform-origin:left center;transform:scaleX(0);animation:b 1.1s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes b{{to{{transform:scaleX(1)}}}}
.nb{{animation:nb 2.4s ease-in-out infinite}}
@keyframes nb{{50%{{opacity:.35}}}}
@media (prefers-reduced-motion:reduce){{.gir,.bar,.nb{{animation:none;opacity:1;transform:none}}}}
</style>""",
        f'<g clip-path="url(#k)"><rect width="{G}" height="{Y}" fill="url(#z)"/>'
        f'<rect width="{G}" height="{Y}" fill="url(#isik)"/><rect width="{G}" height="{Y}" fill="url(#isik2)"/>',
        f'<rect x=".75" y=".75" width="{G - 1.5}" height="{Y - 1.5}" rx="16" fill="none" stroke="url(#kn)" stroke-width="1.5"/>',
        f'<circle class="nb" cx="38" cy="44" r="5" fill="{T["mavi"]}"/>',
        f'<text class="bs" x="54" y="51">{baslik}</text>',
        f'<text class="alt m" x="{G - 32}" y="50" text-anchor="end">{alt}</text>',
    ]


def svg_istatistik(veri):
    G, Y = 800, 262
    p = _ust(G, Y, f"{KULLANICI} GitHub istatistikleri", "Genel Bakış", "her gece güncellenir")
    kutular = [
        ("Açık repo", veri["repo"]),
        ("Toplam yıldız", veri["yildiz"]) if veri["yildiz"] else ("Kullandığım dil", veri["dil_sayisi"]),
        ("Yayın", veri["yayin"]),
        ("Son 1 yılda katkı", veri["katki"]),
        ("Son 1 yılda commit", veri["commit"]),
        ("Lisans", "MIT"),
    ]
    kw, kh, ara = 236, 78, 14
    for i, (ad, deger) in enumerate(kutular):
        x = 32 + (i % 3) * (kw + ara)
        y = 80 + (i // 3) * (kh + ara)
        deger = deger if isinstance(deger, str) else sayi(deger)
        renk = T["mavi"] if i % 2 == 0 else T["mor"]
        p.append(f'<g class="gir" style="animation-delay:{i * .08:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="{kw}" height="{kh}" rx="12" fill="{T["kutu"]}" stroke="{T["kutu_kenar"]}"/>'
                 f'<rect x="{x}" y="{y + 18}" width="3" height="{kh - 36}" rx="1.5" fill="{renk}"/>'
                 f'<text class="dg" x="{x + 20}" y="{y + 40}" fill="{renk}">{deger}</text>'
                 f'<text class="et" x="{x + 20}" y="{y + 62}">{ad}</text></g>')
    p.append("</g></svg>")
    return "\n".join(p)


def svg_diller(veri):
    liste = veri["diller"]
    G = 800
    Y = 118 + 34 * len(liste) + 10
    p = _ust(G, Y, "En çok kullandığım diller: " + ", ".join(f"{d} %{o * 100:.1f}" for d, o in liste),
             "En Çok Kullandığım Diller", "açık repolar · kod baytı")
    x0, w = 32, G - 64
    # Üstte tek parça oran şeridi
    p.append(f'<rect x="{x0}" y="78" width="{w}" height="10" rx="5" fill="{T["ray"]}"/>')
    p.append(f'<clipPath id="serit"><rect x="{x0}" y="78" width="{w}" height="10" rx="5"/></clipPath><g clip-path="url(#serit)">')
    x = x0
    for dil, oran in liste:
        genis = oran * w
        p.append(f'<rect class="bar" x="{x:.1f}" y="78" width="{genis + .6:.1f}" height="10" fill="{DIL_RENK.get(dil, "#5d6b8f")}"/>')
        x += genis
    p.append("</g>")
    # Satır satır
    iz_x, iz_w = 210, 470
    for i, (dil, oran) in enumerate(liste):
        y = 124 + i * 34
        genis = max(4.0, oran * iz_w)
        p.append(f'<g class="gir" style="animation-delay:{.15 + i * .07:.2f}s">'
                 f'<circle cx="{x0 + 7}" cy="{y - 5}" r="6" fill="{DIL_RENK.get(dil, "#5d6b8f")}"/>'
                 f'<text class="dl" x="{x0 + 24}" y="{y}">{dil}</text>'
                 f'<rect x="{iz_x}" y="{y - 10}" width="{iz_w}" height="10" rx="5" fill="{T["ray"]}"/>'
                 f'<rect class="bar" style="animation-delay:{.3 + i * .08:.2f}s" x="{iz_x}" y="{y - 10}" width="{genis:.1f}" height="10" rx="5" fill="url(#n)"/>'
                 f'<text class="yz m" x="{G - 32}" y="{y}" text-anchor="end">%{oran * 100:.1f}</text></g>')
    p.append("</g></svg>")
    return "\n".join(p)


def yaz(veri):
    os.makedirs(CIKTI, exist_ok=True)
    with open(os.path.join(CIKTI, "istatistik.svg"), "w", encoding="utf-8") as f:
        f.write(svg_istatistik(veri))
    if veri["diller"]:
        with open(os.path.join(CIKTI, "diller.svg"), "w", encoding="utf-8") as f:
            f.write(svg_diller(veri))


if __name__ == "__main__":
    repolar = [r for r in repolari_al() if not r.get("private")]
    if not repolar:
        print("Repo listesi alınamadı, kartlar değişmedi")
        raise SystemExit(0)
    katki, commit = katki_al()
    veri = {
        "repo": len(repolar),
        "yildiz": sum(r.get("stargazers_count", 0) for r in repolar),
        "yayin": yayin_sayisi(),
        "katki": katki,
        "commit": commit,
    }
    veri["diller"], veri["dil_sayisi"] = diller(repolar)
    print(veri)
    yaz(veri)
    print("İstatistik kartları yazıldı")
