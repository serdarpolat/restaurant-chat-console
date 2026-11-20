
## 2026-11-21 — Composer redesign + odak düzeltmesi

Serdar'dan gelen geri bildirim:
1. Ekran görüntüsü: "Salon 2'nin siparişi nedir?" sorusuna `get_order` tool'u kırmızı
   "Error executing tool get_order: Salon 2 has no open order (free)." hatası verdi, ama
   asistan yine de doğru cevabı üretti ("Salon 2 masasında şu anda açık bir sipariş yok").
   **Bu bir bug değil** — masa gerçekten boş olduğu için `get_order` beklenen şekilde hata
   döndürüyor, UI bunu kırmızı ✕ ile doğru gösteriyor, model de hatayı doğru yorumlayıp
   kullanıcıya anlamlı bir cevap veriyor. Tasarım gereği çalışıyor.
2. Nano Banana Pro ekran görüntüsü referans alınarak composer yeniden tasarlandı: koyu/açık
   temaya uyumlu, yuvarlak köşeli büyüyen textarea + alt satırda ipucu metni + sağda mor
   yuvarlak gönder butonu.
3. Chat geçmişi yoksa composer, karşılama metni ve öneri butonlarıyla birlikte ekranın
   ortasında; geçmiş oluşunca AYNI composer alta sabitleniyor (tek `ChatComposer.vue`
   bileşeni, iki farklı yerde kullanılıyor — kopya kod yok).
4. Bir soru gönderildiğinde (yazarak ya da öneri butonuna tıklayarak) cevap tamamlanınca
   cursor otomatik olarak composer'a geri dönüyor (`focusComposer()` → `onDone`'da
   çağrılıyor; sending sırasında textarea disabled olduğu için focus'u önce değil, enable
   olduktan sonra veriyoruz).

Değişen dosyalar: `frontend/app/app.vue`, `frontend/app/components/ChatComposer.vue` (yeni).
Backend'de değişiklik yok.

Doğrulama: backend 19/19 test + ruff temiz; frontend `npm run build` temiz; gerçek MCP
server + fake LM Studio + backend + headless Chrome ile açık/koyu mod boş durum ve
öneri-butonu-tıklama → docked composer + otomatik odak akışı uçtan uca test edildi
(screenshot: v3_light_empty, v3_dark_empty, v3_dark_chat_docked). Dosyalar cihaza
push edilip sha256sum ile doğrulandı.

>>> SIRADAKİ: Serdar görsel onay versin, "bugün boşsa genişlet" prompt fix'ini gerçek
LM Studio ile test etsin (önceki rounddan hâlâ bekliyor), sonra commit+push+CI. Ardından
M2: onay akışı.

## 2026-11-21 (devam) — Tablo + grafik desteği (M3'ten öne çekildi)

Serdar'dan gelen istek: tablo yapılabilecek cevaplarda gerçek HTML tablo, grafik
yapılabilecek cevaplarda cevabın altında otomatik grafik.

**Tablo/markdown render (frontend):**
- `useMarkdown.ts` eklendi — markdown-it ile assistant cevabı HTML'e çevriliyor
  (tablo, **kalın**, liste, kod), DOMPurify ile sanitize ediliyor. Sadece asistan
  cevabında kullanılıyor, kullanıcı mesajında değil.
- `ChatMessage.vue`: `{{ message.content }}` yerine `v-html="renderMarkdown(...)"`,
  tablo/kod/link için scoped CSS (açık/koyu tema uyumlu, geniş tablolar için
  yatay scroll sarmalayıcı).

**Grafik (backend + frontend, PROJECT6_SCOPE.md bölüm 5'teki M3 planı öne çekildi):**
- `charts.py` dolduruldu: `get_top_items` (yatay bar, adet/gelir), `get_sales_report`
  (çizgi, sadece group_by=day/hour), `get_staff_performance` (bar), `get_void_report`
  (sebebe göre toplanmış bar), `get_daily_summary` (büyük sayı + kanal kırılımı bar).
  Model DEĞİL, gerçek tool sonucundan deterministik üretiliyor — 12 yeni birim test.
- `chat.py`: başarılı + grafiklenebilir bir tool_result'tan sonra yeni `chart` SSE
  event'i (`{tool, spec}`) yollanıyor.
- Frontend: `useChatApi.ts`'e `onChart` handler, `ChartBlock.vue` (vue-chartjs +
  chart.js) eklendi, `app.vue`/`ChatMessage.vue` cevabın altında render ediyor.
- **Önemli bug + fix**: vue-chartjs, parent'ta HERHANGİ bir reactive değişiklikte
  (token stream, composer focus vb.) `chart.update()`'i animasyonlu çağırıyor;
  grafik statik olduğu için bu sürekli yeniden başlayan animasyon bazı anlarda
  grafiği görünmez/yarım bırakıyordu. `animation: false` ile çözüldü. Ayrıca
  Chart.js'in reactive Vue proxy'leri üzerinde kendi iç state'ini tutmasını
  önlemek için veri `structuredClone(toRaw(...))` ile düz objeye çevriliyor.

Değişen/yeni dosyalar: `backend/src/chat_console/{chat.py,charts.py}`,
`backend/tests/test_charts.py` (yeni), `frontend/package.json` (+chart.js,
vue-chartjs, markdown-it, dompurify), `frontend/app/composables/{useChatApi.ts,
useMarkdown.ts (yeni)}`, `frontend/app/components/{ChatMessage.vue,ChartBlock.vue
(yeni)}`, `frontend/app/app.vue`.

Doğrulama: backend 31/31 test (12 yeni chart testi) + ruff temiz; `npm run build`
temiz; gerçek MCP server + 3 farklı sahte LM Studio senaryosu (satış raporu tablo+
çizgi, en çok satanlar tablo+yatay bar, günlük özet büyük sayı+bar) + headless
Chrome ile açık/koyu modda uçtan uca doğrulandı. Dosyalar (package-lock.json dahil)
cihaza push edilip sha256sum ile doğrulandı.

Not: İlk ekran görüntüsündeki kırmızı "Error executing tool get_order" — bug değil,
masa gerçekten boş olduğu için beklenen hata; model doğru yorumlayıp doğru cevap
verdi (ayrıca sohbette açıklandı).

>>> SIRADAKİ: Serdar `npm install` çalıştırıp (yeni bağımlılıklar var) görsel onay
versin + "bugün boşsa genişlet" prompt fix'ini gerçek LM Studio ile test etsin
(hâlâ bekliyor), sonra commit+push+CI. Ardından M2: onay akışı (M3 artık bu round'da
büyük ölçüde tamamlandı).

## 2026-11-21 (devam 2) — Tablo da grafik gibi deterministik hale getirildi

Serdar'ın bulgusu: aynı "son 7 günün satış raporu" sorusuna bir seferinde model markdown
tablo yazdı (render düzgün çalıştı), bir seferinde düz liste yazdı ("Günlük detaylar:" +
satır satır) — bu durumda tablo görünmedi çünkü markdown-it'in render edeceği bir tablo
syntax'ı yoktu. Bu bug değildi (render doğru çalışıyordu) ama model aynı veriyi iki farklı
şekilde formatlayabildiği için tutarsızdı.

**Çözüm**: tablo da grafik gibi backend'de deterministik hale getirildi (bölüm 5'teki
"model grafik çiz demese bile çiziyoruz" mantığının tabloya uygulanması):
- `tables.py` (yeni): `table_for(tool_name, result)` — `get_top_items`,
  `get_sales_report` (HER group_by için, chart'tan farklı olarak day/hour kısıtı yok),
  `get_staff_performance`, `get_void_report` başarıyla döndüğünde `{columns, rows}`
  üretiyor. 9 yeni birim test.
- `chat.py`: chart emisyonunun yanına `table` SSE event'i (`{tool, table}`) eklendi.
- Frontend: `useChatApi.ts`'e `onTable`, `ChatMessage.vue`'de tablo HTML'i doğrudan
  render ediliyor (markdown tablosuyla aynı CSS'i paylaşıyor), `app.vue` topluyor.

Doğrulandı: modelin markdown tablo YAZMADIĞI (düz liste yazdığı) senaryoda bile tablo artık
kendiliğinden görünüyor — Serdar'ın gönderdiği ekran görüntüsünün birebir aynısı sahte LM
Studio stub'ıyla tekrar edildi, backend 41/41 test + ruff temiz, frontend build temiz,
dosyalar cihaza push edilip sha256sum ile doğrulandı.

>>> SIRADAKİ: Serdar görsel onay versin + "bugün boşsa genişlet" prompt fix'ini gerçek
LM Studio ile test etsin (hâlâ bekliyor), sonra commit+push+CI. Ardından M2: onay akışı.
