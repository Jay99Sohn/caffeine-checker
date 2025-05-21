import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.colors import black, HexColor
import io
from datetime import datetime

# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('NanumGothic', 'fonts/NanumGothic.ttf'))

# Streamlit UI 꾸미기
st.markdown("""
    <style>
    .main {
        background-color: #f8f5f2;
    }
    .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3, h4 {
        color: #4b3832;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center; color: #4b3832;'>☕ 카페인-약물 궁합 분석기 💊</h1>
    <p style='text-align: center;'>카페인 섭취와 약물 복용 간의 상호작용을 분석하여 맞춤형 가이드를 제공합니다.</p>
    <hr style='border: 1px solid #d3c0b0;'>
""", unsafe_allow_html=True)

# 사용자 정보 입력
name = st.text_input("이름을 입력하세요")
sex = st.radio("성별", ["남성", "여성"])
age = st.slider("나이", 15, 80)
weight = st.number_input("체중 (kg)", min_value=30.0, max_value=120.0, step=1.0)

test_date = st.date_input("검사일", value=datetime.today())

# 카페인 섭취 정보
caffeine_intake = st.slider("하루 카페인 섭취량 (잔 기준)", 0, 6)
drink_time = st.radio("카페인 섭취 시간대", ["오전", "오후 3시 이전", "오후 3시 이후"])

# 민감도 증상 선택
symptom = st.multiselect("카페인 섭취 후 경험하는 증상", ["두근거림", "불면", "속쓰림", "불안", "없음"])

# 복용 약물 선택 (세분화)
drug = st.selectbox("복용 중인 약물", [
    "없음",
    "타이레놀 (아세트아미노펜)",
    "이부프로펜, 덱시부프로펜 (NSAIDs)",
    "항히스타민제 (세티리진, 레보세티리진, 클로르페니라민, 로라타딘, 펙소페나딘)",
    "진정제/수면제 (로라제팜, 디아제팜, 졸피뎀)",
    "위장약 (에소메프라졸, 오메프라졸, 라베프라졸 등 PPI 계열)",
    "항우울제 (플루옥세틴, 에스시탈로프람, 설트랄린 등 SSRI 계열)"
])

# PDF 생성 함수 (결과 평가 포함)
def generate_pdf(name, age, sex, weight, drug, caffeine_intake, drink_time, symptom, test_date, max_caffeine, actual_mg, feedback, sensitivity_level):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("NanumGothic", 18)
    p.setFillColor(HexColor("#4b3832"))
    p.drawString(50, 800, "☕ 카페인-약물 궁합 분석 결과지 💊")

    p.setFont("NanumGothic", 12)
    p.setFillColor(black)
    y = 760

    info = [
        f"검사일: {test_date.strftime('%Y년 %m월 %d일')}",
        f"성명: {name}",
        f"성별: {sex} / 나이: {age}세 / 체중: {weight}kg",
        f"복용 중인 약물: {drug}",
        f"하루 카페인 섭취량: {caffeine_intake}잔 (약 {actual_mg:.1f} mg)",
        f"섭취 시간대: {drink_time}",
        f"카페인 섭취 후 경험한 증상: {', '.join(symptom) if symptom else '없음'}",
        f"권장 최대 카페인 섭취량: {max_caffeine:.1f} mg/day",
        f"현재 섭취량 평가: {feedback}",
        f"카페인 민감도 평가: {sensitivity_level}"
    ]

    for line in info:
        p.drawString(50, y, line)
        y -= 24

    p.setStrokeColor(HexColor("#cccccc"))
    p.line(40, y, 550, y)
    y -= 30

    p.setFont("NanumGothic", 10)
    p.setFillColor(HexColor("#333333"))
    p.drawString(50, y, "🔎 본 결과는 사용자 입력 기반이며, 의료 전문가의 진단을 대체하지 않습니다.")
    y -= 18
    p.drawString(50, y, "📌 참고: 식품의약품안전처(KMFDS)는 성인의 카페인 1일 섭취 권장 상한을 400mg, 임산부는 300mg 이하로 제시하고 있습니다.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# 분석 버튼
if st.button("🔍 궁합 분석하기"):
    st.subheader(f"📋 {name}님의 개인 맞춤 분석 결과")

    max_caffeine = weight * 3
    actual_mg = caffeine_intake * 90
    st.markdown(f"💡 **권장 최대 카페인 섭취량**: {max_caffeine:.1f} mg/day")
    st.markdown(f"☕ 현재 추정 섭취량: **{actual_mg:.1f} mg/day**")

    if actual_mg > max_caffeine:
        feedback = "⚠️ 권장량을 초과하고 있습니다. 카페인 섭취를 줄이세요."
        st.error(feedback)
    elif actual_mg > max_caffeine * 0.8:
        feedback = "⚠️ 권장량에 가까워지고 있습니다. 주의가 필요합니다."
        st.warning(feedback)
    else:
        feedback = "✅ 카페인 섭취량이 적절한 범위입니다."
        st.success(feedback)

    score = 0
    if caffeine_intake >= 4: score += 1
    if drink_time == "오후 3시 이후": score += 1
    if "불면" in symptom: score += 2
    if "두근거림" in symptom: score += 2
    if "불안" in symptom: score += 1
    if "속쓰림" in symptom: score += 1

    st.subheader("📊 카페인 민감도 레벨")
    st.progress(min(score * 10, 100))

    if score >= 5:
        sensitivity_level = "⚠️ 매우 민감한 체질입니다. 카페인 제한이 필요합니다."
        st.error(sensitivity_level)
    elif score >= 3:
        sensitivity_level = "⚠️ 민감한 편입니다. 섭취량과 시간대에 주의하세요."
        st.warning(sensitivity_level)
    else:
        sensitivity_level = "✅ 카페인에 대한 민감도가 낮은 편입니다."
        st.success(sensitivity_level)

    pdf_file = generate_pdf(name, age, sex, weight, drug, caffeine_intake, drink_time, symptom, test_date, max_caffeine, actual_mg, feedback, sensitivity_level)
    st.download_button(
        label="📄 분석 결과 PDF 다운로드",
        data=pdf_file,
        file_name="카페인-약물-분석결과.pdf",
        mime="application/pdf"
    )

    st.markdown("---")
    st.caption("🔎 본 앱은 의약학적 참고 자료를 기반으로 하며, 정확한 진단 및 처방은 의료 전문가와 상담하세요.")
    st.caption("📌 참고: 식약처 기준에 따르면 성인의 1일 카페인 권장 상한은 400mg, 임산부는 300mg 이하입니다.")
