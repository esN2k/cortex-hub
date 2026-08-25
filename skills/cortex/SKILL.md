---
name: cortex
description: CortexAI abonelik araçları — görsel, video, ses, müzik, web arama, kota. Kullanıcı görsel/video/müzik/TTS istediğinde veya güncel web bilgisi gerektiğinde kullan.
---

# Cortex araçları

Beyin: `grok/grok-4.6-max` (ana). Yedek: `app-cortex/claude-sonnet-4-6-thinking`. Medya ve arama **araç** (MCP `cortex_*`).

- Görsel iste → `cortex_image` (core `seedream-5`; studio `gpt-image-2` alternatif)
- Video → `cortex_video` (`minimax-h3`, 4–15 sn; dakikalar sürebilir)
- Konuşma → `cortex_speech` (Türkçe varsayılan)
- Müzik → `cortex_music`
- Güncel bilgi → `cortex_web_search` (api-v2, 5000/gün)
- Kota → `cortex_quota` (üretimden önce bak)
- Dosya referansı → `cortex_upload` sonra URL’yi image/video’ya ver

Çıktı: `C:\Users\Esen\.config\opencode\cortex-out\`

Başka modele geçmek için OpenCode model seçici (`grok`, `llmv2-cortex`, `apiv2-cortex`) veya tek seferlik `cortex_chat`.
