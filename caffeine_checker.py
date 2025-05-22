import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, grey, darkblue
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
import io
from datetime import datetime
import os

# 기본 설정
st.set_page_config(
    page_title="AI기반 맞춤형 카페인-약물 상호작용 분석기",
    page_icon="☕",
    layout="centered"
)

def check_page_overflow(pdf, y, margin, FONT_NAME):
    if y < 120:  # 임계값은 여백과 바닥글 고려해 80~100 정도
        pdf.showPage()
        pdf.setFont(FONT_NAME, 11)
        return 780  # 새 페이지에서의 y 시작 위치
    return y


# 세션 상태 초기화
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'show_result' not in st.session_state:
    st.session_state.show_result = False

# 폰트 디렉토리 확인 및 생성
FONT_DIR = "fonts"
if not os.path.exists(FONT_DIR):
    os.makedirs(FONT_DIR)

# 한글 폰트 처리 - 더 안전한 방식으로 수정
try:
    # 이미 폰트가 등록되어 있는지 확인
    if 'NanumGothic' not in pdfmetrics._fonts:
        # 폰트 파일이 존재하는지 확인
        font_path = os.path.join(FONT_DIR, 'NanumGothic.ttf')
        if not os.path.exists(font_path):
            st.warning("한글 폰트 파일이 없습니다. PDF 생성 시 한글이 제대로 표시되지 않을 수 있습니다.")
            # 기본 폰트 사용 (한글 깨질 수 있음)
            FONT_NAME = "Helvetica"
        else:
            pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
            FONT_NAME = "NanumGothic"
    else:
        FONT_NAME = "NanumGothic"
except Exception as e:
    st.error(f"폰트 로딩 중 오류 발생: {e}")
    FONT_NAME = "Helvetica"  # 기본 폰트로 대체

# UI 스타일링
st.markdown("""
    <style>
    .main { background-color: #f8f5f2; }
    .block-container { padding-top: 2rem; }
    h1, h2, h3, h4 { color: #4b3832; }
    .stButton>button {
        background-color: #4b3832;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #6a5043;
    }
    .header-container {
        display: flex;
        justify-content: center;
        text-align: center;
    }
    .copyright {
        text-align: center;
        color: #6a5043;
        font-size: 12px;
        margin-top: 10px;
    }
    .section-container {
        background-color: #f0e6da;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .info-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 4px solid #4b3832;
        color: #333333;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #ffeeba;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #c3e6cb;
    }
    .tab-subheader {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
        color: #4b3832;
    }
    .result-header {
        background-color: #6a5043;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 헤더 및 저작권
st.markdown("<div class='copyright'>© 2025 Copyright Jungho Sohn</div>", unsafe_allow_html=True)

# 썸네일 이미지 중앙 배치
col1, col2, col3 = st.columns([1, 2, 1])
with col2:  # 중앙 컬럼에 이미지 배치
    try:
        st.image("https://raw.githubusercontent.com/Jay99Sohn/caffeine-checker/main/thumbnail.png", width=400)
    except:
        st.info("썸네일 이미지를 로드할 수 없습니다.")

st.markdown("""
    <h1 style='text-align: center; color: #4b3832;'>☕ AI기반 카페인-약물 궁합 분석기 💊</h1>
    <p style='text-align: center;'>카페인 섭취와 약물 복용 간의 상호작용을 분석하여 맞춤형 가이드를 제공합니다.</p>
    <hr style='border: 1px solid #d3c0b0;'>
""", unsafe_allow_html=True)


# 분석 함수들
def get_drug_interaction(drug, symptoms, health_conditions):
    """약물과 카페인 간의 상호작용을 분석"""
    if not drug:  # 빈 문자열 체크
        return "약물 정보가 없습니다."

    if "타이레놀 (아세트아미노펜)" in drug:
        return "해열진통제는 카페인과 직접적 상호작용은 없지만, 간 대사 경로 일부 겹침 가능성 있으므로 고용량 병용은 피하는 것이 좋습니다."
    elif "이부프로펜, 덱시부프로펜 (NSAIDs)" in drug:
        if "속쓰림" in symptoms or "위염/역류성 식도염" in health_conditions:
            return "NSAIDs는 위장 자극이 있고, 카페인은 위산을 자극하므로 위장관 부담이 증가할 수 있습니다."
        return "공복 섭취 시 위장 자극 가능성 있습니다."
    elif "항히스타민제" in drug:
        return "항히스타민제는 졸음을 유발하며, 카페인은 각성 작용이 있어 수면 방해 가능성이 있습니다."
    elif "진정제/수면제" in drug:
        return "진정제 복용자는 카페인 섭취로 수면 효과가 감소할 수 있습니다. 특히 취침 전 복용 시 주의하세요."
    elif "위장약" in drug:
        return "위산 억제제 복용 중 과량의 카페인은 위장관 불편을 유발할 수 있습니다."
    elif "항우울제" in drug:
        if "불안" in symptoms or "불안장애" in health_conditions:
            return "SSRI 복용자는 카페인 과다 섭취 시 불안, 심박 증가 가능성이 있습니다."
        return "카페인은 기분, 수면에 영향을 줄 수 있으므로 SSRI 복용 시 모니터링 필요합니다."

    return "카페인 민감도에 따라 증상이 나타날 수 있습니다."


def analyze_timing_interaction(drugs_list, caffeine_time, medicine_time):
    """약물 복용 시간과 카페인 섭취 시간 간의 상호작용 분석"""
    warnings = []

    # 약물 리스트가 비어있으면 빈 경고 반환
    if not drugs_list:
        return warnings

    for drug in drugs_list:
        if "진정제/수면제" in drug:
            if medicine_time == "취침 전" and caffeine_time == "오후 3시 이후":
                warnings.append("🛌 진정제를 취침 전 복용 중이므로 오후 늦은 카페인은 수면 방해가 될 수 있습니다.")
        if "항히스타민제" in drug:
            if medicine_time in ["저녁", "취침 전"] and caffeine_time == "오후 3시 이후":
                warnings.append("🌙 항히스타민제 복용과 늦은 카페인 섭취가 충돌할 수 있습니다.")
        if "위장약" in drug:
            if medicine_time == "아침" and caffeine_time == "오전":
                warnings.append("☕ 공복에 카페인은 위장약 효과를 약화시킬 수 있습니다.")

    return warnings


def suggest_safe_caffeine_time(drugs_list, medicine_time):
    """안전한 카페인 섭취 시간 제안"""
    # 약물 리스트가 비어있으면 기본 권장사항 반환
    if not drugs_list:
        return "현재 약물 복용 기준으로 특별한 제한 없이 섭취 가능합니다."

    for drug in drugs_list:
        if "진정제/수면제" in drug and medicine_time == "취침 전":
            return "카페인은 오전 또는 점심 이전 섭취가 권장됩니다."
        if "항히스타민제" in drug and medicine_time in ["저녁", "취침 전"]:
            return "카페인은 가급적 오전 시간대 섭취를 권장합니다."
        if "위장약" in drug and medicine_time == "아침":
            return "카페인은 아침 공복에 피하고, 점심 식후 섭취가 좋습니다."

    return "현재 약물 복용 기준으로 특별한 제한 없이 섭취 가능합니다."


def get_recommendation(caffeine_count, caffeine_time, drugs_list, health_conditions):
    """카페인 섭취 관련 권장사항"""
    tips = []

    if caffeine_count >= 4:
        tips.append("💡 하루 4잔 이상 카페인 섭취는 줄이세요. 허브티, 보리차도 좋아요.")

    if any("진정제/수면제" in drug for drug in drugs_list) and caffeine_time == "오후 3시 이후":
        tips.append("🌙 수면제 복용자는 오후 늦은 카페인은 피하세요.")

    if "불안장애" in health_conditions:
        tips.append("🧠 불안장애가 있다면 카페인은 증상을 악화시킬 수 있어요.")

    if "위염/역류성 식도염" in health_conditions:
        tips.append("🍵 위장 질환이 있다면 카페인은 저카페인 음료로 대체하는 것이 좋아요.")

    if "고혈압" in health_conditions:
        tips.append("❤️ 고혈압이 있다면 카페인은 혈압을 일시적으로 상승시킬 수 있어요.")

    if not tips:
        tips.append("✅ 현재 습관은 비교적 적절해 보입니다.")

    return tips


# PDF 생성 함수 개선
def generate_pdf(user_data):
    """PDF 결과지 생성 - 개선된 레이아웃과 가독성"""
    buffer = io.BytesIO()

    if not user_data:
        st.error("사용자 데이터가 없습니다.")
        return None

    try:
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setFont(FONT_NAME, 12)
        pdf.setFillColor(black)

        # 페이지 여백 및 너비 설정
        margin = 50
        page_width = A4[0] - 2 * margin

        # 제목 및 기본 정보 - 시각적으로 분리
        y = 780
        pdf.setFont(FONT_NAME, 18)
        pdf.setFillColor(darkblue)
        pdf.drawString(margin, y, "카페인-약물 궁합 분석 결과지")
        pdf.setFillColor(grey)
        pdf.setFont(FONT_NAME, 10)
        pdf.drawString(margin, y - 20, "by 카페인-약물 궁합 분석기 | © Jungho Sohn")

        # 구분선
        y -= 30
        pdf.setStrokeColor(grey)
        pdf.line(margin, y, A4[0] - margin, y)

        # 기본 정보 섹션
        y -= 30
        pdf.setFillColor(black)
        pdf.setFont(FONT_NAME, 14)
        pdf.drawString(margin, y, "개인 기본 정보")
        y -= 20

        # 기본 정보 테이블 형식
        pdf.setFont(FONT_NAME, 11)
        data_items = [
            ["성명:", user_data['name'], "검사일:", user_data['test_date'].strftime('%Y년 %m월 %d일')],
            ["성별:", user_data['sex'], "나이:", f"{user_data['age']}세"],
            ["체중:", f"{user_data['weight']}kg", "민감도:", user_data['sensitivity_level']]
        ]

        col_widths = [70, 130, 70, page_width - 270]

        for items in data_items:
            for i, item in enumerate(items):
                pdf.drawString(margin + sum(col_widths[:i]), y, item)
            y -= 20

        # 카페인 섭취 정보
        y -= 20
        pdf.setFont(FONT_NAME, 14)
        pdf.drawString(margin, y, "카페인 섭취 현황")
        y -= 20

        pdf.setFont(FONT_NAME, 11)
        pdf.drawString(margin, y, f"• 하루 카페인 섭취량: {user_data['caffeine_intake']}잔 (약 {user_data['actual_mg']:.1f} mg)")
        y -= 20
        pdf.drawString(margin, y, f"• 권장 섭취 한계: {user_data['max_caffeine']:.1f} mg")
        y -= 20
        pdf.drawString(margin, y, f"• 섭취 평가: {user_data['feedback']}")
        y -= 20
        pdf.drawString(margin, y, f"• 주요 섭취 시간대: {user_data['drink_time']}")
        y -= 30

        # 약물 정보
        pdf.setFont(FONT_NAME, 14)
        pdf.drawString(margin, y, "약물 복용 정보")
        y -= 20

        pdf.setFont(FONT_NAME, 11)
        if user_data['drugs']:
            pdf.drawString(margin, y, f"• 복용 중인 약물: {', '.join(user_data['drugs'])}")
        else:
            pdf.drawString(margin, y, "• 복용 중인 약물: 없음")
        y -= 20
        pdf.drawString(margin, y, f"• 주요 복용 시간대: {user_data['drug_time']}")
        y -= 20

        # 증상 및 질환
        symptoms_text = ", ".join(user_data['symptom']) if user_data['symptom'] and "없음" not in user_data[
            'symptom'] else "없음"
        diseases_text = ", ".join(user_data['diseases']) if user_data['diseases'] and "없음" not in user_data[
            'diseases'] else "없음"

        pdf.drawString(margin, y, f"• 카페인 관련 증상: {symptoms_text}")
        y -= 20
        pdf.drawString(margin, y, f"• 진단받은 질환: {diseases_text}")
        y -= 30

        # 구분선
        pdf.setStrokeColor(grey)
        pdf.line(margin, y, A4[0] - margin, y)
        y -= 30

        # 약물-카페인 상호작용
        pdf.setFont(FONT_NAME, 14)
        pdf.setFillColor(darkblue)
        pdf.drawString(margin, y, "약물-카페인 상호작용 분석")
        y -= 25

        pdf.setFillColor(black)
        pdf.setFont(FONT_NAME, 11)

        # 약물-카페인 상호작용 내용
        if user_data['drugs']:
            for d in user_data['drugs']:
                interaction_msg = get_drug_interaction(d, user_data['symptom'], user_data['diseases'])
                pdf.setFont(FONT_NAME if FONT_NAME == 'Helvetica' else FONT_NAME, 11)
                pdf.drawString(margin, y, f"▶ {d}")
                y -= 20

                # 멀티라인 텍스트 처리
                pdf.setFont(FONT_NAME, 11)
                words = interaction_msg.split()
                line = ""
                for word in words:
                    test_line = line + " " + word if line else word
                    if pdf.stringWidth(test_line, FONT_NAME, 11) < page_width - 20:
                        line = test_line
                    else:
                        y = check_page_overflow(pdf, y, margin, FONT_NAME)
                        pdf.drawString(margin + 10, y, line)
                        y -= 15
                        line = word

                if line:
                    y = check_page_overflow(pdf, y, margin, FONT_NAME)
                    pdf.drawString(margin + 10, y, line)
                    y -= 20

        else:
            pdf.drawString(margin, y, "복용 중인 약물이 없습니다.")
            y -= 20

        y -= 10

        # 시간대 상호작용
        pdf.setFont(FONT_NAME, 14)
        pdf.setFillColor(darkblue)
        pdf.drawString(margin, y, "카페인-약물 시간대 상호작용")
        y -= 25

        pdf.setFillColor(black)
        pdf.setFont(FONT_NAME, 11)

        interaction_msgs = analyze_timing_interaction(user_data['drugs'], user_data['drink_time'],
                                                      user_data['drug_time'])
        if interaction_msgs:
            for msg in interaction_msgs:
                words = msg.split()
                line = ""
                for word in words:
                    test_line = line + " " + word if line else word
                    if pdf.stringWidth(test_line, FONT_NAME, 11) < page_width - 20:
                        line = test_line
                    else:
                        y = check_page_overflow(pdf, y, margin, FONT_NAME)
                        pdf.drawString(margin + 10, y, line)
                        y -= 15
                        line = word
                if line:
                    y = check_page_overflow(pdf, y, margin, FONT_NAME)
                    pdf.drawString(margin + 10, y, line)
                    y -= 20
        else:
            pdf.drawString(margin, y, "특별한 시간대 상호작용이 발견되지 않았습니다.")
            y -= 20

        y -= 10

        # 권장 섭취 시간대
        pdf.setFont(FONT_NAME, 14)
        pdf.setFillColor(darkblue)
        pdf.drawString(margin, y, "맞춤형 권장사항")
        y -= 25

        pdf.setFillColor(black)
        pdf.setFont(FONT_NAME, 11)

        safe_time = suggest_safe_caffeine_time(user_data['drugs'], user_data['drug_time'])
        pdf.drawString(margin, y, f"▶ 권장 카페인 섭취 시간대:")
        y -= 20
        pdf.drawString(margin + 10, y, safe_time)
        y -= 25

        # 생활 습관 권장사항
        pdf.drawString(margin, y, "▶ 생활 습관 및 대체 음료:")
        y -= 20

        tips = get_recommendation(user_data['caffeine_intake'], user_data['drink_time'],
                                  user_data['drugs'], user_data['diseases'])
        for tip in tips:
            words = tip.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if pdf.stringWidth(test_line, FONT_NAME, 11) < page_width - 20:
                    line = test_line
                else:
                    y = check_page_overflow(pdf, y, margin, FONT_NAME)
                    pdf.drawString(margin + 10, y, line)
                    y -= 15
                    line = word
            if line:
                y = check_page_overflow(pdf, y, margin, FONT_NAME)
                pdf.drawString(margin + 10, y, line)
                y -= 20

        # 주의사항 출력 전에 공간 부족 확인
        y = check_page_overflow(pdf, y, margin, FONT_NAME)

        pdf.setStrokeColor(grey)
        pdf.line(margin, y, A4[0] - margin, y)
        y -= 20

        pdf.setFont(FONT_NAME, 10)
        y = check_page_overflow(pdf, y, margin, FONT_NAME)
        pdf.drawString(margin, y, "📌 주의사항")
        y -= 15

        pdf.setFont(FONT_NAME, 9)
        for line in [
            "🔎 본 결과는 사용자 입력 기반이며, 전문가 진단을 대체하지 않습니다.",
            "📌 식약처 기준: 성인 1일 400mg, 임산부 300mg 이하 권장",
            "© 2025 카페인-약물 궁합 분석기 | Copyright Jungho Sohn"
        ]:
            y = check_page_overflow(pdf, y, margin, FONT_NAME)
            pdf.drawString(margin, y, line)
            y -= 12

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF 생성 중 오류 발생: {e}")
        return None


# 입력 섹션
st.markdown("<div class='section-container'>", unsafe_allow_html=True)

# 첫 번째 row - 사용자 정보와 약물 정보
row1_col1, row1_col2 = st.columns(2)

# 사용자 정보
with row1_col1:
    st.subheader("😊 사용자 정보")
    name = st.text_input("이름을 입력하세요")
    sex = st.radio("성별", ["남성", "여성"])
    age = st.slider("나이", 15, 80, 30)
    weight = st.number_input("체중 (kg)", min_value=30.0, max_value=120.0, value=60.0, step=1.0)
    test_date = st.date_input("검사일", value=datetime.today())

# 약물 정보
with row1_col2:
    st.subheader("💊 약물 정보")
    drugs = st.multiselect("복용 중인 약물", [
        "타이레놀 (아세트아미노펜)",
        "이부프로펜, 덱시부프로펜 (NSAIDs)",
        "항히스타민제 (세티리진, 레보세티리진, 클로르페니라민, 로라타딘, 펙소페나딘)",
        "진정제/수면제 (로라제팜, 디아제팜, 졸피뎀)",
        "위장약 (에소메프라졸, 오메프라졸, 라베프라졸 등 PPI 계열)",
        "항우울제 (플루옥세틴, 에스시탈로프람, 설트랄린 등 SSRI 계열)"
    ])
    drug_time = st.radio("주요 약물 복용 시간대", ["아침", "점심", "저녁", "취침 전"])

st.markdown("</div>", unsafe_allow_html=True)

# 두 번째 row - 카페인 정보와 건강 상태
st.markdown("<div class='section-container'>", unsafe_allow_html=True)

row2_col1, row2_col2 = st.columns(2)

# 카페인 섭취 정보
with row2_col1:
    st.subheader("☕ 카페인 섭취 정보")
    caffeine_intake = st.slider("하루 카페인 섭취량 (잔 기준)", 0, 6, 2)
    drink_time = st.radio("주요 카페인 섭취 시간대", ["오전", "오후 3시 이전", "오후 3시 이후"])

# 건강 상태
with row2_col2:
    st.subheader("🩺 건강 상태")
    symptom = st.multiselect("카페인 섭취 후 경험하는 증상", ["두근거림", "불면", "속쓰림", "불안", "없음"])
    diseases = st.multiselect("현재 진단받은 질환", ["불안장애", "위염/역류성 식도염", "간질환", "고혈압", "없음"])

st.markdown("</div>", unsafe_allow_html=True)

# 분석 버튼 - 중앙 배치
st.markdown("""
    <div style='display: flex; justify-content: center; margin: 20px 0;'>
        <div style='width: 300px;'>""", unsafe_allow_html=True)
analyze_button = st.button("🔍 궁합 분석하기", key="analyze_button", use_container_width=True)
st.markdown("</div></div>", unsafe_allow_html=True)

# 분석 버튼을 눌렀을 때 결과 저장
if analyze_button:
    # 필수 정보 확인
    if not name:
        st.warning("이름을 입력해주세요.")
    else:
        # 카페인 분석
        max_caffeine = weight * 3  # 체중 기반 권장량
        actual_mg = caffeine_intake * 90  # 1잔당 평균 90mg으로 계산

        # 피드백 생성
        if actual_mg > max_caffeine:
            feedback = "⚠️ 권장량 초과!"
        elif actual_mg > max_caffeine * 0.8:
            feedback = "⚠️ 권장량에 근접"
        else:
            feedback = "✅ 적절한 섭취량"

        # 민감도 점수 계산
        score = 0
        if caffeine_intake >= 4: score += 1
        if drink_time == "오후 3시 이후": score += 1
        if "불면" in symptom: score += 2
        if "두근거림" in symptom: score += 2
        if "불안" in symptom: score += 1
        if "속쓰림" in symptom: score += 1

        # 민감도 레벨 평가
        if score >= 5:
            sensitivity_level = "⚠️ 매우 민감"
        elif score >= 3:
            sensitivity_level = "⚠️ 민감"
        else:
            sensitivity_level = "✅ 낮은 민감도"

        # 사용자 데이터 저장
        st.session_state.user_data = {
            'name': name,
            'age': age,
            'sex': sex,
            'weight': weight,
            'drugs': drugs,
            'drug_time': drug_time,
            'caffeine_intake': caffeine_intake,
            'drink_time': drink_time,
            'symptom': symptom,
            'diseases': diseases,
            'test_date': test_date,
            'max_caffeine': max_caffeine,
            'actual_mg': actual_mg,
            'feedback': feedback,
            'sensitivity_level': sensitivity_level
        }

        # 결과 표시 활성화
        st.session_state.show_result = True

        # PDF 생성 및 세션에 저장
        pdf_buffer = generate_pdf(st.session_state.user_data)
        st.session_state.pdf_buffer = pdf_buffer

# 결과 표시
if st.session_state.show_result and st.session_state.user_data:
    user_data = st.session_state.user_data

    st.markdown("<div class='result-header'><h2>📊 분석 결과</h2></div>", unsafe_allow_html=True)

    # 결과 탭 표시
    tabs = st.tabs(["개인 정보 요약", "약물-카페인 상호작용", "시간대 분석", "권장 사항"])

    # 탭 1: 개인 정보 요약
    with tabs[0]:
        st.markdown("<div class='tab-subheader'>기본 정보</div>", unsafe_allow_html=True)

        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.markdown(
                f"<div class='info-card'><strong>이름:</strong> {user_data['name']}<br><strong>성별:</strong> {user_data['sex']}<br><strong>나이:</strong> {user_data['age']}세<br><strong>체중:</strong> {user_data['weight']}kg</div>",
                unsafe_allow_html=True)

        with info_col2:
            st.markdown(
                f"<div class='info-card'><strong>카페인 민감도:</strong> {user_data['sensitivity_level']}<br><strong>검사일:</strong> {user_data['test_date'].strftime('%Y년 %m월 %d일')}</div>",
                unsafe_allow_html=True)

        st.markdown("<div class='tab-subheader'>카페인 섭취 현황</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='info-card' style='background-color: #f0f8ff; color: #333;'><strong>하루 카페인 섭취량:</strong> {user_data['caffeine_intake']}잔 (약 {user_data['actual_mg']:.1f} mg)<br><strong>권장 섭취 한계:</strong> {user_data['max_caffeine']:.1f} mg<br><strong>섭취 평가:</strong> {user_data['feedback']}<br><strong>주요 섭취 시간대:</strong> {user_data['drink_time']}</div>",
            unsafe_allow_html=True)

    # 탭 2: 약물-카페인 상호작용
    with tabs[1]:
        st.markdown("<div class='tab-subheader'>복용 중인 약물</div>", unsafe_allow_html=True)

        if user_data['drugs']:
            for drug in user_data['drugs']:
                interaction_msg = get_drug_interaction(drug, user_data['symptom'], user_data['diseases'])
                st.markdown(
                    f"<div class='info-card' style='background-color: #eef2f7; color: #333;'><strong>{drug}</strong><br>{interaction_msg}</div>",
                    unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-card' style='background-color: #eef2f7; color: #333;'>복용 중인 약물이 없습니다.</div>",
                        unsafe_allow_html=True)

    # 탭 3: 시간대 분석
    with tabs[2]:
        st.markdown("<div class='tab-subheader'>약물-카페인 시간대 상호작용</div>", unsafe_allow_html=True)

        interaction_msgs = analyze_timing_interaction(user_data['drugs'], user_data['drink_time'],
                                                      user_data['drug_time'])

        if interaction_msgs:
            for msg in interaction_msgs:
                st.markdown(f"<div class='warning-box'>{msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='success-box'>현재 복용 패턴에서는 특별한 시간대 상호작용이 발견되지 않았습니다.</div>", unsafe_allow_html=True)

        st.markdown("<div class='tab-subheader'>권장 카페인 섭취 시간대</div>", unsafe_allow_html=True)
        safe_time = suggest_safe_caffeine_time(user_data['drugs'], user_data['drug_time'])
        st.markdown(f"<div class='info-card' style='background-color: #e6f7ff; color: #333;'>{safe_time}</div>",
                    unsafe_allow_html=True)

    # 탭 4: 권장 사항
    with tabs[3]:
        st.markdown("<div class='tab-subheader'>맞춤형 권장사항</div>", unsafe_allow_html=True)

        tips = get_recommendation(user_data['caffeine_intake'], user_data['drink_time'], user_data['drugs'],
                                  user_data['diseases'])

        for tip in tips:
            st.markdown(f"<div class='info-card' style='background-color: #e8f4ea; color: #333;'>{tip}</div>",
                        unsafe_allow_html=True)

    st.markdown("""
        <style>
        .custom-button {
            background-color: #4CAF50;
            color: white;
            padding: 35px 50px;
            font-size: 32px;
            border: none;
            border-radius: 14px;
            cursor: pointer;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
            transition: background-color 0.3s ease, transform 0.2s ease;
        }
        .custom-button:hover {
            background-color: #45a049;
            transform: scale(1.03);
        }
        </style>

        <div style="text-align: center; margin-top: 40px;">
            <a href="https://forms.gle/QSkosWvZQKuYFGY19" target="_self">
                <button class="custom-button">
                    📨 지금 바로 설문하고 커피 쿠폰 받자!
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

    # PDF 다운로드 버튼
    if st.session_state.pdf_buffer:
        st.markdown("""
            <div style='display: flex; justify-content: center; margin: 20px 0;'>
                <div style='width: 300px;'>""", unsafe_allow_html=True)
        st.download_button(
            label="📥 PDF 결과지 다운로드",
            data=st.session_state.pdf_buffer,
            file_name=f"카페인_약물_궁합분석_{user_data['name']}_{user_data['test_date'].strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            key="download_pdf",
            use_container_width=True
        )
        st.markdown("</div></div>", unsafe_allow_html=True)

    # 재시작 버튼
    st.markdown("""
        <div style='display: flex; justify-content: center; margin: 20px 0;'>
            <div style='width: 300px;'>""", unsafe_allow_html=True)
    if st.button("🔄 다시 분석하기", use_container_width=True):
        st.session_state.user_data = None
        st.session_state.show_result = False
        st.experimental_rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

# 앱 하단 정보 영역
st.markdown("<hr style='border: 1px solid #d3c0b0;'>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; color: #6a5043;'>
        <small>본 분석은 참고용이며, 의학적 처방을 대체할 수 없습니다.<br>
        복용 중인 약물의 정확한 정보는 의사나 약사에게 문의하세요.</small>
    </div>
""", unsafe_allow_html=True)

