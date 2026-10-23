"""Profil README'sindeki otomatik bölümleri günceller.

- KIS: Nardugan'a (kış gündönümü) kaç gün kaldığı
- YAYIN: repolardaki en son yayınlar (releases)
"""
import datetime as dt
import json
import os
import re
import urllib.request

KULLANICI = "Enskygr234"
README = "README.md"
TR = dt.timezone(dt.timedelta(hours=3))
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def api(yol):
    istek = urllib.request.Request("https://api.github.com/" + yol, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profil-guncelleyici",
        **({"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]} if os.environ.get("GITHUB_TOKEN") else {}),
    })
    try:
        with urllib.request.urlopen(istek, timeout=20) as cevap:
            return json.load(cevap)
    except Exception:
        return None


def tarih_yaz(gun):
    return f"{gun.day} {AYLAR[gun.month - 1]} {gun.year}"


def kis_bolumu(bugun):
    gundonumu = dt.date(bugun.year, 12, 21)
    if bugun > gundonumu:
        gundonumu = dt.date(bugun.year + 1, 12, 21)
    kalan = (gundonumu - bugun).days
    if kalan == 0:
        satir = "🌅 **Bugün Nardugan!** Yılın en uzun gecesi bitti, gün yeniden doğuyor."
    else:
        dolu = max(0, min(20, round(20 * (1 - kalan / 365))))
        cubuk = "❄" * dolu + "·" * (20 - dolu)
        satir = f"🌅 Nardugan'a (kış gündönümü) **{kalan} gün** kaldı &nbsp; `{cubuk}`"
    return f"<div align=\"center\">\n\n{satir}\n\n<sub>Her gün kendiliğinden güncellenir · son: {tarih_yaz(bugun)}</sub>\n\n</div>"


def yayin_bolumu():
    # Kod repoları gizli; indirme dosyaları herkese açık winter-browser-releases reposunda duruyor.
    yayinlar = []
    for y in (api(f"repos/{KULLANICI}/winter-browser-releases/releases?per_page=30") or []):
        if y.get("published_at") and not y.get("draft"):
            yayinlar.append((y["published_at"], y.get("name") or y["tag_name"], y["html_url"]))
    if not yayinlar:
        return None
    yayinlar.sort(reverse=True)
    satirlar = ["| Yayın | Tarih |", "|---|---|"]
    for zaman, ad, link in yayinlar[:5]:
        gun = dt.datetime.fromisoformat(zaman.replace("Z", "+00:00")).astimezone(TR).date()
        satirlar.append(f"| [**{ad}**]({link}) | {tarih_yaz(gun)} |")
    satirlar.append("")
    satirlar.append("<sub>Hepsi ve daha fazlası: [enskygr234.github.io](https://enskygr234.github.io/)</sub>")
    return "\n".join(satirlar)


def yerlestir(metin, etiket, icerik):
    if icerik is None:
        return metin
    desen = re.compile(rf"(<!-- {etiket}:BASLA -->)(.*?)(<!-- {etiket}:BITIS -->)", re.S)
    return desen.sub(lambda m: f"{m.group(1)}\n{icerik}\n{m.group(3)}", metin)


if __name__ == "__main__":
    bugun = dt.datetime.now(TR).date()
    with open(README, encoding="utf-8") as f:
        eski = f.read()
    yeni = yerlestir(eski, "KIS", kis_bolumu(bugun))
    yeni = yerlestir(yeni, "YAYIN", yayin_bolumu())
    if yeni != eski:
        with open(README, "w", encoding="utf-8") as f:
            f.write(yeni)
        print("README güncellendi")
    else:
        print("Değişiklik yok")
