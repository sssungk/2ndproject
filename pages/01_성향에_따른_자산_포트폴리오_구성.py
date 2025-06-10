import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf # 실시간 데이터 연동을 위한 라이브러리

# yfinance 캐싱을 위한 설정 (API 호출 제한에 대비)
# @st.cache_data # Streamlit 1.10.0 이상에서는 st.cache_data 사용
# def get_stock_data(ticker, period="1y"):
#     try:
#         data = yf.download(ticker, period=period)
#         return data['Adj Close']
#     except Exception as e:
#         st.warning(f"'{ticker}' 종목 데이터를 불러오는 데 실패했습니다: {e}")
#         return pd.Series() # 빈 시리즈 반환

# Streamlit 1.10.0 미만 또는 안정성을 위해 st.cache 사용 (deprecated 예정)
@st.cache(ttl=3600) # 1시간마다 캐시 갱신
def get_stock_data(ticker, period="1y"):
    try:
        data = yf.download(ticker, period=period)
        return data['Adj Close']
    except Exception as e:
        st.warning(f"'{ticker}' 종목 데이터를 불러오는 데 실패했습니다: {e}")
        return pd.Series() # 빈 시리즈 반환

# --- 앱 시작 ---
st.set_page_config(layout="wide") # 넓은 레이아웃 설정
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
    # 이 부분은 투자 성향과 선택된 자산에 따라 비율을 동적으로 조절하는 핵심 로직입니다.
    # 실제로는 더 정교한 금융 모델이나 최적화 알고리즘이 필요합니다.
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
    for asset_name in ["금", "채권", "CMA/파킹통장 (현금)", "적금", "ETF", "주식", "원자재"]:
        if asset_name not in selected_assets:
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
                "종목": {"KODEX 골드선물(H)": "000000.KS"}, # 실제 Ticker 아님, 예시
                "설명": "금은 인플레이션 헤지 및 안전자산으로 선호됩니다. 달러 가치와 반대로 움직이는 경향이 있습니다. (ETF: KODEX 골드선물(H), ACE 골드선물블룸버그(H))"
            },
            "채권": {
                "종목": {"KODEX 국고채3년": "000000.KS", "TLT": "TLT"}, # TLT는 미국 장기채 ETF
                "설명": "채권은 주식에 비해 안정적인 수익을 제공하며, 경기 침체 시 가치가 상승할 수 있습니다. 금리 변동에 민감합니다. (ETF: KODEX 국고채3년, KBSTAR 국고채10년, 미국 장기채 ETF)"
            },
            "CMA/파킹통장 (현금)": {
                "종목": {"토스뱅크 파킹통장": "N/A"},
                "설명": "단기 여유자금을 보관하며, 비교적 높은 금리의 이자를 매일 또는 매주 받을 수 있는 상품입니다. 비상 자금으로 활용하기 좋습니다."
            },
            "적금": {
                "종목": {"각 은행의 정기적금 상품": "N/A"},
                "설명": "정해진 기간 동안 꾸준히 저축하며, 확정된 금리 수익을 얻을 수 있는 안전한 상품입니다. 목돈 마련에 유용합니다."
            },
            "ETF": {
                "종목": {"KODEX 200": "069500.KS", "TIGER 미국S&P500": "360750.KS", "QQQ": "QQQ"},
                "설명": "다양한 자산에 분산 투자하는 펀드를 주식처럼 거래할 수 있습니다. 특정 지수, 산업, 국가에 투자하여 분산 효과를 누릴 수 있습니다."
            },
            "주식": {
                "종목": {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "네이버": "035420.KS"},
                "설명": "개별 기업의 성장에 직접 투자하여 높은 수익을 추구할 수 있으나, 변동성이 매우 큽니다. 기업 분석과 시장 상황에 대한 이해가 필수적입니다."
            },
            "원자재": {
                "종목": {"KODEX WTI원유선물(H)": "000000.KS", "KODEX 은선물(H)": "000000.KS"}, # 실제 Ticker 아님, 예시
                "설명": "원유, 구리, 곡물 등 실물 자산에 투자합니다. 글로벌 경제 상황이나 공급망 이슈에 따라 가격 변동성이 큽니다."
            }
        }

        for asset in selected_assets:
            if asset in asset_recommendations:
                st.markdown(f"#### ➡️ {asset}")
                st.write(f"**설명:** {asset_recommendations[asset]['설명']}")
                
                recommended_tickers = asset_recommendations[asset]['종목']
                if recommended_tickers:
                    st.write(f"**추천 종목/ETF:**")
                    for name, ticker in recommended_tickers.items():
                        if ticker != "N/A":
                            col1, col2, col3 = st.columns([0.3, 0.2, 0.5])
                            col1.write(f"- **{name}**")
                            # 실시간 데이터 연동 (yfinance)
                            stock_data = get_stock_data(ticker, period="1d")
                            if not stock_data.empty:
                                current_price = stock_data.iloc[-1]
                                previous_price = stock_data.iloc[-2] if len(stock_data) > 1 else current_price
                                daily_change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price != 0 else 0

                                col2.metric("현재가", f"{current_price:,.2f}", f"{daily_change_percent:,.2f}%")
                                # col2.write(f"**현재가:** {current_price:,.2f}") # 이전 버전
                            else:
                                col2.write("데이터 없음")
                            col3.write(f"(`{ticker}`)")
                        else:
                            st.write(f"- {name}")
                st.markdown("---")

        # 5. ISA 계좌 관련 팁
        st.markdown("### 💡 투자 팁: ISA 계좌 활용")
        st.info(
            "주식, ETF 등 일부 금융 상품을 개인 계좌에서 구매하는 것보다 **ISA (Individual Savings Account) 계좌**를 통해 구매하는 것을 고려해보세요.\n"
            "ISA 계좌는 일정 한도 내에서 **비과세 또는 저율 분리과세 혜택**을 받을 수 있어 절세에 유리합니다.\n"
            "특히, **ETF**와 같은 상품은 ISA 계좌에서 매매차익에 대한 세금 혜택을 받을 수 있으니, 자세한 내용은 증권사에 문의하거나 관련 정보를 찾아보시길 권합니다.\n"
            "**연금저축펀드**와 **IRP** 계좌도 노후 대비 및 세액공제 혜택이 있으니 함께 알아보시면 좋습니다."
        )

        # 백테스팅 (간단한 예시)
        st.markdown("---")
        st.markdown("### 📈 백테스팅 시뮬레이션 (예시)")
        st.markdown("선택된 자산 비중에 따라 **과거 1년 동안**의 포트폴리오 수익률을 **매우 간략하게** 시뮬레이션 합니다. **실제 수익률과는 차이가 있을 수 있습니다.**")
        
        start_date = st.date_input("시작 날짜 (최근 1년)", pd.to_datetime('2024-06-01'))
        end_date = st.date_input("종료 날짜", pd.to_datetime('2025-06-01'))

        # 백테스팅 가능한 종목 선택 (yfinance로 조회 가능한 종목)
        backtest_tickers = {
            "ETF": {"KODEX 200": "069500.KS", "TIGER 미국S&P500": "360750.KS"},
            "주식": {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS"},
            "채권": {"TLT": "TLT"}, # 미국 장기채 ETF (한국 채권 ETF 데이터 연동 어려움)
            "금": {"GLD": "GLD"} # 금 ETF (한국 금 선물 ETF 데이터 연동 어려움)
        }

        # 선택된 자산에 해당하는 백테스팅 종목 추출 및 종목 선택 추가
        available_backtest_assets = {}
        for asset_type, tickers_map in backtest_tickers.items():
            if asset_type in selected_assets:
                available_backtest_assets[asset_type] = tickers_map
        
        selected_backtest_tickers = {}
        if available_backtest_assets:
            st.write("각 자산군에서 백테스팅에 사용할 대표 종목을 선택해주세요:")
            for asset_type, tickers_map in available_backtest_assets.items():
                if tickers_map:
                    default_ticker_name = list(tickers_map.keys())[0] # 첫 번째 종목을 기본값으로
                    selected_name = st.selectbox(f"{asset_type} 대표 종목", list(tickers_map.keys()), key=f"backtest_{asset_type}")
                    selected_backtest_tickers[asset_type] = tickers_map[selected_name]
        
        if st.button("백테스팅 시작"):
            if not selected_backtest_tickers:
                st.warning("백테스팅을 위해 최소 1개 이상의 자산군에서 종목을 선택해주세요.")
            else:
                st.write("---")
                st.subheader("🗓️ 백테스팅 결과")
                
                total_portfolio_returns = pd.Series(dtype=float)
                
                # 가중 평균 수익률 계산
                for asset, allocation in portfolio.items():
                    if allocation > 0 and asset in available_backtest_assets and asset in selected_backtest_tickers:
                        ticker_symbol = selected_backtest_tickers[asset]
                        st.write(f"**{asset} ({ticker_symbol})** 데이터 로딩 중...")
                        asset_data = get_stock_data(ticker_symbol, period="1y") # 1년치 데이터로 충분
                        
                        if not asset_data.empty:
                            # 선택한 기간으로 자르기
                            asset_data = asset_data[(asset_data.index >= pd.Timestamp(start_date)) & (asset_data.index <= pd.Timestamp(end_date))]
                            if not asset_data.empty:
                                daily_returns = asset_data.pct_change().dropna()
                                
                                # 포트폴리오 기여도 계산
                                if total_portfolio_returns.empty:
                                    total_portfolio_returns = daily_returns * (allocation / 100)
                                else:
                                    # 인덱스 정렬 및 조인하여 데이터 누락 방지
                                    common_index = total_portfolio_returns.index.intersection(daily_returns.index)
                                    total_portfolio_returns = total_portfolio_returns.loc[common_index] + (daily_returns.loc[common_index] * (allocation / 100))
                                
                                st.write(f"- **{asset}** ({ticker_symbol}): 데이터 로딩 완료")
                            else:
                                st.warning(f"'{asset}' ({ticker_symbol})에 대한 선택 기간 내 데이터가 없습니다.")
                        else:
                            st.warning(f"'{asset}' ({ticker_symbol})에 대한 데이터를 찾을 수 없습니다.")

                if not total_portfolio_returns.empty:
                    cumulative_returns = (1 + total_portfolio_returns).cumprod()
                    
                    if not cumulative_returns.empty:
                        initial_value = 1000 # 가상의 초기 투자 금액
                        final_value = initial_value * cumulative_returns.iloc[-1]
                        total_return_percent = ((final_value - initial_value) / initial_value) * 100

                        st.markdown(f"**총 포트폴리오 수익률 (기간: {start_date} ~ {end_date}): {total_return_percent:.2f}%**")
                        st.markdown(f"*{initial_value:,.0f}원 투자 시 약 {final_value:,.0f}원이 됩니다.*")

                        fig_backtest = px.line(cumulative_returns, title='<b>포트폴리오 누적 수익률</b>')
                        fig_backtest.update_layout(showlegend=False)
                        st.plotly_chart(fig_backtest, use_container_width=True)
                    else:
                        st.warning("선택하신 종목들로 백테스팅을 수행할 충분한 데이터가 없습니다.")
                else:
                    st.warning("백테스팅을 위한 종목 데이터를 불러오지 못했습니다. 선택하신 자산군 중 데이터를 제공하는 종목을 다시 선택해주세요.")

    # 7. 위험 경고
    st.markdown("---")
    st.markdown("### ⚠️ 중요: 투자 위험 고지")
    st.warning(
        "**본 앱에서 제공하는 정보는 투자 참고용이며, 어떠한 투자 권유도 아닙니다.**\n"
        "투자는 원금 손실의 위험을 내포하고 있으며, 과거 수익률이 미래 수익률을 보장하지 않습니다.\n"
        "제공된 정보는 시장 상황, 데이터 출처, 계산 로직에 따라 실제와 다를 수 있습니다.\n"
        "**투자 결정은 반드시 본인의 판단과 책임 하에 이루어져야 합니다.**\n"
        "전문가와 상담하여 신중하게 투자하시기를 강력히 권고합니다."
    )

st.markdown("---")
st.sidebar.markdown("© 2025 AI 투자 도우미")
