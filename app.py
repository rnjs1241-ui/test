import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="LH매입 공유방 Q&A", page_icon="🏠")
st.title("🏠 전세사기특별법 LH매입 Q&A 챗봇 (무료)")
st.caption("카카오톡 단톡방의 기존 질문과 대화 내역을 기반으로 답변합니다.")

# 대화 내역 로드 (무료 1분당 토큰 제한(429) 초과 방지를 위해 20,000자로 조정)
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
            # 무료 할당량이 안정적인 정식 모델 적용
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            system_instruction = f"""
            너는 전세사기특별법 LH매입 카카오톡 단체방의 대화 기록을 기반으로 주민들의 질문에 답해주는 조력자 AI야.
            아래 [카톡 대화 데이터]를 바탕으로 핵심을 정확하고 알기 쉽게 안내해줘.

            [카톡 대화 데이터]
            {chat_context}
            """
            
            full_prompt = f"{system_instruction}\n\n사용자 질문: {prompt}"
            
            with st.chat_message("assistant"):
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            # 429 (사용량 초과) 에러 감지 시 친절한 안내 메시지 출력
            if "429" in str(e) or "Quota exceeded" in str(e):
                st.warning("⏱️ 현재 요청이 많아 일시적으로 제한되었습니다. 약 30초 후 다시 시도해 주세요!")
            else:
                st.error(f"답변 생성 중 오류가 발생했습니다: {e}")
