import streamlit as st
import os
import io
import base64
from PIL import Image
from pypdf import PdfReader

# Google GenAI SDK'dan gerekli modülleri içe aktarıyoruz
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
except ImportError:
    st.error("Gerekli 'google-genai' kütüphanesi yüklenemedi. Lütfen 'pip install google-genai' komutunu çalıştırın.")
    st.stop()

# --- Yapılandırma ve Anahtar Yönetimi ---

# API Anahtarını ortam değişkeninden okuma
# KRİTİK DÜZELTME: API Anahtarını doğrudan koda yazmak yerine ortam değişkeninden alıyoruz.
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    # Anahtar bulunamazsa kullanıcıya uyarı verme ve uygulamayı durdurma
    st.error(
        "Gemini API Anahtarı bulunamadı. Lütfen anahtarınızı 'GEMINI_API_KEY' "
        "adlı ortam değişkenine ayarlayın ve uygulamayı yeniden başlatın."
    )
    st.stop()

# API Anahtarı mevcutsa istemciyi başlatma
try:
    # client'ı her zaman st.cache_resource ile önbelleğe alıyoruz.
    @st.cache_resource
    def get_gemini_client():
        return genai.Client(api_key=api_key)
    
    client = get_gemini_client()
    st.sidebar.success("API Anahtarı başarıyla yüklendi.")
except Exception as e:
    st.error(f"Gemini İstemcisi başlatılırken bir hata oluştu: {e}")
    st.stop()

# --- Yardımcı Fonksiyonlar ---

def get_pdf_text_chunks(pdf_file):
    """PDF dosyasından metni okur ve metin parçalarını döndürür."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    
    # Basit bir RAG öncesi parçalama: Tüm metni tek bir dize olarak döndürürüz.
    # Gerçek RAG uygulamaları için daha gelişmiş chunking ve embedding gerekir.
    return text

# convert_to_base64_url fonksiyonu kullanılmadığı için kaldırılmıştır.

# Önceki get_chat_session kaldırıldı. Sohbet geçmişi manuel yönetilecek.

# --- Uygulama Başlığı ve Sekmeler ---

st.title("🤖 SeyidAI")
# st.caption satırı isteğiniz üzerine kaldırıldı.

tab_chat, tab_pdf, tab_img_analysis = st.tabs([
    "💬 Sohbet Asistanı", 
    "📄 PDF Analizi", 
    "🖼️ Görsel Anlama"
])

# --- 1. Sohbet Asistanı Sekmesi ---
with tab_chat:
    st.subheader("Sohbet Asistanı (Geçmişi Hatırlar)")

    # Sohbet geçmişini Streamlit session state'de saklama
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Sohbet geçmişini görüntüleme
    for message in st.session_state.chat_history:
        role = "Asistan" if message["role"] == "model" else "Siz"
        st.chat_message(message["role"]).markdown(f"**{role}:** {message['text']}")

    # Kullanıcı girişi
    if prompt := st.chat_input("Buraya yazın..."):
        
        # Kullanıcı mesajını geçmişe ekleme ve gösterme
        st.session_state.chat_history.append({"role": "user", "text": prompt})
        st.chat_message("user").markdown(f"**Siz:** {prompt}")

        # Modelden yanıt alma (streaming)
        with st.chat_message("model"):
            full_response = ""
            message_placeholder = st.empty()
            
            try:
                # DÜZELTME: Sohbet geçmişini Gemini formatına çevirip yeni bir oturum başlatıyoruz.
                # Bu, "client has been closed" hatasını önler.
                gemini_contents = []
                for msg in st.session_state.chat_history:
                    # Modelden gelen son mesajı (şu anda yanıtlanacak olan) hariç tutuyoruz.
                    if msg == st.session_state.chat_history[-1] and msg["role"] == "user":
                        # Yeni prompt'u eklemeden hemen önceki tüm geçmişi ekliyoruz.
                        break
                    
                    gemini_contents.append(types.Content(
                        role=msg["role"], 
                        parts=[types.Part(text=msg["text"]) ]
                    ))

                # Son kullanıcı mesajını (prompt) ekliyoruz
                gemini_contents.append(types.Content(
                    role="user", 
                    parts=[types.Part(text=prompt)]
                ))


                # generate_content_stream kullanılarak akışlı yanıt alınıyor
                response_stream = client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=gemini_contents
                )
                
                for chunk in response_stream:
                    full_response += chunk.text
                    message_placeholder.markdown(f"**Asistan:** {full_response}▌")
                
                message_placeholder.markdown(f"**Asistan:** {full_response}")
                
                # Tam yanıtı geçmişe ekleme
                st.session_state.chat_history.append({"role": "model", "text": full_response})

            except APIError as e:
                 st.error(f"API Hatası oluştu: {e}")
            except Exception as e:
                # Tekrar çalışmasını sağlamak için hata mesajını biraz daha bilgilendirici yapalım
                st.error(f"Beklenmedik bir hata oluştu: {type(e).__name__}: {e}")

# --- 2. PDF Analizi Sekmesi ---
with tab_pdf:
    st.subheader("PDF Analizi ve Sorgulama")
    st.write("PDF dosyanızı yükleyin ve içeriği hakkında sorular sorun. **Not:** Bu demo, PDF'nin tamamını tek bir büyük metin olarak modele gönderir, bu nedenle çok uzun PDF'ler için sınırları zorlayabilir.")

    uploaded_pdf = st.file_uploader("Bir PDF dosyası yükleyin", type=["pdf"])
    
    if uploaded_pdf:
        # PDF'den metin çıkarma
        pdf_text = get_pdf_text_chunks(uploaded_pdf)
        
        st.success(f"PDF yüklendi ve {len(pdf_text.split())} kelime çıkarıldı. Şimdi soru sorabilirsiniz.")
        
        pdf_prompt = st.text_area("PDF içeriği hakkında sorunuz:", value="Bu dokümanın ana fikri nedir ve hangi konuları ele alıyor?")

        if st.button("Analiz Et"):
            if not pdf_text:
                st.warning("PDF'den metin çıkarılamadı.")
            elif not pdf_prompt:
                st.warning("Lütfen bir soru girin.")
            else:
                with st.spinner("PDF analizi yapılıyor..."):
                    try:
                        # Hazırlanan metin ve kullanıcı sorusu ile model çağrısı
                        system_prompt = (
                            "Sen bir belge analiz uzmanısın. Yalnızca sağlanan PDF içeriğine dayanarak "
                            "kullanıcının sorusunu kapsamlı bir şekilde yanıtla."
                        )
                        
                        full_prompt = (
                            f"{system_prompt}\n\n"
                            f"--- PDF İÇERİĞİ BAŞLANGIÇ ---\n{pdf_text[:10000]}...\n--- PDF İÇERİĞİ SONU ---\n\n"
                            f"Kullanıcının Sorusu: {pdf_prompt}"
                        )
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-pro", # Pro daha iyi akıl yürütme için
                            contents=[full_prompt]
                        )
                        st.info(f"**Soru:** {pdf_prompt}")
                        st.markdown("---")
                        st.markdown(response.text)

                    except APIError as e:
                        st.error(f"API Hatası oluştu: {e}")
                    except Exception as e:
                        st.error(f"Beklenmedik bir hata oluştu: {e}")

# --- 3. Görsel Anlama Sekmesi ---
with tab_img_analysis:
    st.subheader("Görsel Anlama (Multimodal)")
    st.write("Bir resim yükleyin ve ona ne hakkında olduğunu sorun.")

    uploaded_image = st.file_uploader("Bir görsel dosyası yükleyin", type=["jpg", "jpeg", "png"])
    image_prompt = st.text_area("Görsel hakkında sorunuz:", value="Bu resimde neler oluyor? Detaylı bir açıklama yap.")
    
    if uploaded_image and image_prompt:
        st.image(uploaded_image, caption="Yüklenen Görsel", use_column_width=True)

        if st.button("Görseli Analiz Et"):
            with st.spinner("Görsel analiz ediliyor..."):
                try:
                    # Görüntüyü PIL Image nesnesine dönüştürme
                    image = Image.open(uploaded_image)
                    
                    # API'ye gönderilecek içerik listesi: Resim ve Metin
                    contents = [image, image_prompt]

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents
                    )
                    st.info(f"**Soru:** {image_prompt}")
                    st.markdown("---")
                    st.markdown(response.text)

                except APIError as e:
                    st.error(f"API Hatası oluştu: {e}")
                except Exception as e:
                    st.error(f"Beklenmedik bir hata oluştu: {e}")


# --- Alt Bilgi ---
st.sidebar.markdown("---")
st.sidebar.markdown("Geliştirici: SeyidAI")

