import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


# ==========================================
# 페이지 설정
# ==========================================

st.set_page_config(
    page_title="초등학교 중학교 고등학교 급식 평균 칼로리는 얼마나 차이날까?",
    page_icon="🍚",
    layout="centered"
)

st.title("🍚 초등학교 중학교 고등학교 급식 평균 칼로리는 얼마나 차이날까?")
st.write(
    "학교와 날짜를 선택하면 해당 학교의 중식 메뉴, 알레르기 정보와 칼로리를 확인할 수 있습니다."
)

st.divider()


# ==========================================
# 나이스 API 기본 주소
# ==========================================

SCHOOL_API = "https://open.neis.go.kr/hub/schoolInfo"
MEAL_API = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# ==========================================
# 한국 시간 기준 오늘 날짜
# ==========================================

KST = ZoneInfo("Asia/Seoul")
today = datetime.now(KST).date()


# ==========================================
# 학교 검색 함수
# ==========================================

def search_school(school_name):
    """학교 이름으로 나이스 학교기본정보 API를 검색한다."""

    params = {
        "Type": "json",
        "SCHUL_NM": school_name
    }

    try:
        response = requests.get(
            SCHOOL_API,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        # 검색 결과가 없는 경우
        if "schoolInfo" not in data:
            return []

        # 두 번째 상자에 학교 정보가 들어 있음
        if len(data["schoolInfo"]) < 2:
            return []

        rows = data["schoolInfo"][1].get("row", [])

        return rows

    except (requests.RequestException, ValueError, KeyError):
        return []


# ==========================================
# 학교 이름 줄임말 처리
# ==========================================

def search_school_with_expansion(school_name):
    """
    먼저 사용자가 입력한 이름 그대로 검색한다.
    검색 결과가 없으면
    여고 → 여자고등학교
    고 → 고등학교
    로 바꿔서 한 번 더 검색한다.
    """

    # 1. 원래 입력한 이름으로 검색
    schools = search_school(school_name)

    if schools:
        return schools

    # 2. 줄임말을 정식 명칭으로 변경
    expanded_name = school_name

    if "여고" in expanded_name:
        expanded_name = expanded_name.replace(
            "여고",
            "여자고등학교"
        )

    elif expanded_name.endswith("고"):
        expanded_name = expanded_name[:-1] + "고등학교"

    # 이름이 실제로 바뀌었을 때만 다시 검색
    if expanded_name != school_name:
        return search_school(expanded_name)

    return []


# ==========================================
# 급식 검색 함수
# ==========================================

def search_meal(school, selected_date):
    """선택한 학교의 특정 날짜 중식 정보를 검색한다."""

    date_string = selected_date.strftime("%Y%m%d")

    params = {
        "Type": "json",

        # 학교 정보 API에서 얻은 코드
        "ATPT_OFCDC_SC_CODE": school["ATPT_OFCDC_SC_CODE"],
        "SD_SCHUL_CODE": school["SD_SCHUL_CODE"],

        # 2 = 중식
        "MMEAL_SC_CODE": "2",

        # 조회 날짜
        "MLSV_FROM_YMD": date_string,
        "MLSV_TO_YMD": date_string,

        "pSize": "1000",
        "pIndex": "1"
    }

    try:
        response = requests.get(
            MEAL_API,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        # 급식 정보 자체가 없는 경우
        if "mealServiceDietInfo" not in data:
            return None

        if len(data["mealServiceDietInfo"]) < 2:
            return None

        rows = data["mealServiceDietInfo"][1].get("row", [])

        if not rows:
            return None

        return rows[0]

    except (requests.RequestException, ValueError, KeyError):
        return None


# ==========================================
# 학교 이름 입력
# ==========================================

school_name = st.text_input(
    "🏫 학교 이름을 입력하세요.",
    placeholder="예: 수도여고"
)


# ==========================================
# 학교 검색
# ==========================================

if school_name.strip():

    schools = search_school_with_expansion(
        school_name.strip()
    )

    if not schools:

        st.info(
            "입력한 학교를 찾지 못했습니다. "
            "학교 이름을 다시 확인해 주세요."
        )

    else:

        st.success(
            f"검색 결과 {len(schools)}개의 학교를 찾았습니다."
        )

        # --------------------------------------
        # 학교 선택 목록 만들기
        # --------------------------------------

        school_options = []

        for school in schools:

            school_display = (
                f"{school['SCHUL_NM']} "
                f"({school['LCTN_SC_NM']})"
            )

            school_options.append(school_display)

        selected_school_display = st.selectbox(
            "검색된 학교 중 하나를 선택하세요.",
            school_options
        )

        # 선택된 학교의 실제 데이터 찾기
        selected_index = school_options.index(
            selected_school_display
        )

        selected_school = schools[selected_index]

        st.write(
            f"**선택한 학교:** "
            f"{selected_school['SCHUL_NM']}"
        )

        st.write(
            f"**지역:** "
            f"{selected_school['LCTN_SC_NM']}"
        )


        # ======================================
        # 날짜 선택
        # ======================================

        selected_date = st.date_input(
            "📅 급식 날짜를 선택하세요.",
            value=today
        )


        # ======================================
        # 급식 조회 버튼
        # ======================================

        if st.button(
            "🍽️ 중식 급식 찾아보기",
            use_container_width=True
        ):

            meal = search_meal(
                selected_school,
                selected_date
            )


            # ==================================
            # 급식이 없는 경우
            # ==================================

            if meal is None:

                st.info(
                    f"{selected_date.strftime('%Y년 %m월 %d일')}에는 "
                    "등록된 중식 급식 정보가 없습니다."
                )


            # ==================================
            # 급식이 있는 경우
            # ==================================

            else:

                st.divider()

                st.subheader(
                    f"🍚 {selected_date.strftime('%Y년 %m월 %d일')} 중식"
                )


                # ----------------------------------
                # 메뉴
                # ----------------------------------

                menu = meal.get(
                    "DDISH_NM",
                    "메뉴 정보가 없습니다."
                )

                # 나이스 API의 <br/>을 실제 줄바꿈으로 변경
                menu = menu.replace("<br/>", "\n")
                menu = menu.replace("<br>", "\n")

                st.markdown("### 🍴 메뉴")

                # 원래 메뉴와 알레르기 번호 그대로 표시
                st.text(menu)


                # ----------------------------------
                # 칼로리
                # ----------------------------------

                calorie = meal.get(
                    "CAL_INFO",
                    "칼로리 정보가 없습니다."
                )

                st.markdown("### 🔥 칼로리")

                st.info(calorie)


                # ----------------------------------
                # 설명
                # ----------------------------------

                st.caption(
                    "※ 메뉴 뒤 괄호 안의 숫자는 알레르기 유발 식품 번호입니다."
                )

                st.caption(
                    "※ 급식 정보는 나이스 교육정보 개방 포털의 "
                    "급식식단정보 API를 이용합니다."
                )


# ==========================================
# 사용 안내
# ==========================================

else:

    st.info(
        "위의 입력창에 학교 이름을 입력하면 급식을 조회할 수 있습니다."
    )
