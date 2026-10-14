# Spor Yayın Akışı (kişisel)

Digiturk, TV+ ve D-Smart'taki 35 spor kanalının akışını günde 2 kez (06:00 / 18:00) çeker, canlı maçları ayıklar, spor dalına göre sınıflar ve telefonda açılan tek sayfada gösterir.

## Kurulum (~10 dk)
1. GitHub'da yeni repo aç: `spor-yayin-akisi` (Private olabilir; Pages için Public daha kolay).
2. Bu klasördeki tüm dosyaları repoya yükle (Add file → Upload files; `.github` klasörü dahil).
3. Settings → Pages → Source: *Deploy from a branch*, Branch: `main`, klasör: `/docs` → Save.
4. Actions sekmesi → "Yayın akışını güncelle" → **Run workflow** (ilk veriyi hemen çeker, ~10–15 dk).
5. Sayfa: `https://KULLANICIADIN.github.io/spor-yayin-akisi/` → telefonda ana ekrana ekle.

## Ayar
- Kanal ekle/çıkar: `sport.channels.xml`
- Lig → spor kuralları ve elenen kelimeler (tekrar, özet…): `scripts/parse.py` → `KURALLAR`, `ELE`
- Şifresiz kanallar: `parse.py` → `SIFRESIZ`
