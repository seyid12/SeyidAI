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
    # Mesaj giriş kutusunu altta tutmak için container kullanıyoruz
    chat_container = st.container()
    
    # Sidebar'a sohbet ayarları ve bilgi ekle
    with st.sidebar:
        st.markdown("### 🛠️ Sohbet Ayarları")
        
        if st.button("🔄 Yeni Sohbet Başlat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        ### 💡 İpuçları
        - Uzun mesajlar için Enter tuşunu kullanın
        - Kod paylaşırken \\` işaretleri kullanın
        - Karmaşık sorular için detay verin
        """)
        
        st.markdown("---")
        st.markdown("### 🎯 Özellikler")
        st.markdown("""
        • 💭 Genel sohbet & yardım
        • 📚 PDF analizi
        • 🖼️ Görsel yorumlama
        """)

    # Modern chat template stili
    st.markdown("""
        <style>
        /* Chat container stilleri */
        .stChatMessage {
            padding: 1.5rem;
            border-radius: 1rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(128, 128, 128, 0.1);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            max-width: 85%;
            transition: all 0.3s ease;
        }
        
        /* Kullanıcı mesajları */
        .stChatMessage.user {
            background: linear-gradient(135deg, #6B46C1 0%, #4F46E5 100%);
            color: white !important;
            margin-left: auto;
            border-bottom-right-radius: 0.2rem;
        }
        .stChatMessage.user p {
            color: white !important;
        }
        
        /* Asistan mesajları */
        .stChatMessage.assistant {
            background: white;
            margin-right: auto;
            border-bottom-left-radius: 0.2rem;
        }
        
        /* Emoji avatar stilleri */
        .stChatMessage .avatar {
            font-size: 1.2rem;
            margin-right: 0.5rem;
        }
        
        /* Markdown içerik stilleri */
        .stChatMessage p {
            margin: 0;
            line-height: 1.6;
        }
        
        /* Kod blokları için özel stil */
        .stChatMessage code {
            background: rgba(0,0,0,0.05);
            padding: 0.2em 0.4em;
            border-radius: 0.3rem;
            font-size: 0.9em;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sohbet geçmişini Streamlit session state'de saklama
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        # Hoş geldin mesajı
        welcome_msg = {
            "role": "model",
            "text": "Merhaba! 👋 Nasıl yardımcı olabilirim?"
        }
        st.session_state.chat_history.append(welcome_msg)

    # Ana sohbet alanı
    with chat_container:
        # Mesaj geçmişi için scrollable alan
        with st.container():
            for message in st.session_state.chat_history:
                avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["text"])
        
        # En son mesaja otomatik kaydırma için JavaScript
        st.markdown("""
            <script>
                var elements = window.parent.document.querySelectorAll('.stChatMessage');
                if (elements.length > 0) {
                    elements[elements.length - 1].scrollIntoView();
                }
            </script>
            """, unsafe_allow_html=True)
    
    # Mesaj giriş kutusunu en alta sabitleme
    st.markdown(
        """
        <style>
        .stChatInputContainer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 1rem;
            background: white;
            z-index: 100;
            border-top: 1px solid rgba(128, 128, 128, 0.1);
        }
        /* Ana içerik için padding ekliyoruz ki mesaj kutusu içeriği kapatmasın */
        .main > div {
            padding-bottom: 100px;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # Kullanıcı girişi - artık her zaman altta kalacak
    if prompt := st.chat_input("Mesajınızı buraya yazın..."):
        
        # Kullanıcı mesajını geçmişe ekleme ve gösterme
        st.session_state.chat_history.append({"role": "user", "text": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # Modelden yanıt alma (streaming)
        with st.chat_message("model", avatar="🤖"):
            full_response = ""
            message_placeholder = st.empty()
            
            try:
                # Düzeltilmiş sohbet geçmişi dönüşümü
                gemini_contents = []
                for msg in st.session_state.chat_history:
                    # Son kullanıcı mesajını hariç tut (ayrıca eklenecek)
                    if msg == st.session_state.chat_history[-1] and msg["role"] == "user":
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


                # Modelimize doğal yanıt verme talimatı
                system_prompt = """Sen yardımcı bir asistansın. Yanıtların:
                - Doğal ve samimi olmalı
                - Kısa ve öz olmalı
                - Gereksiz tekrarlardan kaçınmalı
                - "Ben bir AI'yım" gibi ifadeler kullanmamalı
                Kullanıcıyla normal bir sohbet gibi ilerle."""

                # İçeriğe system prompt'u ekle
                gemini_contents.insert(0, types.Content(
                    role="model",
                    parts=[types.Part(text=system_prompt)]
                ))

                # generate_content_stream kullanılarak akışlı yanıt alınıyor
                response_stream = client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=gemini_contents
                )
                
                # Streaming yanıt
                typing_char = "▌"
                for chunk in response_stream:
                    full_response += chunk.text
                    message_placeholder.markdown(f"{full_response}{typing_char}")
                
                # Final yanıt - gereksiz boşlukları temizle
                full_response = full_response.strip()
                message_placeholder.markdown(full_response)
                
                # Tam yanıtı geçmişe ekleme
                st.session_state.chat_history.append({"role": "model", "text": full_response})

            except APIError as e:
                error_msg = f"🚨 API Hatası: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.chat_history.append({"role": "model", "text": f"*{error_msg}*"})
            except Exception as e:
                error_msg = f"⚠️ Beklenmedik bir hata oluştu: {type(e).__name__} - {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.chat_history.append({"role": "model", "text": f"*{error_msg}*"})

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
st.sidebar.markdown("Geliştirici: Seyid Yıldız")


