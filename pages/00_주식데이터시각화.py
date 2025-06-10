import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 글로벌 시총 TOP 10 기업 티커 (2025년 6월 기준 예상, 실제 시점에 따라 변동 가능)
# 실제 2025년 6월 TOP 10은 변동될 수 있으므로, 실제 서비스를 구현하실 때는
# 최신 데이터를 참고하여 티커를 업데이트 해주셔야 합니다.
# 여기서는 예시를 위해 현재(2024년 말 기준) TOP 10과 유사한 기업들을 포함했습니다.
top_10_tickers = [
    "MSFT",  # Microsoft
    "AAPL",  # Apple
    "NVDA",  # NVIDIA
    "GOOGL", # Alphabet (Google)
    "AMZN",  # Amazon
    "META",  # Meta Platforms
    "TSLA",  # Tesla
    "BRK-A", # Berkshire Hathaway A주
    "LLY",   # Eli Lilly and Company
    "JPM",   # JPMorgan Chase & Co.
]

# 2. 스트림릿 앱 제목 설정
st.title("글로벌 시총 TOP 10 기업 주가 변화 (최근 3년)")
st.write("yfinance를 이용하여 최근 3년간 글로벌 시총 TOP 10 기업의 주가 변화를 시각화합니다.")

# 3. 데이터 로드 함수
@st.cache_data(ttl=3600) # 데이터를 1시간(3600초) 동안 캐싱합니다.
def load_stock_data(tickers, start_date, end_date):
    data = {}
    successful_tickers = []
    failed_tickers = []

    for ticker in tickers:
        try:
            # yfinance로 주가 데이터 다운로드
            # progress=False 로 설정하여 다운로드 시 콘솔에 나타나는 진행률 표시를 비활성화합니다.
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)

            # 데이터프레임이 비어있지 않고, 'Adj Close' 컬럼이 있는지 확인
            if not df.empty and 'Adj Close' in df.columns:
                data[ticker] = df['Adj Close']
                successful_tickers.append(ticker)
            elif not df.empty and 'Adj Close' not in df.columns:
                st.warning(f"⚠️ **{ticker}**: 데이터를 가져왔으나 'Adj Close' 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
                failed_tickers.append(ticker)
            else:
                st.warning(f"⚠️ **{ticker}**: 해당 기간의 주가 데이터를 찾을 수 없거나 데이터가 비어 있습니다.")
                failed_tickers.append(ticker)
        except Exception as e:
            st.error(f"❌ **{ticker}**: 주가 데이터를 다운로드하는 중 오류가 발생했습니다: {e}")
            failed_tickers.append(ticker)

    if failed_tickers:
        st.error(f"다음 기업들의 데이터 로딩에 실패했습니다: **{', '.join(failed_tickers)}**")
    
    # 성공적으로 로드된 데이터만 DataFrame으로 반환
    if successful_tickers:
        return pd.DataFrame({k: data[k] for k in successful_tickers})
    else:
        return pd.DataFrame() # 모든 데이터 로드 실패 시 빈 DataFrame 반환

# 4. 날짜 범위 설정 (최근 3년)
end_date = pd.to_datetime('today').strftime('%Y-%m-%d')
start_date = (pd.to_datetime('today') - pd.DateOffset(years=3)).strftime('%Y-%m-%d')

st.sidebar.header("날짜 및 기업 선택")
selected_tickers = st.sidebar.multiselect(
    "주가 변화를 보고 싶은 기업을 선택하세요:",
    options=top_10_tickers,
    default=top_10_tickers # 기본적으로 모두 선택
)

# 5. 데이터 로드
if selected_tickers:
    stock_data = load_stock_data(selected_tickers, start_date, end_date)

    if not stock_data.empty:
        # 6. 주가 변화율 계산 (선택 사항: 정규화된 주가)
        # 모든 기업의 주가 변화를 동일 선상에서 비교하기 위해 첫 날을 기준으로 정규화합니다.
        # 데이터프레임이 비어있지 않은지 다시 한번 확인 후 정규화 진행
        if not stock_data.empty and not stock_data.iloc[0].isnull().all(): # 첫 행이 모두 NaN이 아닌지 확인
            normalized_stock_data = stock_data / stock_data.iloc[0] * 100
            st.subheader("기업별 주가 변화율 (최초일 기준 100% 정규화)")
            fig = go.Figure()
            for col in normalized_stock_data.columns:
                fig.add_trace(go.Scatter(x=normalized_stock_data.index, y=normalized_stock_data[col], mode='lines', name=col))

            fig.update_layout(
                title="최근 3년간 글로벌 시총 TOP 10 기업 주가 변화율",
                xaxis_title="날짜",
                yaxis_title="주가 변화율 (%)",
                hovermode="x unified",
                legend_title="기업",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("선택된 기업 중 유효한 주가 변화율을 계산할 수 있는 데이터가 없습니다.")

        st.subheader("원본 주가 데이터")
        fig_raw = go.Figure()
        for col in stock_data.columns:
            fig_raw.add_trace(go.Scatter(x=stock_data.index, y=stock_data[col], mode='lines', name=col))

        fig_raw.update_layout(
            title="최근 3년간 글로벌 시총 TOP 10 기업 원본 주가",
            xaxis_title="날짜",
            yaxis_title="주가 (USD)",
            hovermode="x unified",
            legend_title="기업",
            height=600
        )
        st.plotly_chart(fig_raw, use_container_width=True)


        st.subheader("데이터 미리보기")
        st.dataframe(stock_data.tail()) # 최신 데이터 몇 개 보여주기

    else:
        st.warning("선택된 기업에 대한 주가 데이터를 가져오지 못했습니다. 목록에서 다른 기업을 선택해 주세요.")
else:
    st.info("시각화할 기업을 선택해주세요.")
