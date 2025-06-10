import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import datetime
import numpy as np

# --- 앱 설정 (가장 먼저 위치해야 함) ---
st.set_page_config(layout="wide", page_title="AI 투자 도우미")

# --- 캐싱 함수 정의 (st.cache_data 사용) ---
@st.cache_data(ttl=3600) # 1시간마다 캐시 갱신
def get_stock_data(ticker, period="1y"):
    """
    yfinance를 사용하여 주식/ETF 데이터를 가져오는 함수.
    'Adj Close' 데이터가 없을 경우 'Close' 데이터를 사용하고,
    데이터가 없으면 안전하게 빈 Series를 반환하여 호출 측에서 처리하도록 함.
    """
    try:
        data = yf.download(ticker, period="1d", progress=False)

        if data.empty:
            return pd.Series(dtype='float64') # 빈 Series 반환

        if 'Adj Close' in data.columns and not data['Adj Close'].empty:
            return data['Adj Close']
        elif 'Close' in data.columns and not data['Close'].empty:
            return data['Close']
        else:
            return pd.Series(dtype='float64') # 유효한 컬럼이 없으면 빈 Series 반환

    except Exception as e:
        return pd.Series(dtype='float64')

# --- 앱 본문 시작 ---

# '투자위험고지'는 자신의 투자 성향을 선택하는 것보다 위에 위치
st.markdown("---")
st.markdown("### ⚠️ 중요: 투자 위험 고지")
st.warning(
    "**본 앱에서 제공하는 정보는 투자 참고용이며, 어떠한 투자 권유도 아닙니다.**\n"
    "투자는 원금 손실의 위험을 내포하고 있으며, 과거 수익률이 미래 수익률을 보장하지 않습니다.\n"
    "제공된 정보는 시장 상황, 데이터 출처, 계산 로직에 따라 실제와 다를 수 있습니다.\n"
    "**투자 결정은 반드시 본인의 판단과 책임 하에 이루어져야 합니다.**\n"
    "전문가와 상담하여 신중하게 투자하시기를 강력히 권고합니다."
)

st.title("💰 AI 투자 도우미: 맞춤형 자산 포트폴리오 구성")

# 1. 투자 성향 슬라이더
st.markdown("### 📊 나의 투자 성향 선택")
st.markdown("0은 **가장 안정적인 투자**를 선호하며, 100은 **가장 공격적인 투자**를 선호합니다.")
risk_tolerance = st.slider("나의 투자 성향", 0, 100, 50)
st.info(f"현재 선택하신 투자 성향은 **{risk_tolerance}** 입니다.")

# 6. 포트폴리오 구성 자산 선택
st.markdown("---")
st.markdown("### 📝 포트폴리오에 포함할 자산 선택")
st.markdown("자신이 관심 있는 자산군을 선택해주세요. 선택하신 성향에 맞춰 자산 비중을 추천해 드립니다.")
selected_assets = st.multiselect(
    "선택 가능한 자산",
    ["금", "채권", "CMA/파킹통장 (현금)", "적금", "ETF", "주식", "원자재"],
    default=["금", "채권", "CMA/파킹통장 (현금)", "ETF"] # 초기 선택 값
)

if not selected_assets:
    st.warning("포트폴리오에 포함할 자산을 1개 이상 선택해주세요.")
else:
    # 2. 포트폴리오 구성 로직 (예시)
    portfolio = {}

    # 기본 비율 설정 (리스크 성향 50 기준)
    base_allocations = {
        "CMA/파킹통장 (현금)": 15,
        "채권": 30,
        "금": 10,
        "적금": 15,
        "ETF": 20,
        "주식": 5,
        "원자재": 5
    }

    # 리스크 성향에 따른 비율 조정 (간단한 선형 모델)
    for asset in selected_assets:
        if asset in base_allocations:
            base_percent = base_allocations[asset]
            # 안정 자산 (현금, 채권, 적금)은 리스크 성향이 낮을수록 비중 증가
            if asset in ["CMA/파킹통장 (현금)", "채권", "적금"]:
                portfolio[asset] = base_percent + (50 - risk_tolerance) * 0.4
            # 공격 자산 (주식, ETF, 원자재)은 리스크 성향이 높을수록 비중 증가
            elif asset in ["ETF", "주식", "원자재"]:
                portfolio[asset] = base_percent + (risk_tolerance - 50) * 0.4
            # 금은 비교적 중립적으로 유지 (변동성 자산으로 분류 시 공격 성향에 추가 가능)
            else: # 금
                portfolio[asset] = base_percent

    # 선택되지 않은 자산은 0으로 설정
    all_possible_assets = ["금", "채권", "CMA/파킹통장 (현금)", "적금", "ETF", "주식", "원자재"]
    for asset_name in all_possible_assets:
        if asset_name not in selected_assets:
            portfolio[asset_name] = 0
        elif asset_name not in portfolio: # 선택했지만 base_allocations에 없는 경우 (안전장치)
            portfolio[asset_name] = 0

    # 비율 정규화 (총합 100%)
    total_percentage = sum(portfolio.values())
    if total_percentage > 0:
        for asset, percentage in portfolio.items():
            if percentage < 0: # 음수 비율 방지
                portfolio[asset] = 0
            portfolio[asset] = (portfolio[asset] / total_percentage) * 100
    else:
        st.warning("선택된 자산으로 포트폴리오를 구성할 수 없습니다. 다른 자산을 선택해보세요.")
        portfolio = {asset: 0 for asset in selected_assets} # 빈 포트폴리오로 설정하여 오류 방지

    st.markdown("---")
    st.markdown("### 📊 추천 자산 포트폴리오 비율")
    st.write("선택하신 투자 성향과 자산 선택에 따라 추천되는 포트폴리오 구성 비율입니다.")

    if portfolio and sum(portfolio.values()) > 0:
        df_portfolio = pd.DataFrame(portfolio.items(), columns=['자산', '비율'])
        # 0%인 항목 제거하여 그래프에 표시 안함
        df_portfolio = df_portfolio[df_portfolio['비율'] > 0.01] # 0.01% 미만은 표시 안함

        if not df_portfolio.empty:
            fig = px.pie(df_portfolio, values='비율', names='자산',
                         title='<b>나의 맞춤형 자산 포트폴리오 구성</b>',
                         hole=0.4 # 도넛 차트
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("선택된 자산 비중이 너무 작아 차트를 그릴 수 없습니다. 다른 자산을 선택해주세요.")

        # 4. 각 자산별 추천 종목 또는 ETF
        st.markdown("---")
        st.markdown("### 📈 추천 종목 및 ETF")
        st.markdown("선택하신 자산별로 추천하는 종목 또는 ETF입니다. 현재 가격은 `yfinance`를 통해 조회됩니다. 실제 투자는 신중하게 결정해주세요.")

        asset_recommendations = {
            "금": {
                "종목": {
                    "SPDR Gold Shares (GLD)": "GLD", # 미국 금 ETF
                    "iShares Gold Trust (IAU)": "IAU", # 미국 금 ETF
                    "KODEX 골드선물(H)": "132030.KS", # 국내 금 ETF
                    "KRX 금 시장": "N/A" # KRX 금 시장은 티커 없음
                },
                "설명": "금은 인플레이션 헤지 및 안전자산으로 선호됩니다. 달러 가치와 반대로 움직이는 경향이 있습니다. **KRX 금 시장**을 통해 실물 금에 투자하거나, **금 ETF**를 통해 간접 투자할 수 있습니다."
            },
            "채권": {
                "설명": "채권은 주식에 비해 안정적인 수익을 제공하며, 경기 침체 시 가치가 상승할 수 있습니다. 금리 변동에 민감합니다. 투자 성향에 따라 다양한 채권을 고려할 수 있습니다. **국고채**는 정부가 발행하여 안정성이 높고, **회사채**는 기업이 발행하여 수익률이 높지만 신용 위험이 있습니다. 만기에 따라 **단기채**, **중장기채**, **장기채**로 구분됩니다.",
                "세부종목": {
                    "단기채 (안정적, 낮은 수익률)": {
                        "설명": "만기가 짧아 금리 변동에 덜 민감하고 안정적입니다. 단기 자금 운용에 적합합니다.",
                        "종목": {"KOSEF 단기자금": "123530.KS", "KBSTAR 국고채30년액티브": "306200.KS"} # 예시로 국내 단기채 ETF 추가
                    },
                    "중장기채 (중간 위험, 중간 수익률)": {
                        "설명": "금리 변동에 어느 정도 영향을 받지만, 장기채보다는 변동성이 작습니다.",
                        "종목": {"KODEX 국고채3년": "114260.KS", "TIGER 국채10년": "148070.KS"}
                    },
                    "장기채 (공격적, 높은 변동성)": {
                        "설명": "만기가 길어 금리 변동에 매우 민감하여 변동성이 크지만, 금리 하락 시 높은 수익률을 기대할 수 있습니다. 포트폴리오 분산에 활용됩니다.",
                        "종목": {"iShares 20+ Year Treasury Bond ETF (TLT)": "TLT", "KODEX 미국채10년선물(H)": "308620.KS"}
                    }
                }
            },
            "CMA/파킹통장 (현금)": {
                "종목": {}, # 추천 종목 대신 링크 제공
                "설명": "단기 여유자금을 보관하며, 비교적 높은 금리의 이자를 매일 또는 매주 받을 수 있는 상품입니다. 비상 자금으로 활용하기 좋습니다. **가장 높은 금리를 비교하여 선택하는 것이 중요합니다.**"
            },
            "적금": {
                "종목": {}, # 추천 종목 대신 링크 제공
                "설명": "정해진 기간 동안 꾸준히 저축하며, 확정된 금리 수익을 얻을 수 있는 안전한 상품입니다. 목돈 마련에 유용합니다. **은행별 최고 금리를 비교하여 선택하는 것이 중요합니다.**"
            },
            "ETF": {
                "종목": {
                    "KODEX 미국S&P500TR": "379810.KS", # S&P 500
                    "TIGER 미국나스닥100": "133690.KS", # 나스닥 100
                    "KODEX 미국나스닥100TR": "395380.KS", # 나스닥 100
                    "SOL 미국배당다우존스": "446860.KS", # SCHD와 유사한 국내 ETF
                    "ACE 미국배당다우존스": "449170.KS" # SCHD와 유사한 국내 ETF
                },
                "설명": "다양한 자산에 분산 투자하는 펀드를 주식처럼 거래할 수 있습니다. 특정 지수, 산업, 국가에 투자하여 분산 효과를 누릴 수 있습니다. **미국 주요 지수(S&P 500, 나스닥 100) 추종 ETF와 배당 성장 ETF(SCHD 유사)는 장기 투자에 적합합니다.**"
            },
            "주식": {
                "종목": {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "네이버": "035420.KS", "카카오": "035720.KS"},
                "설명": "개별 기업의 성장에 직접 투자하여 높은 수익을 추구할 수 있으나, 변동성이 매우 큽니다. 기업 분석과 시장 상황에 대한 이해가 필수적입니다."
            },
            "원자재": {
                "종목": {
                    "United States Oil Fund (USO)": "USO", # 원유 ETF
                    "Invesco DB Commodity Index Index Tracking Fund (DBC)": "DBC", # 종합 원자재 ETF
                    "Aberdeen Standard Physical Platinum Shares ETF (PPLT)": "PPLT", # 백금 ETF
                    "KODEX 구리선물(H)": "226340.KS" # 국내 구리 ETF
                },
                "설명": "원유, 구리, 곡물, 귀금속 등 실물 자산에 투자합니다. 글로벌 경제 상황이나 공급망 이슈에 따라 가격 변동성이 큽니다. 포트폴리오의 분산 효과를 높이는 데 활용될 수 있습니다."
            }
        }

        # 각 자산별 추천 종목 상세 표시 및 ISA 팁 위치 조정
        for asset in selected_assets:
            if asset in asset_recommendations:
                st.markdown(f"#### ➡️ {asset}")
                st.write(f"**설명:** {asset_recommendations[asset]['설명']}")

                # '투자 팁: ISA 계좌 활용'을 ETF 섹션 바로 아래로 이동
                if asset == "ETF":
                    st.markdown("### 💡 투자 팁: ISA 계좌 활용")
                    st.info(
                        "주식, ETF 등 일부 금융 상품을 개인 계좌에서 구매하는 것보다 **ISA (Individual Savings Account) 계좌**를 통해 구매하는 것을 고려해보세요.\n"
                        "ISA 계좌는 일정 한도 내에서 **비과세 또는 저율 분리과세 혜택**을 받을 수 있어 절세에 유리합니다.\n"
                        "특히, **ETF**와 같은 상품은 ISA 계좌에서 매매차익에 대한 세금 혜택을 받을 수 있으니, 자세한 내용은 증권사에 문의하거나 관련 정보를 찾아보시길 권합니다.\n"
                        "**연금저축펀드**와 **IRP** 계좌도 노후 대비 및 세액공제 혜택이 있으니 함께 알아보시면 좋습니다."
                    )
                    st.markdown("---") # 팁과 종목 사이에 구분선 추가

                # 채권의 경우 세분화된 종목을 표시 (여기서는 현재가 조회를 위해 period="2d" 유지)
                if asset == "채권":
                    for bond_type, bond_info in asset_recommendations[asset]['세부종목'].items():
                        st.markdown(f"##### {bond_type}")
                        st.write(f"**설명:** {bond_info['설명']}")
                        st.write(f"**추천 종목/ETF:**")
                        if bond_info['종목']:
                            for name, ticker in bond_info['종목'].items():
                                col1, col2 = st.columns([0.5, 0.5])
                                col1.write(f"- **{name}**")
                                stock_data_series = get_stock_data(ticker, period="2d") # 여기서 현재가 조회는 유지
                                if not stock_data_series.empty and len(stock_data_series) >= 1 and pd.api.types.is_numeric_dtype(stock_data_series):
                                    current_price = stock_data_series.iloc[-1]
                                    if len(stock_data_series) > 1 and pd.api.types.is_numeric_dtype(stock_data_series.iloc[-2]):
                                        previous_price = stock_data_series.iloc[-2]
                                        daily_change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price != 0 else 0
                                        col2.metric("현재가", f"{current_price:,.2f}", f"{daily_change_percent:,.2f}%")
                                    else:
                                        col2.metric("현재가", f"{current_price:,.2f}")
                                else:
                                    col2.write("(현재가 정보 없음)") # 데이터가 없을 경우 표시
                        else:
                            st.write("- (추천 종목 없음)")
                # CMA/파킹통장 또는 적금은 링크로 대체
                elif asset == "CMA/파킹통장 (현금)":
                    st.markdown("---")
                    st.markdown("[CMA/파킹 통장 금리 비교](https://new-m.pay.naver.com/savings/list/cma)")
                    st.markdown("---")
                elif asset == "적금":
                    st.markdown("---")
                    st.markdown("[예적금 금리 비교](https://new-m.pay.naver.com/savings/list/saving)")
                    st.markdown("---")
                # 그 외 자산군은 기존 방식대로 종목 표시
                else:
                    recommended_tickers_info = asset_recommendations[asset]['종목']
                    if recommended_tickers_info:
                        st.write(f"**추천 종목/ETF:**")
                        for name, ticker in recommended_tickers_info.items():
                            if ticker != "N/A":
                                col1, col2 = st.columns([0.5, 0.5])
                                col1.write(f"- **{name}**")
                                stock_data_series = get_stock_data(ticker, period="2d") # 여기서 현재가 조회는 유지

                                if not stock_data_series.empty and len(stock_data_series) >= 1 and pd.api.types.is_numeric_dtype(stock_data_series):
                                    current_price = stock_data_series.iloc[-1]
                                    if len(stock_data_series) > 1 and pd.api.types.is_numeric_dtype(stock_data_series.iloc[-2]):
                                        previous_price = stock_data_series.iloc[-2]
                                        daily_change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price != 0 else 0
                                        col2.metric("현재가", f"{current_price:,.2f}", f"{daily_change_percent:,.2f}%")
                                    else:
                                        col2.metric("현재가", f"{current_price:,.2f}")
                                else:
                                    col2.write("(현재가 정보 없음)") # 데이터가 없을 경우 표시
                            else:
                                st.write(f"- {name}")
                st.markdown("---")

    # --- 월별 투자 금액 기반 포트폴리오 구성 ---
    st.markdown("### 💸 월별 투자 가이드")
    st.markdown("월별 투자 금액과 각 자산군 내 선택 종목 수에 따라 맞춤형 투자 금액을 제안해 드립니다.")

    # 1. 월 투자금액 선택
    # 월별 투자금액 옵션 확장: 10만원부터 300만원까지 10만원 단위로
    monthly_investment_options = list(range(100000, 3000001, 100000))
    monthly_investment = st.select_slider(
        "월 투자 금액 (10만원 단위)",
        options=monthly_investment_options,
        value=300000 # 기본값
    )
    st.write(f"선택하신 월 투자 금액은 **{monthly_investment:,.0f}원** 입니다.")

    st.markdown("---")
    st.markdown("### 📌 자산군별 종목 선택")
    st.write("각 자산군에서 투자하고 싶은 종목들을 직접 선택해주세요.")

    selected_portfolio_items = {} # 최종 선택된 종목과 티커를 저장할 딕셔너리 (이름: 티커)
    # 채권의 세부 종목별 선택을 저장할 딕셔너리 추가
    selected_bond_types = {}

    # 각 자산군별로 종목을 선택하도록 UI 구성
    for asset_type in selected_assets:
        if asset_type in ["CMA/파킹통장 (현금)", "적금"]:
            # CMA/파킹통장, 적금은 종목 선택 없이 금액 배분으로 처리
            continue

        st.markdown(f"#### {asset_type} 종목 선택")

        # --- 채권 특별 처리: 단기채, 중장기채, 장기채 중에서 선택 ---
        if asset_type == "채권":
            bond_type_options = list(asset_recommendations["채권"]["세부종목"].keys())
            
            # 여기서 슬라이더로 몇 개의 '채권 유형'에 투자할지 선택하도록 함
            max_bond_choices = min(len(bond_type_options), 3) # 최대 3가지 유형
            num_bond_choices = st.slider(
                f"{asset_type}에서 몇 가지 채권 유형에 투자하시겠어요?",
                min_value=1,
                max_value=max_bond_choices,
                value=min(max_bond_choices, 2), # 기본 2가지 유형 선택
                key=f"num_choices_{asset_type}_bond_type"
            )

            chosen_bond_types_names = []
            for i in range(num_bond_choices):
                available_bond_options = [opt for opt in bond_type_options if opt not in chosen_bond_types_names]
                if not available_bond_options:
                    break

                selected_bond_type_name = st.selectbox(
                    f"{asset_type} 유형 {i+1} 선택",
                    ["선택하세요"] + available_bond_options,
                    key=f"{asset_type}_type_{i}"
                )
                if selected_bond_type_name != "선택하세요":
                    chosen_bond_types_names.append(selected_bond_type_name)
                    # 여기서는 실제 티커 대신 '채권 유형' 자체를 저장
                    selected_bond_types[selected_bond_type_name] = selected_bond_type_name 
            
            if not chosen_bond_types_names and num_bond_choices > 0:
                st.warning(f"{asset_type}에서 선택된 채권 유형이 없습니다. 다시 선택해주세요.")
            
            continue # 채권은 여기서 처리 완료, 다음 자산군으로 넘어감
        # --- 채권 특별 처리 끝 ---

        # 기타 자산군 (주식, ETF, 금, 원자재)의 기존 종목 선택 로직
        current_asset_options = {} # {이름: 티커}
        if asset_type in asset_recommendations:
            current_asset_options = asset_recommendations[asset_type]['종목']
            current_asset_options = {name: ticker for name, ticker in current_asset_options.items() if ticker != "N/A"}
        
        if not current_asset_options:
            st.info(f"선택 가능한 {asset_type} 종목이 없습니다.")
            continue

        max_choices = min(len(current_asset_options), 5) # 최대 5개 또는 종목 수만큼
        num_choices = st.slider(
            f"{asset_type}에서 몇 개의 종목에 투자하시겠어요?",
            min_value=1,
            max_value=max_choices,
            value=min(max_choices, 3) if asset_type == "ETF" else min(max_choices, 1),
            key=f"num_choices_{asset_type}"
        )

        chosen_names_for_asset = []
        for i in range(num_choices):
            available_options = list(current_asset_options.keys())
            
            for prev_choice_name in chosen_names_for_asset:
                if prev_choice_name in available_options:
                    available_options.remove(prev_choice_name)

            if not available_options:
                break

            selected_name = st.selectbox(
                f"{asset_type} 종목 {i+1} 선택",
                ["선택하세요"] + available_options,
                key=f"{asset_type}_item_{i}"
            )
            if selected_name != "선택하세요":
                chosen_names_for_asset.append(selected_name)
                selected_portfolio_items[selected_name] = current_asset_options[selected_name]

        if not chosen_names_for_asset and num_choices > 0:
            st.warning(f"{asset_type}에서 선택된 종목이 없습니다. 다시 선택해주세요.")

    st.markdown("---")
    st.markdown("### 💰 월별 추천 투자 금액")

    if st.button("포트폴리오 구성 제안 받기"):
        # 채권 유형이 선택되지 않았지만 채권 자산군이 선택된 경우 경고 추가
        if "채권" in selected_assets and not selected_bond_types:
            st.warning("채권 자산군을 선택하셨지만, 채권 유형을 선택하지 않으셨습니다. 다시 선택해주세요.")
            st.stop() # 여기서 실행을 중단하여 불필요한 계산 방지

        if not selected_portfolio_items and not any(asset in ["CMA/파킹통장 (현금)", "적금"] for asset in selected_assets) and not selected_bond_types:
            st.warning("월별 투자 가이드를 받으려면 최소 한 개 이상의 자산군에서 종목을 선택하거나, 현금/적금을 선택해주세요.")
        else:
            st.subheader("💡 당신의 월별 투자 플랜")
            
            # 주식, ETF, 금, 원자재 종목들의 현재가를 미리 가져옵니다.
            all_selected_tickers = {v for k, v in selected_portfolio_items.items()}
            current_prices_cache = {}
            for ticker in all_selected_tickers:
                price_series = get_stock_data(ticker, period="1d")
                if not price_series.empty:
                    current_prices_cache[ticker] = price_series.iloc[-1]
                else:
                    current_prices_cache[ticker] = None

            total_invested_amount = 0

            # 4. 처음에 나타내준 원그래프 비중에 따라서 각 자산군별 투자 금액 계산
            st.markdown(f"#### 총 월 투자 금액: **{monthly_investment:,.0f}원**")
            st.markdown("---")

            for asset, percentage in portfolio.items():
                if percentage > 0.01:
                    asset_amount = monthly_investment * (percentage / 100)
                    total_invested_amount += asset_amount
                    st.markdown(f"##### {asset}: **{asset_amount:,.0f}원** ({percentage:.1f}%)")

                    if asset in ["CMA/파킹통장 (현금)", "적금"]:
                        st.write(f"- `{asset_amount:,.0f}원`을 {asset}에 예치하는 것을 추천합니다. (위의 비교 링크를 활용하세요.)")
                    elif asset == "채권":
                        if selected_bond_types:
                            st.write(f"**추천 채권 유형별 구매 금액:**")
                            # 채권 유형별 비중 배분 로직 (투자 성향 반영)
                            bond_type_allocations = {}
                            num_selected_bond_types = len(selected_bond_types)
                            
                            # 투자 성향에 따른 채권 유형별 비중 조정
                            # 안정성(0)이 높을수록 단기채 비중 높고, 공격성(100)이 높을수록 장기채 비중 높음
                            # 중간(50)일 때 균등 배분
                            if num_selected_bond_types > 0:
                                # 단기채, 중장기채, 장기채의 가중치 초기화
                                short_term_weight = 1
                                mid_long_term_weight = 1
                                long_term_weight = 1

                                # 리스크 성향에 따른 가중치 조정
                                if risk_tolerance < 50: # 안정성 선호
                                    short_term_weight += (50 - risk_tolerance) * 0.04 # 0 -> 1+2 = 3
                                    long_term_weight -= (50 - risk_tolerance) * 0.04 # 0 -> 1-2 = -1 (최소 0.1으로)
                                elif risk_tolerance > 50: # 공격성 선호
                                    long_term_weight += (risk_tolerance - 50) * 0.04 # 100 -> 1+2 = 3
                                    short_term_weight -= (risk_tolerance - 50) * 0.04 # 100 -> 1-2 = -1 (최소 0.1으로)
                                
                                # 가중치 음수 방지 및 최소값 설정
                                short_term_weight = max(0.1, short_term_weight)
                                mid_long_term_weight = max(0.1, mid_long_term_weight) # 중장기채는 비교적 중립 유지
                                long_term_weight = max(0.1, long_term_weight)

                                total_weight = 0
                                if "단기채 (안정적, 낮은 수익률)" in selected_bond_types:
                                    bond_type_allocations["단기채 (안정적, 낮은 수익률)"] = short_term_weight
                                    total_weight += short_term_weight
                                if "중장기채 (중간 위험, 중간 수익률)" in selected_bond_types:
                                    bond_type_allocations["중장기채 (중간 위험, 중간 수익률)"] = mid_long_term_weight
                                    total_weight += mid_long_term_weight
                                if "장기채 (공격적, 높은 변동성)" in selected_bond_types:
                                    bond_type_allocations["장기채 (공격적, 높은 변동성)"] = long_term_weight
                                    total_weight += long_term_weight

                                if total_weight > 0:
                                    for bond_type_name, weight in bond_type_allocations.items():
                                        recommended_bond_amount = asset_amount * (weight / total_weight)
                                        st.write(f"- **{bond_type_name}**: 약 **{recommended_bond_amount:,.0f}원** 투자")
                                else:
                                    st.write("- 선택하신 채권 유형에 대한 비중을 설정할 수 없습니다.")
                            else:
                                st.write("- 채권 유형을 선택하지 않으셨습니다.")
                        else:
                            st.write("- 선택하신 채권 유형이 없습니다.")

                    else: # 주식, ETF, 금, 원자재
                        actual_selected_tickers_for_asset = {}
                        if asset in asset_recommendations:
                            for rec_name, rec_ticker in asset_recommendations[asset]['종목'].items():
                                if rec_name in selected_portfolio_items and selected_portfolio_items[rec_name] == rec_ticker:
                                    actual_selected_tickers_for_asset[rec_name] = rec_ticker

                        if actual_selected_tickers_for_asset:
                            st.write(f"**추천 종목별 구매 금액:**")
                            
                            valid_items_with_prices = {
                                name: current_prices_cache[ticker]
                                for name, ticker in actual_selected_tickers_for_asset.items()
                                if current_prices_cache.get(ticker) is not None
                            }

                            if valid_items_with_prices:
                                num_valid_items = len(valid_items_with_prices)
                                if num_valid_items > 0:
                                    amount_per_valid_item = asset_amount / num_valid_items
                                    remaining_amount_for_asset = asset_amount
                                    
                                    for name, price in valid_items_with_prices.items():
                                        if isinstance(price, (int, float)):
                                            num_shares_raw = amount_per_valid_item / price
                                            num_shares_scalar = np.floor(num_shares_raw).item()

                                            if num_shares_scalar > 0:
                                                purchase_amount = num_shares_scalar * price
                                                st.write(f"- **{name}**: 약 **{float(purchase_amount):,.0f}원** ({int(num_shares_scalar)}주/개 구매 가능)")
                                                remaining_amount_for_asset -= purchase_amount
                                            else:
                                                st.write(f"- **{name}**: **{float(price):,.0f}원** (1주/개 구매 금액) - 현재 배분 금액으로는 1주/개 구매 어려움.")
                                        else:
                                            st.write(f"- **{name}**: 가격 정보를 가져올 수 없습니다. ({asset_amount:,.0f}원 배분 예정)")
                                            
                                    if remaining_amount_for_asset > 0.01:
                                        st.write(f"*{asset}군 내 남은 금액: {remaining_amount_for_asset:,.0f}원 (소수점 이하 또는 1주/개 미만으로 남을 수 있습니다.)*")
                                else:
                                    st.write(f"- {asset}군 내 선택하신 종목의 현재가 정보를 가져올 수 없습니다. (해당 자산군 내 투자 금액: {asset_amount:,.0f}원)")
                            else:
                                st.write(f"- {asset}군 내 선택하신 모든 종목의 현재가 정보를 가져올 수 없어 정확한 금액 산출이 어렵습니다. (해당 자산군 내 투자 금액: {asset_amount:,.0f}원)")
                        else:
                            st.write(f"- {asset}군 내 선택하신 종목이 없습니다. 다시 선택해주세요.")
                    st.markdown("---")
            st.success(f"**총 {total_invested_amount:,.0f}원**에 대한 포트폴리오 구성 제안이 완료되었습니다.")

st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 AI 투자 도우미")
