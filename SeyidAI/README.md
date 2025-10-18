# SeyidAI — Streamlit demo for Gemini

Bu küçük demo uygulama Gemini (Google GenAI) modellerini kullanarak üç ana özellik sağlar:
- Sohbet Asistanı (multimodal destekli sohbet)
- PDF Analizi ve sorgulama
- Görsel Anlama (yüklenen görsellerin analiz edilmesi)

## Gereksinimler
- Python 3.10+ önerilir
- Aşağıdaki paketler (proje kökünde):

requirements.txt dosyasında listelenmiştir. Önerilen kurulum:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

## API Anahtarı (Güvenlik)
Uygulama `GEMINI_API_KEY` ortam değişkenini bekler. Anahtarı direkt koda koymayın.
Geliştirme için `.env` dosyası kullanabilirsiniz (git'e eklemeyin):

```
GEMINI_API_KEY=your_api_key_here
```

Ardından `python-dotenv` ile veya PowerShell üzerinden ortam değişkenini ayarlayabilirsiniz.

Örnek PowerShell (geçici):

```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
streamlit run .\app.py
```

## Çalıştırma
1. Ortamı hazırlayın ve bağımlılıkları kurun (bkz. Gereksinimler).
2. API anahtarınızı ayarlayın.
3. Uygulamayı başlatın:

```powershell
streamlit run .\app.py
```

Uygulama yerel olarak http://localhost:8501 adresinde açılacaktır.

## Notlar ve sorun giderme
- Eğer `google-genai` kütüphanesi bulunamazsa, uygulama başlangıcında kullanıcıya hata mesajı gösterir.
- SDK sürümlerine bağlı imza farkları olabileceğinden `types.Part(text=...)` şeklinde nesne oluşturma tercih edilmiştir.
- Çok büyük PDF'ler gönderilirken token/length sınırlarına dikkat edin; daha sağlam RAG için chunking ve embedding önerilir.

## İleri adımlar
- `requirements.txt` içindeki sürümleri kilitleyebiliriz.
- Streamlit Secrets veya bir `.env` + `python-dotenv` entegrasyonu yapabilirim.
- Basit testler/CI ekleyebilirim.

