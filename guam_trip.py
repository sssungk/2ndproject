import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
from folium import PolyLine

# ---------------------------
# 테스트용 위치 데이터
# ---------------------------
day_by_day_locations = {
    "1일차": {
        "🏖️ 타무닝 해변": [13.4961, 144.7782]
    },
    "2일차": {
        "🏝️ 투몬 비치": [13.5165, 144.8077],
        "💑 사랑의 절벽": [13.5270, 144.8071]
    },
    "3일차": {
        "🐬 돌핀 와칭 투어 출발지": [13.4584, 144.7223],
        "🐟 피쉬아이 마린 파크": [13.4651, 144.7068]
    },
    "4일차": {
        "🛍️ 괌 프리미엄 아울렛": [13.4878, 144.7766],
        "⛪ 아가나 대성당": [13.4744, 144.7487]
    },
    "5일차": {
        "🏞️ 이나라한 자연풀장": [13.3148, 144.7602]
    },
    "6일차": {
        # 자유 일정
    },
    "7일차": {
        # 귀국일
    }
}

# ---------------------------
# 해당 일자의 \uuc77c정 정보
# ---------------------------
day_by_day_schedule = {
    "1일차": {
        "오전": "괌 공항 도착, 렌터카 수령 또는 셔틀 이용",
        "점심": "숙소 근처 로컬 식당 (예: Shirley's Coffee Shop)",
        "오후": "🏖️ 타무닝 해변 산책 및 호텔 체크인",
        "저녁": "Tony Roma's에서 립 스테이크 또는 해산물 디너"
    },
    "2일차": {
        "오전": "🏝️ 투몬 비치에서 해수욕 및 스노클링",
        "점심": "Beachin' Shrimp 투몬점에서 쉬림프 타코",
        "오후": "💑 사랑의 절벽 방문 및 전망 감상",
        "저녁": "Jamaican Grill에서 가족 BBQ 세트"
    },
    "3일차": {
        "오전": "🐬 돌핀 와칭 투어 (오전 9시 출발, 약 3시간)",
        "점심": "피쉬아이 마린파크 레스토랑 뷔페",
        "오후": "🐟 피쉬아이 수족관 및 해양 전망 타워 관람",
        "저녁": "숙소 복귀 후 근처에서 간단한 식사"
    },
    "4일차": {
        "오전": "🛍️ 괌 프리미엄 아울렛 쇼핑",
        "점심": "Food Court 또는 Panda Express",
        "오후": "⛪ 아가나 대성당 관람 및 주변 거리 산책",
        "저녁": "Caliente에서 멕시칸 음식 즐기기"
    },
    "5일차": {
        "오전": "🏞️ 이나라한 자연풀장에서 수영 및 사진 촬영",
        "점심": "마을 근처 로컬식당에서 전통 음식",
        "오후": "자연 탐방 또는 원주민 마을 구경",
        "저녁": "숙소 디너 뷔페 또는 랍스터 요리"
    },
    "6일차": {
        "오전": "호텔 수영장, 마사지 등 자유 일정",
        "점심": "숙소 내 레스토랑 또는 인근 까페",
        "오후": "🌅 석양 크루즈 탑승 (선택, 오후 5시~)",
        "저녁": "크루즈 내 해산물 뷔페 또는 야시장"
    },
    "7일차": {
        "오전": "호텔 체크아웃 및 공항 이동",
        "점심": "공항 내 간단한 샌드위치 또는 컵라면",
        "오후": "✈️ 귀국"
    }
}

# ---------------------------
# UI 시작
# ---------------------------
st.title("🌴 괌 6박 7일 가족여행 가이드")

# 날짜 입력
st.sidebar.header("📅 여행 날짜 선택")
def_date = datetime.date.today()
start_date = st.sidebar.date_input("여행 시작일", def_date)
end_date = st.sidebar.date_input("여행 종료일", start_date + datetime.timedelta(days=6))

if start_date > end_date:
    st.sidebar.error("시작일은 종료일보다 앞서야 합니다.")
    st.stop()

day_count = (end_date - start_date).days + 1
base_date = start_date

# 날짜별 버튼 생성
selected_day = st.selectbox("🔘 일차를 선택하세요", list(day_by_day_schedule.keys()))

# 선택된 날짜 정보 표시
selected_idx = int(selected_day.replace("일차", "")) - 1
current_date = base_date + datetime.timedelta(days=selected_idx)
day_of_week = current_date.strftime("(%A)")

st.header(f"🗓️ {selected_day} - {current_date.strftime('%Y-%m-%d')} {day_of_week}")
schedule = day_by_day_schedule[selected_day]

for time, activity in schedule.items():
    st.markdown(f"### ⏰ {time}\n- {activity}")

# 지도 표시 (해당 일자의 장소들)
if selected_day in day_by_day_locations:
    st.subheader("📍 방문 장소 지도")
    m = folium.Map(location=[13.5, 144.8], zoom_start=11)
    locs = day_by_day_locations[selected_day]
    coords = []
    for name, coord in locs.items():
        coords.append(coord)
        folium.Marker(location=coord, popup=name, icon=folium.Icon(color="green")).add_to(m)

    # 루트 표시 (선택 사항)
    if len(coords) >= 2:
        PolyLine(locations=coords, color='blue').add_to(m)

    st_folium(m, width=700, height=500)
else:
    st.info("해당 날짜에는 특별한 장소 방문 계획이 없습니다.")
