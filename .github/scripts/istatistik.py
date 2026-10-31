"""Profil için kış temalı istatistik kartı çizer (dış servis gerektirmez).

Çıktı: dist/istatistik-koyu.svg ve dist/istatistik-acik.svg
- Sol: açık repo, toplam yıldız, son bir yıldaki katkı, commit ve yayın sayısı
- Sağ: en çok kullanılan diller (açık repolardaki kod baytına göre)

Kullanım: python istatistik.py
  REPOLAR="a,b,c" ortam değişkeni verilirse kullanıcı listesi yerine bu repolar okunur.
Veri alınamazsa eski kartlar olduğu gibi bırakılır.
"""
import json
import os
import random
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

TEMALAR = {
    "koyu": {"zemin1": "#0a1830", "zemin2": "#050b15", "cizgi": "#1d3550", "yazi": "#e8f4ff",
             "soluk": "#7f9bb5", "vurgu": "#5fd4ff", "turuncu": "#f2a33a", "tane": "#ffffff", "ray": "#16263a"},
    "acik": {"zemin1": "#f6fbff", "zemin2": "#e6f1fa", "cizgi": "#cfe0ee", "yazi": "#1f3b57",
             "soluk": "#6a87a1", "vurgu": "#1d7fc4", "turuncu": "#d9821a", "tane": "#9cc4e4", "ray": "#dce9f4"},
}


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


def svg(veri, tema):
    t = TEMALAR[tema]
    G, Y = 900, 210
    rnd = random.Random(11)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {G} {Y}" width="{G}" height="{Y}" role="img" '
         f'aria-label="{KULLANICI} GitHub istatistikleri">']
    p.append(f"""<defs>
<linearGradient id="z" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['zemin1']}"/><stop offset="1" stop-color="{t['zemin2']}"/></linearGradient>
<clipPath id="k"><rect width="{G}" height="{Y}" rx="14"/></clipPath>
</defs>
<style>
text{{font-family:-apple-system,'Segoe UI',system-ui,Helvetica,Arial,sans-serif}}
.bs{{font-size:15px;font-weight:700;fill:{t['yazi']}}}
.et{{font-size:12.5px;fill:{t['soluk']}}}
.dg{{font-size:24px;font-weight:800;fill:{t['yazi']}}}
.dl{{font-size:12.5px;fill:{t['yazi']}}}
.yz{{font-size:12.5px;fill:{t['soluk']};font-variant-numeric:tabular-nums}}
.tn{{fill:{t['tane']};animation:d linear infinite}}
@keyframes d{{from{{transform:translateY(-12px)}}to{{transform:translateY({Y + 12}px)}}}}
.gir{{opacity:0;animation:g .7s ease-out forwards}}
@keyframes g{{to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.tn{{display:none}}.gir{{animation:none;opacity:1}}}}
</style>""")
    p.append(f'<g clip-path="url(#k)"><rect width="{G}" height="{Y}" fill="url(#z)"/>')
    # Kar taneleri
    for _ in range(26):
        x, r_ = rnd.uniform(0, G), rnd.choice([1, 1.2, 1.6, 2])
        p.append(f'<circle class="tn" cx="{x:.0f}" cy="0" r="{r_}" opacity="{rnd.uniform(.25, .7):.2f}" '
                 f'style="animation-duration:{rnd.uniform(9, 18):.1f}s;animation-delay:-{rnd.uniform(0, 18):.1f}s"/>')
    p.append(f'<rect x=".5" y=".5" width="{G - 1}" height="{Y - 1}" rx="14" fill="none" stroke="{t["cizgi"]}"/>')
    p.append(f'<line x1="446" y1="28" x2="446" y2="{Y - 28}" stroke="{t["cizgi"]}"/>')

    # Sol: rakamlar
    p.append(f'<text class="bs" x="32" y="44">❄ Rakamlarla</text>')
    kutular = [
        ("Açık repo", veri["repo"], t["vurgu"]),
        (("Toplam yıldız", veri["yildiz"]) if veri["yildiz"] else ("Kullandığım dil", veri["dil_sayisi"])) + (t["turuncu"],),
        ("Yayın", veri["yayin"], t["vurgu"]),
        ("Son 1 yılda katkı", veri["katki"], t["turuncu"]),
        ("Son 1 yılda commit", veri["commit"], t["vurgu"]),
        ("Lisans", "MIT", t["turuncu"]),
    ]
    for i, (ad, deger, renk) in enumerate(kutular):
        x = 32 + (i % 3) * 134
        y = 92 + (i // 3) * 72
        deger = deger if isinstance(deger, str) else sayi(deger)
        p.append(f'<g class="gir" style="animation-delay:{i * .08:.2f}s">'
                 f'<rect x="{x}" y="{y - 30}" width="3" height="40" rx="1.5" fill="{renk}"/>'
                 f'<text class="dg" x="{x + 12}" y="{y - 4}">{deger}</text>'
                 f'<text class="et" x="{x + 12}" y="{y + 13}">{ad}</text></g>')

    # Sağ: diller
    p.append(f'<text class="bs" x="474" y="44">🛠️ En çok yazdığım diller</text>')
    x0, w = 474, 394
    if veri["diller"]:
        x = x0
        p.append(f'<rect x="{x0}" y="62" width="{w}" height="10" rx="5" fill="{t["ray"]}"/>')
        p.append(f'<clipPath id="bar"><rect x="{x0}" y="62" width="{w}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">')
        for dil, oran in veri["diller"]:
            genis = oran * w
            p.append(f'<rect x="{x:.1f}" y="62" width="{genis + .5:.1f}" height="10" fill="{DIL_RENK.get(dil, "#8aa4bb")}"/>')
            x += genis
        p.append('</g>')
        for i, (dil, oran) in enumerate(veri["diller"]):
            cx = x0 + (i % 2) * 204
            cy = 104 + (i // 2) * 28
            p.append(f'<g class="gir" style="animation-delay:{.3 + i * .07:.2f}s">'
                     f'<circle cx="{cx + 6}" cy="{cy - 4}" r="5.5" fill="{DIL_RENK.get(dil, "#8aa4bb")}"/>'
                     f'<text class="dl" x="{cx + 20}" y="{cy}">{dil}</text>'
                     f'<text class="yz" x="{cx + 190}" y="{cy}" text-anchor="end">%{oran * 100:.1f}</text></g>')
    p.append('</g></svg>')
    return "\n".join(p)


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
    os.makedirs(CIKTI, exist_ok=True)
    for tema in TEMALAR:
        with open(os.path.join(CIKTI, f"istatistik-{tema}.svg"), "w", encoding="utf-8") as f:
            f.write(svg(veri, tema))
    print("İstatistik kartları yazıldı")
