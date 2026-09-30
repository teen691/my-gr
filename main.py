import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


# ==========================================
# 페이지 설정
# ==========================================

st.set_page_config(
    page_title="학교 급식 찾아보기",
    page_icon="🍚",
    layout="centered"
)


# ==========================================
# 제목
# ==========================================

st.title("🍚 학교 급식 찾아보기")

st.markdown(
    """
    ### 📊 데이터과학 탐구 주제
    **초등학교·중학교·고등학교 급식 평균 칼로리는 얼마나 차이날까?**

    학교별 급식의 칼로리를 확인하고 비교해 보면서
    학교급에 따른 급식 칼로리의 차이를 알아봅니다.
    """
)

st.divider()


# ==========================================
# 나이스 API 주소
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

        if "schoolInfo" not in data:
            return []

        if len(data["schoolInfo"]) < 2:
            return []

        rows = data["schoolInfo"][1].get(
            "row",
            []
        )

        return rows

    except (
        requests.RequestException,
        ValueError,
        KeyError
    ):

        return []


# ==========================================
# 학교 이름 줄임말 처리
# ==========================================

def search_school_with_expansion(school_name):

    # --------------------------------------
    # 1. 원래 이름으로 검색
    # --------------------------------------

    schools = search_school(school_name)

    if schools:
        return schools


    # --------------------------------------
    # 2. 줄임말을 정식 명칭으로 변경
    # --------------------------------------

    expanded_name = school_name


    # "여고" → "여자고등학교"
    if "여고" in expanded_name:

        expanded_name = expanded_name.replace(
            "여고",
            "여자고등학교"
        )


    # "고"로 끝나는 경우
    elif expanded_name.endswith("고"):

        expanded_name = (
            expanded_name[:-1]
            + "고등학교"
        )


    # --------------------------------------
    # 3. 변경된 이름으로 다시 검색
    # --------------------------------------

    if expanded_name != school_name:

        return search_school(
            expanded_name
        )

    return []


# ==========================================
# 학교급 구분
# ==========================================

def get_school_level(school_name):

    if "초등학교" in school_name:
        return "초등학교"

    elif "중학교" in school_name:
        return "중학교"

    elif "고등학교" in school_name:
        return "고등학교"

    return "기타"


# ==========================================
# 급식 검색 함수
# ==========================================

def search_meal(
    school,
    selected_date
):

    date_string = selected_date.strftime(
        "%Y%m%d"
    )

    params = {

        "Type": "json",

        "ATPT_OFCDC_SC_CODE":
            school["ATPT_OFCDC_SC_CODE"],

        "SD_SCHUL_CODE":
            school["SD_SCHUL_CODE"],

        # 중식
        "MMEAL_SC_CODE": "2",

        "MLSV_FROM_YMD":
            date_string,

        "MLSV_TO_YMD":
            date_string,

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


        if "mealServiceDietInfo" not in data:
            return None


        if len(data["mealServiceDietInfo"]) < 2:
            return None


        rows = data["mealServiceDietInfo"][1].get(
            "row",
            []
        )


        if not rows:
            return None


        return rows[0]


    except (
        requests.RequestException,
        ValueError,
        KeyError
    ):

        return None


# ==========================================
# 학교 이름 입력
# ==========================================

school_name = st.text_input(
    "🏫 학교 이름을 입력하세요.",
    placeholder="예: 송탄고등학교"
)


# ==========================================
# 학교 검색
# ==========================================

if school_name.strip():

    schools = search_school_with_expansion(
        school_name.strip()
    )


    # ======================================
    # 학교 검색 실패
    # ======================================

    if not schools:

        st.info(
            "🔎 학교를 찾지 못했습니다. "
            "학교 이름을 다시 확인해 주세요."
        )


    # ======================================
    # 학교 검색 성공
    # ======================================

    else:

        st.success(
            f"총 {len(schools)}개의 학교를 찾았습니다."
        )


        # ----------------------------------
        # 학교 목록
        # ----------------------------------

        school_options = []


        for school in schools:

            school_options.append(
                f"{school['SCHUL_NM']} "
                f"({school['LCTN_SC_NM']})"
            )


        selected_school_display = st.selectbox(
            "🏫 학교를 선택하세요.",
            school_options
        )


        selected_index = school_options.index(
            selected_school_display
        )

        selected_school = schools[
            selected_index
        ]


        # ==================================
        # 선택한 학교 정보
        # ==================================

        school_level = get_school_level(
            selected_school["SCHUL_NM"]
        )


        info_col1, info_col2 = st.columns(2)


        with info_col1:

            st.metric(
                "학교급",
                school_level
            )


        with info_col2:

            st.metric(
                "지역",
                selected_school["LCTN_SC_NM"]
            )


        st.write(
            f"**선택한 학교:** "
            f"{selected_school['SCHUL_NM']}"
        )


        st.divider()


        # ==================================
        # 날짜 선택
        # ==================================

        selected_date = st.date_input(
            "📅 급식 날짜를 선택하세요.",
            value=today
        )


        # ==================================
        # 급식 조회 버튼
        # ==================================

        if st.button(
            "🍽️ 급식 확인하기",
            use_container_width=True
        ):

            meal = search_meal(
                selected_school,
                selected_date
            )


            # ==================================
            # 급식 없음
            # ==================================

            if meal is None:

                st.info(
                    f"{selected_date.strftime('%Y년 %m월 %d일')}에는 "
                    "등록된 중식 급식이 없습니다."
                )


            # ==================================
            # 급식 있음
            # ==================================

            else:

                st.divider()


                st.subheader(
                    f"🍚 {selected_date.strftime('%Y년 %m월 %d일')} 급식"
                )


                # ==================================
                # 칼로리
                # ==================================

                calorie = meal.get(
                    "CAL_INFO",
                    "정보 없음"
                )


                st.metric(
                    "🔥 중식 칼로리",
                    calorie
                )


                # ==================================
                # 메뉴
                # ==================================

                st.markdown("### 🍴 오늘의 메뉴")


                menu = meal.get(
                    "DDISH_NM",
                    "메뉴 정보가 없습니다."
                )


                # <br/> → 줄바꿈
                menu = menu.replace(
                    "<br/>",
                    "\n"
                )

                menu = menu.replace(
                    "<br>",
                    "\n"
                )


                st.text(menu)


                # ==================================
                # 데이터과학 탐구 안내
                # ==================================

                st.divider()

                st.markdown(
                    """
                    ### 📊 데이터과학 탐구에 활용하기

                    이 급식의 **칼로리 정보**를 여러 날짜와 여러 학교에서
                    수집하면 학교급별 평균을 계산할 수 있습니다.

                    예를 들어 다음과 같이 비교할 수 있습니다.

                    - 🟢 초등학교 평균 급식 칼로리
                    - 🔵 중학교 평균 급식 칼로리
                    - 🟠 고등학교 평균 급식 칼로리

                    이렇게 모은 데이터를 이용해
                    **학교급에 따라 급식 평균 칼로리가 얼마나 다른지**
                    그래프로 나타낼 수 있습니다.
                    """
                )


                st.caption(
                    "※ 메뉴 이름 뒤 괄호 안의 숫자는 "
                    "알레르기 유발 식품 번호입니다."
                )

                st.caption(
                    "※ 급식 정보는 나이스 교육정보 개방 포털 "
                    "급식식단정보 API를 이용합니다."
                )


# ==========================================
# 처음 화면
# ==========================================

else:

    st.info(
        "👆 학교 이름을 입력해서 급식을 찾아보세요."
    )


    st.markdown(
        """
        ### 🔍 이 앱에서 할 수 있는 것

        **① 학교 검색**  
        학교 이름을 입력하면 나이스 학교정보에서 학교를 찾습니다.

        **② 학교 선택**  
        같은 이름의 학교가 여러 곳이면 지역을 함께 보여 줍니다.

        **③ 날짜 선택**  
        달력에서 원하는 날짜를 선택합니다.

        **④ 급식 확인**  
        해당 날짜의 중식 메뉴와 칼로리를 확인합니다.

        **⑤ 데이터 비교**  
        여러 학교와 날짜의 칼로리를 모아
        초등학교·중학교·고등학교의 평균 칼로리를 비교할 수 있습니다.
        """
    )
