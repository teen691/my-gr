# ==========================================
# 날짜 + 알레르기 스위치
# ==========================================

date_col, allergy_col = st.columns(2)

with date_col:
    selected_date = st.date_input(
        "📅 날짜",
        value=today
    )

with allergy_col:
    show_allergy = st.toggle(
        "알레르기 정보 보기",
        value=True
    )


# ==========================================
# 선택한 날짜의 급식 조회
# ==========================================

meal = get_meal(selected_date)


# ==========================================
# 급식이 없는 경우
# ==========================================

if meal is None:
    st.info("🍽️ 급식이 없는 날입니다.")
    st.stop()


# ==========================================
# 메뉴 처리
# ==========================================

raw_menu = meal.get("DDISH_NM", "")

menus = split_menu(raw_menu)


# 알레르기 번호 표시 여부
if show_allergy:
    display_menus = menus
else:
    display_menus = [
        remove_allergy_number(menu)
        for menu in menus
    ]


# ==========================================
# 칼로리
# ==========================================

calorie = meal.get(
    "CAL_INFO",
    "정보 없음"
)


# ==========================================
# 선택한 날짜 표시
# ==========================================

st.divider()

st.subheader(
    f"🍚 {selected_date.strftime('%Y년 %m월 %d일')} 송탄고등학교 중식"
)


# ==========================================
# 메뉴 가짓수 + 칼로리 큰 숫자 카드
# ==========================================

menu_count_col, calorie_col = st.columns(2)

with menu_count_col:

    st.metric(
        label="🍴 메뉴 가짓수",
        value=f"{len(display_menus)}개"
    )


with calorie_col:

    st.metric(
        label="🔥 오늘의 칼로리",
        value=calorie
    )


# ==========================================
# 메뉴 카드
# ==========================================

st.markdown("### 🍴 오늘의 메뉴")


# 한 줄에 4개의 카드
CARDS_PER_ROW = 4


for i in range(
    0,
    len(display_menus),
    CARDS_PER_ROW
):

    row_menus = display_menus[
        i:i + CARDS_PER_ROW
    ]

    columns = st.columns(CARDS_PER_ROW)

    for column, menu in zip(
        columns,
        row_menus
    ):

        with column:

            st.markdown(
                f"""
                <div style="
                    background-color: #ffffff;
                    border: 1px solid #e1e5e9;
                    border-radius: 16px;
                    padding: 24px 12px;
                    margin-bottom: 16px;
                    min-height: 90px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
                ">
                    <div style="
                        font-size: 17px;
                        font-weight: 600;
                        text-align: center;
                        color: #222222;
                        line-height: 1.5;
                    ">
                        {menu}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ==========================================
# 알레르기 안내
# ==========================================

st.divider()

if show_allergy:

    st.caption(
        "※ 메뉴 이름 뒤 괄호 안의 숫자는 "
        "알레르기 유발 식품 번호입니다."
    )

else:

    st.caption(
        "※ 알레르기 정보 보기를 끄면 "
        "메뉴 뒤의 알레르기 번호가 표시되지 않습니다."
    )
