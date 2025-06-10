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
# 해당 일자의 일정 정보 및 이미지
# ---------------------------
day_by_day_schedule = {
    "1일차": {
        "오전": {
            "activity": "괌 공항 도착, 렌터카 수령 또는 셔틀 이용",
            "image": "https://upload.wikimedia.org/wikipedia/commons/e/e4/A.B._Won_Pat_International_Airport_Guam_terminal.jpg" # 유효한 링크로 가정
        },
        "점심": {
            "activity": "숙소 근처 로컬 식당 (예: Shirley's Coffee Shop)",
            "image": "https://media-cdn.tripadvisor.com/media/photo-s/0e/43/e7/31/shirley-s-coffee-shop.jpg" # 유효한 링크로 가정
        },
        "오후": {
            "activity": "🏖️ 타무닝 해변 산책 및 호텔 체크인",
            "image": "https://upload.wikimedia.org/wikipedia/commons/e/ed/Tumon_Bay_Guam_2016.jpg" # 유효한 링크로 가정
        },
        "저녁": {
            "activity": "Tony Roma's에서 립 스테이크 또는 해산물 디너",
            "image": "https://www.tonyromas.com/assets/images/menu-items/ribs/original-bbq-ribs.jpg" # 유효한 링크로 가정
        }
    },
    "2일차": {
        "오전": {
            "activity": "🏝️ 투몬 비치에서 해수욕 및 스노클링",
            "image": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Tumon_Beach_Guam.jpg" # 유효한 링크로 가정
        },
        "점심": {
            "activity": "Beachin' Shrimp 투몬점에서 쉬림프 타코",
            "image": "https://d1ralsognjng37.cloudfront.net/955375df-2d6f-40c2-9e90-c116c4c3b5b6.jpeg" # 유효한 링크로 가정
        },
        "오후": {
            "activity": "💑 사랑의 절벽 방문 및 전망 감상",
            "image": "https://upload.wikimedia.org/wikipedia/commons/c/cf/Two_Lovers_Point.jpg" # 유효한 링크로 가정
        },
        "저녁": {
            "activity": "Jamaican Grill에서 가족 BBQ 세트",
            "image": "https://media-cdn.tripadvisor.com/media/photo-s/0e/8c/5e/2c/jamaican-grill.jpg" # 유효한 링크로 가정
        }
    },
    "3일차": {
        "오전": {
            "activity": "🐬 돌핀 와칭 투어 (오전 9시 출발, 약 3시간)",
            "image": "https://i.ytimg.com/vi/aC8_3fJ8XwQ/maxresdefault.jpg" # 유효한 링크로 가정
        },
        "점심": {
            "activity": "피쉬아이 마린파크 레스토랑 뷔페",
            "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRz-4sX2q7X_1-g5gL5gQ3p-0l-1Q-7z-6_A&s" # 예시, 실제 이미지 아님
        },
        "오후": {
            "activity": "🐟 피쉬아이 수족관 및 해양 전망 타워 관람",
            "image": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Fish_Eye_Marine_Park_Piti_Guam.jpg" # 유효한 링크로 가정
        },
        "저녁": {
            "activity": "숙소 복귀 후 근처에서 간단한 식사",
            "image": "https://www.fodors.com/assets/media/2513903/guam-food-hero.jpg" # 유효한 링크로 가정
        }
    },
    "4일차": {
        "오전": {
            "activity": "🛍️ 괌 프리미엄 아울렛 쇼핑",
            "image": "https://upload.wikimedia.org/wikipedia/commons/9/91/Guam_Premier_Outlets.jpg" # 유효한 링크로 가정
        },
        "점심": {
            "activity": "Food Court 또는 Panda Express",
            "image": "https://media-cdn.tripadvisor.com/media/photo-s/0e/d9/d2/8c/food-court.jpg" # 유효한 링크로 가정
        },
        "오후": {
            "activity": "⛪ 아가나 대성당 관람 및 주변 거리 산책",
            "image": "https://upload.wikimedia.org/wikipedia/commons/2/22/Dulce_Nombre_de_Maria_Cathedral_Basilica_Guam.jpg" # 유효한 링크로 가정
        },
        "저녁": {
            "activity": "Caliente에서 멕시칸 음식 즐기기",
            "image": "https://media-cdn.tripadvisor.com/media/photo-s/0e/c4/b0/0f/caliente-guam.jpg" # 유효한 링크로 가정
        }
    },
    "5일차": {
        "오전": {
            "activity": "🏞️ 이나라한 자연풀장에서 수영 및 사진 촬영",
            "image": "https://upload.wikimedia.org/wikipedia/commons/1/18/Inarajan_Natural_Pools.jpg" # 유효한 링크로 가정
        },
        "점심": {
            "activity": "마을 근처 로컬식당에서 전통 음식",
            "image": "https://i.ytimg.com/vi/qQ8m_J0_r2w/maxresdefault.jpg" # 예시, 실제 음식 아님
        },
        "오후": {
            "activity": "자연 탐방 또는 원주민 마을 구경",
            "image": "https://upload.wikimedia.org/wikipedia/commons/d/d5/Chamorro_Village_Guam.jpg" # 유효한 링크로 가정
        },
        "저녁": {
            "activity": "숙소 디너 뷔페 또는 랍스터 요리",
            "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRz-4sX2q7X_1-g5gL5gQ3p-0l-1Q-7z-6_A&s" # 예시, 실제 이미지 아님
        }
    },
    "6일차": {
        "오전": {
            "activity": "호텔 수영장, 마사지 등 자유 일정",
            "image": "https://t-cf.bstatic.com/xdata/images/hotel/max1024x768/32570075.jpg?k=b4e3a4e9b9c0f9a2d0c2f8f7b7f7f7f7&o=&s" # 유효한 링크로 가정
        },
        "점심": {
            "activity": "숙소 내 레스토랑 또는 인근 까페",
            "image": "https://www.tripadvisor.com/Restaurant_Review-g60647-d15024148-Reviews-The_Beach_Bar_Grill_at_Dusit_Thani_Guam_Resort-Tamuning_Guam.html" # 예시, 실제 이미지 아님
        },
        "오후": {
            "activity": "🌅 석양 크루즈 탑승 (선택, 오후 5시~)",
            "image": "https://assets.traveltriangle.com/blog/wp-content/uploads/2019/02/Sunset-Dinner-Cruise-in-Guam.jpg" # 유효한 링크로 가정
        },
        "저녁": {
            "activity": "크루즈 내 해산물 뷔페 또는 야시장",
            "image": "https://upload.wikimedia.org/wikipedia/commons/0/07/Chamorro_Night_Market.jpg" # 유효한 링크로 가정
        }
    },
    "7일차": {
        "오전": {
            "activity": "호텔 체크아웃 및 공항 이동",
            "image": "https://upload.wikimedia.org/wikipedia/commons/e/e4/A.B._Won_Pat_International_Airport_Guam_terminal.jpg" # 유효한 링크로 가정
        },
        "점심": {
            "activity": "공항 내 간단한 샌드위치 또는 컵라면",
            "image": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Airport_food.jpg" # 유효한 링크로 가정
        },
        "오후": {
            "activity": "✈️ 귀국",
            "image": "https://upload.wikimedia.org/wikipedia/commons/9/91/Boeing_747-400_Korean_Air.jpg" # 유효한 링크로 가정
        }
    }
}

# Define clock emoji colors
CLOCK_EMOJIS = {
    "오전": "⏰", # Blue/Morning
    "점심": "🕛", # Green/Noon
    "오후": "🕞", # Orange/Afternoon
    "저녁": "🌙"  # Purple/Night
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

for time, details in schedule.items():
    emoji = CLOCK_EMOJIS.get(time, "⏰") # Get colored emoji
    st.markdown(f"### {emoji} {time}\n- {details['activity']}")
    if details['image']:
        st.image(details['image'], caption=details['activity'], use_container_width=True)
    st.markdown("---") # Add a separator

# 지도 표시 (해당 일자의 장소들)
if selected_day in day_by_day_locations:
    st.subheader("📍 방문 장소 지도")
    locs = day_by_day_locations[selected_day]
    coords = []
    
    # Check if there are locations for the selected day
    if locs:
        for name, coord in locs.items():
            coords.append(coord)
        
        # Calculate bounds for fitting the map
        if coords:
            min_lat = min(c[0] for c in coords)
            max_lat = max(c[0] for c in coords)
            min_lon = min(c[1] for c in coords)
            max_lon = max(c[1] for c in coords)

            # Initialize map with center of the bounds
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

            # Add markers with emojis
            for name, coord in locs.items():
                emoji = name.split(" ")[0] if name[0] in ['🏖️', '🏝️', '💑', '🐬', '🐟', '🛍️', '⛪', '🏞️', '✈️', '🌅'] else '📍' # Extract emoji or use default
                folium.Marker(
                    location=coord,
                    popup=name,
                    icon=folium.DivIcon(
                        html=f"""
                        <div style="font-size: 24px;">{emoji}</div>""",
                        class_name="custom-icon"
                    )
                ).add_to(m)

            # Add route if more than one location
            if len(coords) >= 2:
                PolyLine(locations=coords, color='blue', weight=5, opacity=0.7).add_to(m)
            
            # Fit bounds to the map if there are multiple locations
            if len(coords) > 1:
                m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
            
            st_folium(m, width=700, height=500)
    else:
        st.info("해당 날짜에는 특별한 장소 방문 계획이 없습니다.")
else:
    st.info("해당 날짜에는 특별한 장소 방문 계획이 없습니다.")
