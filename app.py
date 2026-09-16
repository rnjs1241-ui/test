import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="LH매입 공유방 Q&A", page_icon="🏠")
st.title("🏠 전세사기특별법 LH매입 Q&A 챗봇 (무료)")
st.caption("카카오톡 단톡방의 기존 질문과 대화 내역을 기반으로 답변합니다.")

# 대화 내역 로드 (무료 1분당 토큰 제한 방지를 위해 20,000자로 조정)
@st.cache_data
def load_chat():
    try:
        with open("KakaoTalkChats.txt", "r", encoding="utf-8") as f:
            text = f.read()
            return text[:20000]
    except FileNotFoundError:
        return ""

chat_context = load_chat()

# Secrets에서 API 키 로드
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Gemini API Key", type="password")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 질문 처리
if prompt := st.chat_input("질문을 입력하세요 (예: 감평 예상가 어떻게 물어보나요?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not api_key:
        st.error("사이드바에 Gemini API Key를 입력하거나 Secrets를 설정해 주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            # 권장 표준 모델 적용
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            system_instruction = f"""
            너는 전세사기특별법 LH매입 카카오톡 단체방의 대화 기록을 기반으로 주민들의 질문에 답해주는 조력자 AI야.
            아래 [카톡 대화 데이터]를 바탕으로 핵심을 정확하고 알기 쉽게 안내해줘.

            [카톡 대화 데이터]
            {chat_context}
            """
            
            full_prompt = f"{system_instruction}\n\n사용자 질문: {prompt}"
            
            with st.chat_message("assistant"):
                # 애니메이션을 표시할 공간 확보
                placeholder = st.empty()
                
                # 로딩 애니메이션 및 안내 문구 HTML/CSS
                loading_html = """
                <style>
                @keyframes pulse-emoji {
                    0%, 100% { transform: scale(0.9); opacity: 0.5; }
                    50% { transform: scale(1.4); opacity: 1; }
                }
                .loading-box {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 15px;
                    font-weight: 600;
                    color: #4A5568;
                    padding: 8px 0;
                }
                .pulse-emoji {
                    display: inline-block;
                    font-size: 18px;
                    animation: pulse-emoji 1.2s infinite ease-in-out;
                }
                .e1 { animation-delay: 0.0s; }
                .e2 { animation-delay: 0.3s; }
                .e3 { animation-delay: 0.6s; }
                </style>

                <div class="loading-box">
                    약 2년간 쌓인 대화 내용을 분석하여 답변을 생성하는 중...
                    <span class="pulse-emoji e1">🔍</span>
                    <span class="pulse-emoji e2">💭</span>
                    <span class="pulse-emoji e3">🧠</span>
                </div>
                """
                
                # 대기 상태 애니메이션 노출
                placeholder.markdown(loading_html, unsafe_allow_html=True)
                
                # API 호출 및 답변 생성
                response = model.generate_content(full_prompt)
                
                # 완료 후 로딩 애니메이션을 지우고 최종 답변 표시
                placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

        except Exception as e:
            # 429 무료 할당량 초과 시 예외 처리
            if "429" in str(e) or "Quota exceeded" in str(e):
                st.warning("⏱️ 현재 무료 이용 한도(429)에 도달했습니다. 약 30초~1분 뒤 다시 질문해 주세요!")
            else:
                st.error(f"답변 생성 중 오류가 발생했습니다: {e}")
