import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import datetime

# --- 앱 설정 (가장 먼저 위치해야 함) ---
st.set_page_config(layout="wide", page_title="AI 투자 도우미")

# --- 캐싱 함수 정의 (st.cache_data 사용) ---
@st.cache_data(ttl=3600) # 1시간마다 캐시 갱신
def get_stock_data(ticker, period="1y"):
    """
    yfinance를 사용하여 주식/ETF 데이터를 가져오는 함수.
    'Adj Close' 데이터가 없을 경우 'Close' 데이터를 사용하고,
    데이터가 없으면 안전하게 빈 Series를 반환하여 호출 측에서 처리하도록 함.
    (데이터 없음 경고 메시지는 호출하는 곳에서 제어)
    """
    try:
        data = yf.download(ticker, period=period)

        if data.empty:
            return pd.Series(dtype='float64') # 빈 Series 반환

        if 'Adj Close' in data.columns and not data['Adj Close'].empty:
            return data['Adj Close']
        elif 'Close' in data.columns and not data['Close'].empty:
            return data['Close']
        else:
            return pd.Series(dtype='float64') # 유효한 컬럼이 없으면 빈 Series 반환

    except Exception:
        # yfinance 오류 시에도 경고 메시지를 외부에서 제어하기 위해 빈 Series 반환
        return pd.Series(dtype='float64')

# --- 앱 본문 시작 ---

# 4. '투자위험고지'는 자신의 투자 성향을 선택하는 것보다 위에 위치하도록 수정
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
                    "Invesco DB Commodity Index Tracking Fund (DBC)": "DBC", # 종합 원자재 ETF
                    "Aberdeen Standard Physical Platinum Shares ETF (PPLT)": "PPLT", # 백금 ETF
                    "KODEX 구리선물(H)": "226340.KS" # 국내 구리 ETF
                },
                "설명": "원유, 구리, 곡물, 귀금속 등 실물 자산에 투자합니다. 글로벌 경제 상황이나 공급망 이슈에 따라 가격 변동성이 큽니다. 포트폴리오의 분산 효과를 높이는 데 활용될 수 있습니다."
            }
        }

        for asset in selected_assets:
            if asset in asset_recommendations:
                st.markdown(f"#### ➡️ {asset}")
                st.write(f"**설명:** {asset_recommendations[asset]['설명']}")

                # 채권의 경우 세분화된 종목을 표시
                if asset == "채권":
                    for bond_type, bond_info in asset_recommendations[asset]['세부종목'].items():
                        st.markdown(f"##### {bond_type}")
                        st.write(f"**설명:** {bond_info['설명']}")
                        st.write(f"**추천 종목/ETF:**")
                        if bond_info['종목']:
                            for name, ticker in bond_info['종목'].items():
                                col1, col2 = st.columns([0.5, 0.5]) # 티커는 표시하지 않도록 컬럼 조정
                                col1.write(f"- **{name}**")
                                stock_data_series = get_stock_data(ticker, period="2d")
                                if not stock_data_series.empty and len(stock_data_series) >= 1 and pd.api.types.is_numeric_dtype(stock_data_series):
                                    current_price = stock_data_series.iloc[-1]
                                    if len(stock_data_series) > 1 and pd.api.types.is_numeric_dtype(stock_data_series.iloc[-2]):
                                        previous_price = stock_data_series.iloc[-2]
                                        daily_change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price != 0 else 0
                                        col2.metric("현재가", f"{current_price:,.2f}", f"{daily_change_percent:,.2f}%")
                                    else:
                                        col2.metric("현재가", f"{current_price:,.2f}")
                                else:
                                    col2.write("데이터 없음") # 데이터가 없을 때만 "데이터 없음" 표시
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
                            if ticker != "N/A": # N/A인 경우 현재가 표시하지 않음 (KRX 금 시장 등)
                                col1, col2 = st.columns([0.5, 0.5]) # 티커는 표시하지 않도록 컬럼 조정
                                col1.write(f"- **{name}**")
                                stock_data_series = get_stock_data(ticker, period="2d")

                                if not stock_data_series.empty and len(stock_data_series) >= 1 and pd.api.types.is_numeric_dtype(stock_data_series):
                                    current_price = stock_data_series.iloc[-1]
                                    if len(stock_data_series) > 1 and pd.api.types.is_numeric_dtype(stock_data_series.iloc[-2]):
                                        previous_price = stock_data_series.iloc[-2]
                                        daily_change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price != 0 else 0
                                        col2.metric("현재가", f"{current_price:,.2f}", f"{daily_change_percent:,.2f}%")
                                    else:
                                        col2.metric("현재가", f"{current_price:,.2f}")
                                else:
                                    col2.write("데이터 없음") # 데이터가 없을 때만 "데이터 없음" 표시
                            else:
                                st.write(f"- {name}") # N/A인 경우 티커 없이 이름만 표시 (예: KRX 금 시장)
                st.markdown("---")

        # 3. '투자팁 : ISA 계좌 활용'은 'ETF' 란의 상단에 오도록 위치 수정
        if "ETF" in selected_assets:
            st.markdown("### 💡 투자 팁: ISA 계좌 활용")
            st.info(
                "주식, ETF 등 일부 금융 상품을 개인 계좌에서 구매하는 것보다 **ISA (Individual Savings Account) 계좌**를 통해 구매하는 것을 고려해보세요.\n"
                "ISA 계좌는 일정 한도 내에서 **비과세 또는 저율 분리과세 혜택**을 받을 수 있어 절세에 유리합니다.\n"
                "특히, **ETF**와 같은 상품은 ISA 계좌에서 매매차익에 대한 세금 혜택을 받을 수 있으니, 자세한 내용은 증권사에 문의하거나 관련 정보를 찾아보시길 권합니다.\n"
                "**연금저축펀드**와 **IRP** 계좌도 노후 대비 및 세액공제 혜택이 있으니 함께 알아보시면 좋습니다."
            )
            st.markdown("---")


        # 백테스팅 (간단한 예시)
        st.markdown("### 📈 백테스팅 시뮬레이션 (예시)")
        st.markdown("선택된 자산 비중에 따라 **과거 데이터**로 포트폴리오 수익률을 **매우 간략하게** 시뮬레이션 합니다. **실제 수익률과는 차이가 있을 수 있습니다.**")

        # 백테스팅 기간 설정
        current_date_for_default = datetime.date(2025, 6, 10) # 기준 날짜 설정
        default_start_date = (current_date_for_default - pd.DateOffset(years=1)).date()
        default_end_date = current_date_for_default

        start_date = st.date_input("시작 날짜", default_start_date)
        end_date = st.date_input("종료 날짜", default_end_date)

        if start_date >= end_date:
            st.error("시작 날짜는 종료 날짜보다 빨라야 합니다.")
        else:
            # 백테스팅 가능한 종목 선택 (yfinance로 조회 가능한 종목)
            backtest_tickers = {
                "ETF": {"KODEX 미국S&P500TR": "379810.KS", "TIGER 미국나스닥100": "133690.KS", "Invesco QQQ Trust (QQQ)": "QQQ", "SOL 미국배당다우존스": "446860.KS"},
                "주식": {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS"},
                "채권": {"iShares 20+ Year Treasury Bond ETF (TLT)": "TLT", "KODEX 국고채3년": "114260.KS", "KOSEF 단기자금": "123530.KS", "KBSTAR 국고채30년액티브": "306200.KS"},
                "금": {"SPDR Gold Shares (GLD)": "GLD", "KODEX 골드선물(H)": "132030.KS"},
                "원자재": {"United States Oil Fund (USO)": "USO", "KODEX 구리선물(H)": "226340.KS"}
            }

            # 선택된 자산에 해당하는 백테스팅 종목 추출 및 종목 선택 추가
            selected_backtest_tickers = {}
            st.write("각 자산군에서 백테스팅에 사용할 대표 종목을 선택해주세요:")

            has_selectable_backtest_assets = False
            for asset_type in selected_assets:
                # 채권의 경우 세분화된 종목 중 하나를 선택
                if asset_type == "채권" and "세부종목" in asset_recommendations["채권"]:
                    bond_options = {}
                    for bond_category, info in asset_recommendations["채권"]["세부종목"].items():
                        for name, ticker in info["종목"].items():
                            bond_options[f"{bond_category} - {name}"] = ticker
                    
                    if bond_options:
                        has_selectable_backtest_assets = True
                        selected_option_name = st.selectbox(
                            f"{asset_type} 대표 종목", 
                            list(bond_options.keys()), 
                            index=0, 
                            key=f"backtest_{asset_type}"
                        )
                        selected_backtest_tickers[asset_type] = bond_options[selected_option_name]
                # 그 외 자산군
                elif asset_type in backtest_tickers and backtest_tickers[asset_type]:
                    has_selectable_backtest_assets = True
                    if backtest_tickers[asset_type]:
                        default_ticker_name = list(backtest_tickers[asset_type].keys())[0]
                        selected_name = st.selectbox(f"{asset_type} 대표 종목", list(backtest_tickers[asset_type].keys()), index=0, key=f"backtest_{asset_type}")
                        selected_backtest_tickers[asset_type] = backtest_tickers[asset_type][selected_name]
                    else:
                        st.warning(f"{asset_type}에 선택 가능한 백테스팅 종목이 없습니다.")


            if not has_selectable_backtest_assets:
                st.warning("선택하신 자산 중 백테스팅을 지원하는 종목이 없습니다. ETF, 주식, 채권, 금, 원자재 중에서 선택해주세요.")

            if st.button("백테스팅 시작"):
                if not selected_backtest_tickers:
                    st.warning("백테스팅을 위해 최소 1개 이상의 자산군에서 종목을 선택해주세요.")
                else:
                    st.write("---")
                    st.subheader("🗓️ 백테스팅 결과")

                    total_portfolio_returns = pd.Series(dtype=float)
                    initial_data_loaded = False

                    for asset, allocation in portfolio.items():
                        if allocation > 0 and asset in selected_backtest_tickers:
                            ticker_symbol = selected_backtest_tickers[asset]
                            st.write(f"**{asset} ({ticker_symbol})** 데이터 로딩 중...")
                            asset_data_series = get_stock_data(ticker_symbol, period="5y")

                            if not asset_data_series.empty and pd.api.types.is_numeric_dtype(asset_data_series):
                                asset_data_period = asset_data_series[(asset_data_series.index.date >= start_date) & (asset_data_series.index.date <= end_date)]

                                if not asset_data_period.empty:
                                    daily_returns = asset_data_period.pct_change().dropna()

                                    if not initial_data_loaded:
                                        total_portfolio_returns = daily_returns * (allocation / 100)
                                        initial_data_loaded = True
                                    else:
                                        common_index = total_portfolio_returns.index.intersection(daily_returns.index)
                                        if not common_index.empty:
                                            if len(daily_returns.loc[common_index]) > 0 and len(total_portfolio_returns.loc[common_index]) > 0:
                                                total_portfolio_returns = total_portfolio_returns.loc[common_index] + (daily_returns.loc[common_index] * (allocation / 100))
                                            else:
                                                st.warning(f"'{asset}' ({ticker_symbol})과 다른 자산 간의 공통 데이터 기간이 너무 짧거나 데이터가 부족합니다.")
                                        else:
                                            st.warning(f"'{asset}' ({ticker_symbol})과 다른 자산 간의 공통 데이터 기간이 부족하여 합산할 수 없습니다.")

                                    st.write(f"- **{asset}** ({ticker_symbol}): 데이터 로딩 완료")
                                else:
                                    st.warning(f"'{asset}' ({ticker_symbol})에 대한 선택 기간 내 데이터가 없습니다.")
                            else:
                                st.warning(f"'{asset}' ({ticker_symbol})에 대한 데이터를 찾을 수 없거나 유효하지 않습니다. Ticker가 정확한지 확인해주세요.")

                    if not total_portfolio_returns.empty and initial_data_loaded:
                        cumulative_returns = (1 + total_portfolio_returns).cumprod()

                        if not cumulative_returns.empty:
                            initial_value = 1000 # 가상의 초기 투자 금액
                            final_value = initial_value * cumulative_returns.iloc[-1]
                            total_return_percent = ((final_value - initial_value) / initial_value) * 100

                            st.markdown(f"**총 포트폴리오 수익률 (기간: {start_date} ~ {end_date}): {total_return_percent:.2f}%**")
                            st.markdown(f"*{initial_value:,.0f}원 투자 시 약 {final_value:,.0f}원이 됩니다.*")

                            fig_backtest = px.line(cumulative_returns, title='<b>포트폴리오 누적 수익률</b>')
                            fig_backtest.update_layout(showlegend=False, yaxis_title="누적 수익률 (초기 1.0)", xaxis_title="날짜")
                            st.plotly_chart(fig_backtest, use_container_width=True)
                        else:
                            st.warning("선택하신 종목들로 백테스팅을 수행할 충분한 데이터가 없습니다.")
                    else:
                        st.warning("백테스팅을 위한 종목 데이터를 불러오지 못했거나, 선택하신 자산군의 데이터가 부족합니다. 선택하신 자산군 중 데이터를 제공하는 종목을 다시 선택해주세요.")


st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 AI 투자 도우미")
