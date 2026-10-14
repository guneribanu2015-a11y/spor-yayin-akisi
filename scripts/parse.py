"""guides/*.xml (XMLTV, platform başına bir dosya) -> docs/matches.json : canlı maçları ayıklar, spor dalı atar."""
import glob, json, os, re, sys, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

TR = timezone(timedelta(hours=3))
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

PLATFORM = {"digiturk.com.tr": "Digiturk", "tvplus.com.tr": "TV+", "dsmart.com.tr": "D-Smart"}
SIFRESIZ = ("trt spor", "trt 3", "a spor", "ht spor", "tabii")  # diğerleri şifreli

# Sınıflandırma kural tablosu: (anahtar kelime, spor, lig). İlk eşleşen kazanır.
KURALLAR = [
    ("sultanlar ligi", "Voleybol", "Sultanlar Ligi"), ("efeler ligi", "Voleybol", "Efeler Ligi"),
    ("cev ", "Voleybol", "CEV"), ("voleybol", "Voleybol", ""), ("vnl", "Voleybol", "VNL"),
    ("euroleague", "Basketbol", "EuroLeague"), ("euroleaque", "Basketbol", "EuroLeague"),
    ("eurocup", "Basketbol", "EuroCup"), ("nba", "Basketbol", "NBA"),
    ("basketbol süper ligi", "Basketbol", "BSL"), ("bsl", "Basketbol", "BSL"),
    ("basketbol", "Basketbol", ""), ("fiba", "Basketbol", "FIBA"), ("bcl", "Basketbol", "BCL"),
    ("hentbol", "Hentbol", ""), ("ehf", "Hentbol", "EHF"),
    ("tenis", "Tenis", ""), ("atp", "Tenis", "ATP"), ("wta", "Tenis", "WTA"),
    ("formula 1", "Motor Sporları", "Formula 1"), ("f1", "Motor Sporları", "Formula 1"),
    ("motogp", "Motor Sporları", "MotoGP"), ("nfl", "Amerikan Futbolu", "NFL"),
    ("nhl", "Buz Hokeyi", "NHL"), ("snooker", "Snooker", ""), ("bisiklet", "Bisiklet", ""),
    ("süper lig", "Futbol", "Süper Lig"), ("1. lig", "Futbol", "1. Lig"),
    ("şampiyonlar ligi", "Futbol", "Şampiyonlar Ligi"), ("champions league", "Futbol", "Şampiyonlar Ligi"),
    ("avrupa ligi", "Futbol", "Avrupa Ligi"), ("konferans ligi", "Futbol", "Konferans Ligi"),
    ("premier lig", "Futbol", "Premier Lig"), ("premier league", "Futbol", "Premier Lig"),
    ("laliga", "Futbol", "LaLiga"), ("la liga", "Futbol", "LaLiga"), ("serie a", "Futbol", "Serie A"),
    ("bundesliga", "Futbol", "Bundesliga"), ("ligue 1", "Futbol", "Ligue 1"),
    ("türkiye kupası", "Futbol", "Türkiye Kupası"), ("ziraat", "Futbol", "Türkiye Kupası"),
    ("roshn", "Futbol", "Suudi Pro Lig"), ("suudi", "Futbol", "Suudi Pro Lig"),
    ("uefa", "Futbol", "UEFA"), ("fifa", "Futbol", "FIFA"), ("futbol", "Futbol", ""),
]
# Kanal bazlı varsayılan (başlıkta lig yoksa)
KANAL_VARSAYILAN = [("eurosport", "Tenis/Diğer"), ("bein", "Futbol"), ("s sport", "Basketbol"),
                    ("ht spor", "Futbol"), ("tabii", "Futbol"), ("a spor", "Futbol")]

ELE = re.compile(r"tekrar|özet|ozet|ban ?arası|stüdyo|studyo|analiz|maç sonu|mac sonu|öncesi|"
                 r"onu konuşalım|magazin|haber|belgesel|\(t\)|röportaj|en iyi|golleri|hikaye", re.I)
MAC = re.compile(r"\S.{1,40}?\s[-–—]\s\S|\svs\.?\s|canlı|canli|live", re.I)


def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def zaman(s):
    return datetime.strptime(s[:14], "%Y%m%d%H%M%S").replace(
        tzinfo=datetime.strptime(s[15:], "%z").tzinfo if len(s) > 15 else timezone.utc).astimezone(TR)


def siniflandir(baslik, kanal):
    b = tr_lower(baslik) + " "
    for k, spor, lig in KURALLAR:
        if re.search(r"(?<![a-zçğıöşü])" + re.escape(k), b):
            return spor, lig
    for k, spor in KANAL_VARSAYILAN:
        if k in tr_lower(kanal):
            return spor, ""
    return "Diğer", ""


def karsilasma(baslik):
    t = re.sub(r"\(?\b(canlı|canli|live)\b\)?\s*[|:-]?", "", baslik, flags=re.I).strip(" |:-")
    return t.split(":", 1)[1].strip() if ":" in t and re.search(r"[-–]", t.split(":", 1)[1]) else t


def main(dosyalar, out):
    maclar = {}
    for guide in dosyalar:
        try:
            root = ET.parse(guide).getroot()
        except ET.ParseError:
            print("atlandı:", guide); continue
        plat = next((v for k, v in PLATFORM.items() if k in os.path.basename(guide)), "")
        tara(root, plat, maclar)
    yaz(maclar, out)


def tara(root, plat, maclar):
    kanallar = {c.get("id"): (c.findtext("display-name") or c.get("id")) for c in root.iter("channel")}
    for p in root.iter("programme"):
        baslik = (p.findtext("title") or "").strip()
        desc = (p.findtext("desc") or "")
        if not baslik or ELE.search(baslik) or not MAC.search(baslik) or re.search(r"tekrar|özet", desc[:80], re.I):
            continue
        kid = p.get("channel")
        kanal = kanallar.get(kid, kid)
        bas = zaman(p.get("start"))
        spor, lig = siniflandir(baslik + " " + desc[:120], kanal)
        anahtar = (bas.isoformat(), tr_lower(re.sub(r"\W", "", kanal)), tr_lower(re.sub(r"\W", "", baslik)))
        m = maclar.setdefault(anahtar, {
            "tarih": bas.strftime("%Y-%m-%d"), "gun": GUNLER[bas.weekday()], "saat": bas.strftime("%H:%M"),
            "spor": spor, "lig": lig, "karsilasma": karsilasma(baslik), "kanal": kanal, "platform": [],
            "sifresiz": any(s in tr_lower(kanal) for s in SIFRESIZ)})
        if plat and plat not in m["platform"]:
            m["platform"].append(plat)


def yaz(maclar, out):
    # Tekrar yayınları ele: aynı karşılaşmanın sadece ilk yayın(lar)ı kalır (1 saatten sonraki tekrarlar atılır)
    ilk, liste = {}, []
    for m in sorted(maclar.values(), key=lambda m: (m["tarih"], m["saat"])):
        k = tr_lower(re.sub(r"\W", "", m["karsilasma"]))
        t = datetime.fromisoformat(f'{m["tarih"]}T{m["saat"]}')
        if k in ilk and t - ilk[k] > timedelta(hours=1):
            continue
        ilk.setdefault(k, t)
        if t.replace(tzinfo=TR) >= datetime.now(TR) - timedelta(hours=3):
            liste.append(m)
    liste.sort(key=lambda m: (m["tarih"], m["saat"], m["spor"]))
    json.dump({"guncelleme": datetime.now(TR).strftime("%Y-%m-%d %H:%M"), "maclar": liste},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(liste)} maç yazıldı -> {out}")


if __name__ == "__main__":
    main(sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "guides/*.xml")),
         sys.argv[2] if len(sys.argv) > 2 else "docs/matches.json")
