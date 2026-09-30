import streamlit as st
import requests
import re
from collections import Counter


# ==========================================
# 페이지 설정
# ==========================================

st.set_page_config(
    page_title="우리 학교 메뉴별 급식",
    page_icon="🍴",
    layout="wide"
)


# ==========================================
# 제목
# ==========================================

st.title("🍴 우리 학교 메뉴별 급식")

st.write(
    "송탄고등학교의 2025년 9월부터 2026년 9월까지 "
    "중식 메뉴를 분석합니다."
)

st.caption(
    "📊 탐구 주제: 초등학교·중학교·고등학교 급식 평균 칼로리는 얼마나 차이날까?"
)


# ==========================================
# 기본 정보
# ==========================================

OFFICE_CODE = "J10"
SCHOOL_CODE = "7530480"

MEAL_API = (
    "https://open.neis.go.kr/hub/mealServiceDietInfo"
)

START_DATE = "20250901"
END_DATE = "20260930"

MEAL_CODE = "2"  # 중식


# ==========================================
# Secrets에서 인증키 가져오기
# ==========================================

if "NEIS_API_KEY" not in st.secrets:

    st.error(
        "NEIS_API_KEY가 Streamlit Secrets에 설정되어 있지 않습니다."
    )

    st.info(
        "Streamlit의 Secrets 설정에서 "
        "`NEIS_API_KEY`를 추가해 주세요."
    )

    st.stop()


NEIS_API_KEY = st.secrets["NEIS_API_KEY"]


# ==========================================
# 알레르기 번호 제거
# ==========================================

def remove_allergy_number(menu):

    # 예:
    # 김치찌개(5.6.9) → 김치찌개
    # 계란찜(1) → 계란찜

    return re.sub(
        r"\(\s*\d+(?:\.\d+)*\s*\)",
        "",
        menu
    ).strip()


# ==========================================
# 메뉴 하나의 이름 정리
# ==========================================

def clean_menu(menu):

    menu = menu.strip()

    # 알레르기 번호 제거
    menu = remove_allergy_number(menu)

    # 앞뒤 공백 제거
    menu = menu.strip()

    return menu


# ==========================================
# NEIS API에서 전체 급식 데이터 가져오기
# ==========================================

@st.cache_data(show_spinner=False)
def get_all_meals():

    all_rows = []

    page = 1
    page_size = 1000

    total_count = None


    # --------------------------------------
    # 전체 데이터가 올 때까지 반복
    # --------------------------------------

    while True:

        params = {
            "KEY": NEIS_API_KEY,
            "Type": "json",

            "ATPT_OFCDC_SC_CODE": OFFICE_CODE,
            "SD_SCHUL_CODE": SCHOOL_CODE,

            # 중식만 조회
            "MMEAL_SC_CODE": MEAL_CODE,

            "MLSV_FROM_YMD": START_DATE,
            "MLSV_TO_YMD": END_DATE,

            "pSize": page_size,
            "pIndex": page
        }


        response = requests.get(
            MEAL_API,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()


        # ----------------------------------
        # 데이터가 없는 경우
        # ----------------------------------

        if "mealServiceDietInfo" not in data:
            return []


        # ----------------------------------
        # 전체 건수 확인
        # ----------------------------------

        head = data["mealServiceDietInfo"][0].get(
            "head",
            []
        )

        if head:

            for item in head:

                if "list_total_count" in item:

                    total_count = int(
                        item["list_total_count"]
                    )

                    break


        # ----------------------------------
        # 현재 페이지 데이터
        # ----------------------------------

        if len(data["mealServiceDietInfo"]) < 2:
            break


        rows = data["mealServiceDietInfo"][1].get(
            "row",
            []
        )


        if not rows:
            break


        all_rows.extend(rows)


        # ----------------------------------
        # 전체 데이터를 다 받은 경우
        # ----------------------------------

        if total_count is not None:

            if len(all_rows) >= total_count:
                break


        # ----------------------------------
        # 다음 페이지
        # ----------------------------------

        page += 1


        # 안전장치
        if page > 100:
            break


    return all_rows


# ==========================================
# 데이터 가져오기
# ==========================================

with st.spinner(
    "2025년 9월부터 2026년 9월까지 급식 데이터를 가져오는 중..."
):

    try:

        meal_rows = get_all_meals()

    except requests.RequestException:

        st.error(
            "나이스 급식 API에 연결하지 못했습니다."
        )

        st.stop()

    except (ValueError, KeyError):

        st.error(
            "급식 데이터를 읽는 중 문제가 발생했습니다."
        )

        st.stop()


# ==========================================
# 데이터가 없는 경우
# ==========================================

if not meal_rows:

    st.info(
        "해당 기간에 등록된 중식 급식 데이터가 없습니다."
    )

    st.stop()


# ==========================================
# 날짜별 메뉴 집계
# ==========================================

daily_menus = {}


for row in meal_rows:

    meal_date = row.get(
        "MLSV_YMD",
        ""
    )

    raw_menu = row.get(
        "DDISH_NM",
        ""
    )


    if not meal_date or not raw_menu:
        continue


    # <br/> 기준으로 메뉴 분리
    raw_menus = raw_menu.split("<br/>")


    cleaned_menus = set()


    for menu in raw_menus:

        menu = clean_menu(menu)


        if menu:
            cleaned_menus.add(menu)


    # 같은 날 같은 메뉴가 여러 번 있어도
    # 하루에 한 번 나온 것으로 계산
    if meal_date not in daily_menus:

        daily_menus[meal_date] = set()


    daily_menus[meal_date].update(
        cleaned_menus
    )


# ==========================================
# 메뉴별 나온 날짜 수 계산
# ==========================================

menu_days = Counter()


for meal_date, menus in daily_menus.items():

    for menu in menus:

        menu_days[menu] += 1


# ==========================================
# 집계한 날짜 수
# ==========================================

total_days = len(daily_menus)


if total_days == 0:

    st.info(
        "집계할 급식 날짜가 없습니다."
    )

    st.stop()


# ==========================================
# 메뉴별 비율 계산
# ==========================================

menu_data = []


for menu, days in menu_days.items():

    ratio = (
        days / total_days * 100
    )

    menu_data.append(
        {
            "menu": menu,
            "days": days,
            "ratio": ratio
        }
    )


# 많이 나온 순서
menu_data.sort(
    key=lambda x: x["days"],
    reverse=True
)


# ==========================================
# TOP 10
# ==========================================

top_10 = menu_data[:10]


# ==========================================
# 상단 큰 숫자 카드
# ==========================================

st.divider()

card1, card2, card3 = st.columns(3)


with card1:

    st.metric(
        label="📅 집계한 날수",
        value=f"{total_days}일"
    )


with card2:

    st.metric(
        label="🥇 1위 메뉴",
        value=top_10[0]["menu"]
        if top_10
        else "-"
    )


with card3:

    st.metric(
        label="📈 1위 메뉴 비율",
        value=(
            f"{top_10[0]['ratio']:.1f}%"
            if top_10
            else "-"
        )
    )


# ==========================================
# 몇 위까지 볼지 선택
# ==========================================

st.divider()

rank_count = st.slider(
    "📊 몇 위까지 볼까요?",
    min_value=1,
    max_value=10,
    value=10
)


selected_data = top_10[:rank_count]


# ==========================================
# 막대그래프
# ==========================================

st.subheader(
    f"🍴 가장 자주 나온 메뉴 TOP {rank_count}"
)


# ------------------------------------------
# Plotly 없이 Streamlit 기본 차트 사용
# ------------------------------------------
# 1위가 맨 위에 오도록 역순으로 표시

chart_data = {
    item["menu"]: item["days"]
    for item in reversed(selected_data)
}


st.bar_chart(
    chart_data,
    horizontal=True,
    color="#ff8c42"
)


# ==========================================
# 색상이 진해지는 막대그래프
# ==========================================

st.caption(
    "※ 메뉴가 많이 나온 순서이며, 1위가 가장 위에 표시됩니다."
)


# ==========================================
# 메뉴별 상세 정보
# ==========================================

st.subheader("📋 메뉴별 상세 정보")


for index, item in enumerate(
    selected_data,
    start=1
):

    menu = item["menu"]
    days = item["days"]
    ratio = item["ratio"]


    # 순위별 색상
    if index == 1:
        color = "#d94841"

    elif index <= 3:
        color = "#f0784b"

    elif index <= 5:
        color = "#f59e5b"

    else:
        color = "#f7b267"


    st.markdown(
        f"""
        <div style="
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 10px;
            background-color: #ffffff;
        ">

            <div style="
                display: flex;
                align-items: center;
                gap: 15px;
            ">

                <div style="
                    background-color: {color};
                    color: white;
                    border-radius: 50%;
                    width: 36px;
                    height: 36px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                ">
                    {index}
                </div>

                <div style="
                    flex: 1;
                    font-size: 18px;
                    font-weight: 600;
                ">
                    {menu}
                </div>

                <div style="
                    text-align: right;
                    color: #555555;
                ">
                    <b>{days}일</b>
                    &nbsp; · &nbsp;
                    {ratio:.1f}%
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================
# 분석 설명
# ==========================================

st.divider()

st.markdown(
    """
    ### 📊 데이터 해석

    이 페이지에서는 **2025년 9월부터 2026년 9월까지의 송탄고등학교 중식**을
    날짜별로 확인한 뒤, 각 메뉴가 **며칠 동안 등장했는지**를 계산했습니다.

    같은 날 같은 메뉴가 여러 번 기록되어 있어도 그 날짜에는
    **1번 나온 것으로만 계산**했습니다.

    메뉴의 비율은 다음과 같이 계산합니다.

    **메뉴가 나온 날짜 수 ÷ 전체 급식이 집계된 날짜 수 × 100**
    """
)


st.caption(
    "※ 데이터 출처: 나이스 교육정보 개방 포털 급식식단정보 API"
)
