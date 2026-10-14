"""Sporekrani.com verisinden 7 günlük canlı maç listesi üretir -> docs/matches.json (kişisel kullanım)."""
import json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

TR = timezone(timedelta(hours=3))
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
API = "https://api.sporekrani.com/v4.1/events"
ANAHTAR = {"app_id": "vunsbpYk", "api_key": "LltEnsF0MViM001z71NBVrZ4J8KmLqU5Ho5Mkew1"}
GUN_SAYISI = 7

# Türkiye'den izlenmeyen kanal/platformlar listeden çıkarılır
YABANCI_KANAL = ("idman", "cbc sport", "ictimai", "yayın yok")
YABANCI_PLATFORM = ("Azerspace",)
ACIK_KANAL = ("trt", "a spor", "ht spor", "tv8", "tv 8", "atv", "fb tv", "gs tv", "bjk tv", "ts tv", "tivibu spor", "euroleague tv", "tbf", "tvf", "thf", "fiba")
SPOR_ADI = {"Motosiklet": "Motor Sporları", "Otomobil Yarışı": "Motor Sporları", "Formula 1": "Motor Sporları"}


def gun_verisi(gun):
    q = urllib.parse.urlencode({"day": gun, **ANAHTAR})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    for deneme in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r).get("data") or []
        except Exception as e:
            print(f"{gun} deneme {deneme + 1}: {e}")
            time.sleep(5)
    return []


def donustur(e):
    if e.get("event_type_name") != "match" or e.get("sport_name") == "Programlar":
        return None
    kanallar, platformlar, sifresiz = [], [], False
    for c in e.get("channels") or []:
        ad = (c.get("name") or "").strip()
        if not ad or any(y in ad.lower() for y in YABANCI_KANAL):
            continue
        ad = ad.replace("Bein Sports beIN Connect", "beIN Connect").replace("Bein Sports", "beIN Sports")
        if ad not in kanallar:
            kanallar.append(ad)
        for p in c.get("providers") or []:
            pad = p.get("name") or ""
            if pad in YABANCI_PLATFORM:
                continue
            if pad == "Şifresiz":
                sifresiz = True
            if pad and pad != "Şifresiz" and pad not in platformlar:
                platformlar.append("İnternet" if pad == "Web" else pad)
    if not kanallar:
        return None
    if any(k.lower().startswith(ACIK_KANAL) for k in kanallar):
        sifresiz = True
    t = datetime.strptime(e["date_time"], "%Y-%m-%d %H:%M:%S")
    spor = SPOR_ADI.get(e.get("sport_name"), e.get("sport_name") or "Diğer")
    return {"tarih": t.strftime("%Y-%m-%d"), "gun": GUNLER[t.weekday()], "saat": t.strftime("%H:%M"),
            "spor": spor, "lig": e.get("league_name") or "", "karsilasma": e.get("name") or "",
            "kanal": ", ".join(kanallar), "platform": sorted(set(platformlar)), "sifresiz": sifresiz}


def main(out):
    bugun = datetime.now(TR).date()
    simdi = datetime.now(TR).replace(tzinfo=None) - timedelta(hours=2)
    maclar, gorulen = [], set()
    for i in range(GUN_SAYISI):
        gun = (bugun + timedelta(days=i)).isoformat()
        veri = gun_verisi(gun)
        print(f"{gun}: {len(veri)} etkinlik")
        for e in veri:
            m = donustur(e)
            if not m or e["id"] in gorulen:
                continue
            if datetime.fromisoformat(f'{m["tarih"]}T{m["saat"]}') < simdi:
                continue
            gorulen.add(e["id"])
            maclar.append(m)
    if not maclar:
        sys.exit("Hiç veri gelmedi; eski liste korunuyor.")
    maclar.sort(key=lambda m: (m["tarih"], m["saat"], m["spor"]))
    json.dump({"guncelleme": datetime.now(TR).strftime("%Y-%m-%d %H:%M"), "kaynak": "sporekrani.com", "maclar": maclar},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(maclar)} maç yazıldı -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/matches.json")
