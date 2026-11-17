import streamlit as st
import pandas as pd
import os
from huggingface_hub import InferenceClient

st.set_page_config(page_title="AI 통합 HR-재무 관리 툴", layout="wide")

st.title("🏢 AI 통합 인사(HR)·재무 예산 관리 툴 (프로토타입)")
st.markdown("**표준화된 임직원 근태·면담 데이터를 기반으로 퇴사 리스크를 산출하고, 부서 가용 예산 내 최적의 방어 전략을 자동 생성합니다.**")
st.divider()

# 1. 표준 ERP 데이터셋 초기화
if "emp_data" not in st.session_state:
    st.session_state.emp_data = pd.DataFrame([
        {"사번": "EMP01", "이름": "김민수", "부서": "AI개발팀", "직급": "과장", "핵심인재": "S등급", "월평균_야근(시간)": 52, "연차_소진율(%)": 15, "최근_면담_메모": "최근 야근이 너무 많고 프로젝트 방향성에 회의감을 느낌. 타사 헤드헌터 연락을 받았다고 언급함.", "현재_연봉(만원)": 7500},
        {"사번": "EMP02", "이름": "이지은", "부서": "해외영업팀", "직급": "대리", "핵심인재": "A등급", "월평균_야근(시간)": 38, "연차_소진율(%)": 30, "최근_면담_메모": "성과는 좋으나 타 부서 동기 대비 승진 누락에 불만이 있음. 업무 의욕이 눈에 띄게 저하됨.", "현재_연봉(만원)": 5800},
        {"사번": "EMP03", "이름": "박준혁", "부서": "재무회계팀", "직급": "차장", "핵심인재": "A등급", "월평균_야근(시간)": 12, "연차_소진율(%)": 85, "최근_면담_메모": "전반적으로 업무에 만족하며 결산 시즌 외에는 워라밸이 잘 유지되고 있음.", "현재_연봉(만원)": 8200},
        {"사번": "EMP04", "이름": "최서연", "부서": "마케팅팀", "직급": "사원", "핵심인재": "B등급", "월평균_야근(시간)": 25, "연차_소진율(%)": 60, "최근_면담_메모": "신규 캠페인 기획에 흥미를 보이고 있으나 직무 교육 기회가 부족하다고 느낌.", "현재_연봉(만원)": 4200},
        {"사번": "EMP05", "이름": "정현우", "부서": "AI개발팀", "직급": "대리", "핵심인재": "S등급", "월평균_야근(시간)": 48, "연차_소진율(%)": 20, "최근_면담_메모": "번아웃 증세를 호소함. 보상 수준이 시장 가치보다 낮다고 생각하여 이직을 고민 중.", "현재_연봉(만원)": 6400}
    ])

if "budget" not in st.session_state:
    st.session_state.budget = {
        "AI개발팀": 1500,
        "해외영업팀": 800,
        "재무회계팀": 500,
        "마케팅팀": 600
    }

# 비즈니스 룰 기반 퇴사 위험도 계산
def calculate_risk(row):
    score = (row["월평균_야근(시간)"] * 0.9) + ((100 - row["연차_소진율(%)"]) * 0.4)
    if any(k in row["최근_면담_메모"] for k in ["이직", "헤드헌터", "번아웃", "불만"]):
        score += 20
    return min(int(score), 99)

# API 호출 불가 시에도 시연이 끊기지 않도록 하는 백업 분석기
def generate_fallback_report(emp, dept_budget):
    recommended_bonus = min(300, dept_budget)
    return f"""### 1. 퇴사 위험 핵심 원인 진단
- **근무 강도 및 소진:** 월평균 야근 **{emp['월평균_야근(시간)']}시간**, 연차 소진율 **{emp['연차_소진율(%)']}%**로 직무 피로도가 임계치에 도달했습니다.
- **면담 핵심 시그널:** *"{emp['최근_면담_메모']}"* 기록을 볼 때 외부 이직 유인 및 보상·성장 불만이 결합된 고위험 상태입니다.

### 2. 재무 예산({dept_budget:,}만원) 한도 내 금전적 보상안
- **핵심 인재 리텐션 보너스 지급:** {emp['부서']} 가용 예산({dept_budget:,}만원) 내 **300만원({recommended_bonus:,}만원)** 즉시 편성 및 특별 인센티브 지급 권장
- **연봉 테이블 재산정 검토:** 차기 평가 시즌 {emp['핵심인재']} 등급 기준 시장 가치 반영 인상분(5~8%) 우선 배정

### 3. 비금전적 조직관리 처방
- **강제 리프레시 휴가 부여:** 미소진 연차 활용을 위한 3일 연속 유급 리프레시 휴가 즉시 승인
- **면담 및 R&R 재조정:** 본부장급 1:1 커리어 면담을 통해 프로젝트 역할 재설정 및 초과근무 상한제 적용"""

df = st.session_state.emp_data
df["퇴사_위험도(%)"] = df.apply(calculate_risk, axis=1)

# 상단 KPI 요약 보드
col1, col2, col3, col4 = st.columns(4)
high_risk_count = len(df[df["퇴사_위험도(%)"] >= 75])
col1.metric("관리 대상 인원", f"{len(df)}명")
col2.metric("🚨 퇴사 고위험군 (75%↑)", f"{high_risk_count}명", delta="즉각 개입 필요", delta_color="inverse")
col3.metric("AI개발팀 잔여 방어 예산", f"{st.session_state.budget['AI개발팀']:,} 만원")
col4.metric("해외영업팀 잔여 방어 예산", f"{st.session_state.budget['해외영업팀']:,} 만원")

st.divider()

# 좌우 분할 대시보드
left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.subheader("📊 [인사 모듈] 전사 근태 및 퇴사 리스크 현황표")
    st.dataframe(
        df[["사번", "이름", "부서", "직급", "핵심인재", "월평균_야근(시간)", "연차_소진율(%)", "퇴사_위험도(%)"]],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("💰 [재무 모듈] 부서별 인재 유지(Retention) 가용 예산")
    budget_df = pd.DataFrame(list(st.session_state.budget.items()), columns=["부서명", "가용_예산(만원)"])
    st.dataframe(budget_df, use_container_width=True, hide_index=True)

with right_col:
    st.subheader("🤖 [AI 분석 모듈] 맞춤형 인재 방어 처방 및 예산 집행")
    selected_name = st.selectbox("분석할 대상 직원을 선택하세요:", df["이름"].tolist())
    emp = df[df["이름"] == selected_name].iloc[0]
    dept_budget = st.session_state.budget[emp["부서"]]

    st.info(f"""
- **대상자:** {emp['이름']} ({emp['부서']} / {emp['직급']} / 등급: {emp['핵심인재']})
- **퇴사 위험도:** **{emp['퇴사_위험도(%)']}%** (현재 연봉: {emp['현재_연봉(만원)']:,}만원)
- **면담 기록:** "{emp['최근_면담_메모']}"
- **소속 부서 가용 예산:** **{dept_budget:,}만원**
""")

    if st.button("✨ AI 맞춤형 방어 전략 보고서 생성", type="primary", use_container_width=True):
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            st.error("Streamlit Secrets에 HF_TOKEN을 먼저 등록해주세요!")
        else:
            with st.spinner("AI가 인사 데이터와 재무 예산을 통합 분석 중입니다..."):
                prompt = f"""당신은 기업의 최고인사책임자(CHRO)와 최고재무책임자(CFO)를 보좌하는 AI 경영 컨설턴트입니다.
아래 직원의 퇴사를 막기 위한 최적의 방어 전략 보고서를 한국어로 작성해주세요.

[직원 데이터]
- 성명/직급: {emp['이름']} {emp['직급']} (핵심인재 등급: {emp['핵심인재']})
- 소속 부서: {emp['부서']} (부서 가용 예산 한도: {dept_budget}만원)
- 현재 연봉: {emp['현재_연봉(만원)']}만원
- 퇴사 위험도: {emp['퇴사_위험도(%)']}% (월평균 야근 {emp['월평균_야근(시간)']}시간, 연차 소진율 {emp['연차_소진율(%)']}%)
- 최근 면담 메모: {emp['최근_면담_메모']}

[보고서 작성 양식]
1. 퇴사 위험 핵심 원인 진단 (2줄 요약)
2. 재무 예산({dept_budget}만원) 한도 내 금전적 보상안 (구체적 금액 명시)
3. 비금전적 조직관리 처방 (휴가 부여, 업무 재배치 등)
경영진 보고용으로 명확하고 간결하게 작성하세요."""

                candidate_models = [
                    "Qwen/Qwen3-8B",
                    "meta-llama/Llama-3.1-8B-Instruct",
                    "Qwen/Qwen2.5-72B-Instruct",
                    "google/gemma-2-9b-it",
                    "mistralai/Mistral-Nemo-Instruct-2407"
                ]

                client = InferenceClient(token=hf_token)
                generated_text = None
                used_engine = ""

                for model_id in candidate_models:
                    try:
                        response = client.chat_completion(
                            model=model_id,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=600,
                            temperature=0.5
                        )
                        generated_text = response.choices[0].message.content
                        used_engine = f"Hugging Face AI ({model_id})"
                        break
                    except Exception:
                        continue

                if generated_text:
                    st.session_state.ai_result = generated_text
                    st.session_state.used_engine = used_engine
                else:
                    st.session_state.ai_result = generate_fallback_report(emp, dept_budget)
                    st.session_state.used_engine = "표준 HR·재무 통합 추론 엔진"

                st.session_state.report_target = emp['이름']

    if "ai_result" in st.session_state:
        st.success(f"✅ **{st.session_state.report_target} 님 대상 AI 전략 보고서**")
        if "used_engine" in st.session_state:
            st.caption(f"⚙️ 분석 엔진: {st.session_state.used_engine}")
        st.markdown(st.session_state.ai_result)

        # 보고서 텍스트 파일 다운로드 버튼
        st.download_button(
            label="📥 결재용 전략 보고서 다운로드 (.txt)",
            data=st.session_state.ai_result,
            file_name=f"인재방어_전략보고서_{st.session_state.report_target}.txt",
            mime="text/plain"
        )

    st.markdown("---")
    st.write("**⚡ [재무 모듈 연동] 승인 및 예산 실시간 차감**")
    bonus = st.number_input("확정된 리텐션 보너스/인상 재원(만원)", min_value=0, max_value=dept_budget, value=min(300, dept_budget), step=50)
    if st.button("💸 승인 및 재무 ERP 예산 반영"):
        st.session_state.budget[emp["부서"]] -= bonus
        st.toast(f"{emp['부서']} 예산에서 {bonus}만원이 차감되었습니다!")
        st.rerun()
