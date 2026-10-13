"""Katkı grafiğini (yeşil kareler) kar yağan, hareketli bir SVG'ye çevirir.

Çıktı: dist/kar-acik.svg (açık tema) ve dist/kar-koyu.svg (koyu tema)
Kullanım: python kar_grafik.py [--deneme]   (--deneme: rastgele veriyle dener)
"""
import datetime as dt
import json
import os
import random
import re
import sys
import urllib.request

KULLANICI = "Enskygr234"
CIKTI = "dist"

HUCRE, BOSLUK = 11, 3
ADIM = HUCRE + BOSLUK
SOL, UST = 34, 34
GUNLER = ["", "Pzt", "", "Çar", "", "Cum", ""]
AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

TEMALAR = {
    "acik": {
        "zemin": "#f6fbff", "yazi": "#3b5b78", "soluk": "#8aa4bb",
        "seviye": ["#e3edf5", "#b9dcf2", "#7cc0ea", "#3d97d3", "#1d5f99"],
        "kar": "#ffffff", "kar_kenar": "#b8cfe0", "tane": "#8fb6d6",
    },
    "koyu": {
        "zemin": "#0d1520", "yazi": "#cfe3f5", "soluk": "#6f8aa3",
        "seviye": ["#16212e", "#1c4466", "#26679a", "#3a8fcf", "#8ecae6"],
        "kar": "#f4fbff", "kar_kenar": "#f4fbff", "tane": "#ffffff",
    },
}
SEVIYE_ADLARI = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


# ---------- Veri ----------
def graphql_ile():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    sorgu = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{date contributionLevel}}}}}}"""
    istek = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": sorgu, "variables": {"u": KULLANICI}}).encode(),
        headers={"Authorization": "Bearer " + token, "User-Agent": "kar-grafik", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=30) as c:
            takvim = json.load(c)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except Exception as hata:
        print("GraphQL olmadı:", hata)
        return None
    gunler = [(g["date"], SEVIYE_ADLARI.get(g["contributionLevel"], 0))
              for h in takvim["weeks"] for g in h["contributionDays"]]
    return gunler, takvim["totalContributions"]


def sayfadan():
    istek = urllib.request.Request(f"https://github.com/users/{KULLANICI}/contributions",
                                   headers={"User-Agent": "Mozilla/5.0 kar-grafik"})
    try:
        with urllib.request.urlopen(istek, timeout=30) as c:
            html = c.read().decode("utf-8", "replace")
    except Exception as hata:
        print("Sayfa okunamadı:", hata)
        return None
    gunler = []
    for etiket in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        tarih = re.search(r'data-date="([\d-]+)"', etiket)
        seviye = re.search(r'data-level="(\d)"', etiket)
        if tarih and seviye:
            gunler.append((tarih.group(1), int(seviye.group(1))))
    if not gunler:
        return None
    gunler.sort()
    toplam = re.search(r"([\d,.]+)\s+contributions?\s+in the last year", html)
    toplam = int(re.sub(r"\D", "", toplam.group(1))) if toplam else None
    return gunler, toplam


def deneme_verisi():
    rnd = random.Random(7)
    bugun = dt.date.today()
    bas = bugun - dt.timedelta(days=364 + (bugun.weekday() + 1) % 7)
    gunler = []
    for i in range((bugun - bas).days + 1):
        g = bas + dt.timedelta(days=i)
        gunler.append((g.isoformat(), rnd.choice([0, 0, 0, 1, 1, 2, 3, 4])))
    return gunler, 412


# ---------- Çizim ----------
def svg_uret(gunler, toplam, tema_adi, tohum):
    t = TEMALAR[tema_adi]
    rnd = random.Random(tohum)

    # Günleri haftalara (sütun) ve haftanın gününe (satır, Pazar=0) yerleştir
    ilk = dt.date.fromisoformat(gunler[0][0])
    ilk_pazar = ilk - dt.timedelta(days=(ilk.weekday() + 1) % 7)
    hucreler = []
    for tarih, seviye in gunler:
        g = dt.date.fromisoformat(tarih)
        sutun = (g - ilk_pazar).days // 7
        satir = (g.weekday() + 1) % 7
        hucreler.append((sutun, satir, seviye, g))
    sutun_sayisi = max(h[0] for h in hucreler) + 1

    gen = SOL + sutun_sayisi * ADIM + 16
    yuk = UST + 7 * ADIM + 40
    dongu = 24  # saniye: bir kar döngüsü

    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {gen} {yuk}" width="{gen}" height="{yuk}" '
             f'role="img" aria-label="{KULLANICI} katkı grafiği, karla">')
    p.append(f"""<style>
  .y{{font:11px -apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:{t['soluk']}}}
  .b{{font:600 13px -apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:{t['yazi']}}}
  .tane{{fill:{t['tane']};animation:dus linear infinite}}
  @keyframes dus{{from{{transform:translate(0,-20px)}}to{{transform:translate(var(--sx),{yuk + 20}px)}}}}
  .ortu{{fill:{t['kar']};stroke:{t['kar_kenar']};stroke-width:.5;opacity:0;animation:ort {dongu}s ease-out infinite}}
  @keyframes ort{{0%{{opacity:0}}6%{{opacity:1}}88%{{opacity:1}}96%,100%{{opacity:0}}}}
  .kirag{{fill:{t['kar']};opacity:0;animation:kir {dongu}s ease-out infinite}}
  @keyframes kir{{0%{{opacity:0}}8%{{opacity:.28}}88%{{opacity:.28}}96%,100%{{opacity:0}}}}
  .ortu,.tane{{will-change:transform,opacity}}
  @media (prefers-reduced-motion:reduce){{.tane{{display:none}}.ortu{{animation:none;opacity:1}}.kirag{{animation:none;opacity:.28}}}}
</style>""")
    p.append(f'<rect width="{gen}" height="{yuk}" rx="10" fill="{t["zemin"]}"/>')

    # Ay adları
    son_ay = None
    for sutun, satir, _, g in sorted(hucreler):
        if satir == 0 and g.month != son_ay and g.day <= 7:
            p.append(f'<text class="y" x="{SOL + sutun * ADIM}" y="{UST - 8}">{AYLAR[g.month - 1]}</text>')
            son_ay = g.month
    # Gün adları
    for satir, ad in enumerate(GUNLER):
        if ad:
            p.append(f'<text class="y" x="4" y="{UST + satir * ADIM + 9}">{ad}</text>')

    # Kareler ve üstlerine biriken kar
    ortular = []
    for sutun, satir, seviye, _ in hucreler:
        x, y = SOL + sutun * ADIM, UST + satir * ADIM
        p.append(f'<rect x="{x}" y="{y}" width="{HUCRE}" height="{HUCRE}" rx="2.5" fill="{t["seviye"][seviye]}"/>')
        # Kar soldan sağa, hafif rastgele sırayla birikir
        gecikme = sutun / sutun_sayisi * dongu * 0.55 + rnd.uniform(0, 2.5)
        if seviye == 0:
            # Boş kareler yavaşça kırağıyla kaplanır
            ortular.append(
                f'<rect class="kirag" style="animation-delay:{gecikme:.2f}s" x="{x}" y="{y}" '
                f'width="{HUCRE}" height="{HUCRE}" rx="2.5"/>')
        else:
            kalinlik = 2 + seviye  # çok katkı = kalın kar
            ortular.append(
                f'<rect class="ortu" style="animation-delay:{gecikme:.2f}s" x="{x - .5}" y="{y - 1}" '
                f'width="{HUCRE + 1}" height="{kalinlik}" rx="{kalinlik / 2:.1f}"/>')
    p.extend(ortular)

    # Yağan kar taneleri
    for _ in range(90):
        x = rnd.uniform(0, gen)
        r = rnd.choice([1, 1.2, 1.5, 1.8, 2.2])
        sure = rnd.uniform(6, 13) * (2.4 / (r + 0.6))
        gecikme = -rnd.uniform(0, sure)
        kayma = rnd.uniform(-40, 40)
        opak = rnd.uniform(.55, .95)
        p.append(f'<circle class="tane" cx="{x:.1f}" cy="0" r="{r}" opacity="{opak:.2f}" '
                 f'style="--sx:{kayma:.0f}px;animation-duration:{sure:.1f}s;animation-delay:{gecikme:.1f}s"/>')

    # Alt yazı
    alt = UST + 7 * ADIM + 24
    yazi = f"Son bir yılda {toplam} katkı ❄" if toplam is not None else "Son bir yılın katkıları ❄"
    p.append(f'<text class="b" x="{SOL}" y="{alt}">{yazi}</text>')
    # Seviye göstergesi
    lx = gen - 16 - 5 * ADIM - 30
    p.append(f'<text class="y" x="{lx - 42}" y="{alt}">Az</text>')
    for i, renk in enumerate(t["seviye"]):
        p.append(f'<rect x="{lx + i * ADIM - 14}" y="{alt - 10}" width="{HUCRE}" height="{HUCRE}" rx="2.5" fill="{renk}"/>')
    p.append(f'<text class="y" x="{lx + 5 * ADIM - 10}" y="{alt}">Çok</text>')
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    veri = deneme_verisi() if "--deneme" in sys.argv else (graphql_ile() or sayfadan())
    if not veri:
        print("Katkı verisi alınamadı, eski görsel korunuyor.")
        sys.exit(0)
    gunler, toplam = veri
    os.makedirs(CIKTI, exist_ok=True)
    tohum = dt.date.today().toordinal()
    for ad in TEMALAR:
        with open(f"{CIKTI}/kar-{ad}.svg", "w", encoding="utf-8") as f:
            f.write(svg_uret(gunler, toplam, ad, tohum))
    print(f"{len(gunler)} gün, toplam {toplam} katkı → {CIKTI}/kar-*.svg")
