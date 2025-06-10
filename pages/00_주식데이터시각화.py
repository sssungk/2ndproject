import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 글로벌 시총 TOP 10 기업 티커 (2025년 6월 기준 예상, 변동 가능성 있음)
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
    "BRK-A", # Berkshire Hathaway
    "LLY",   # Eli Lilly and Company
    "JPM",   # JPMorgan Chase & Co.
    # "AVGO",  # Broadcom - 2024년 기준 TOP 10에 있었으나, 변동될 수 있습니다.
]

# 2. 스트림릿 앱 제목 설정
st.title("글로벌 시총 TOP 10 기업 주가 변화 (최근 3년)")
st.write("yfinance를 이용하여 최근 3년간 글로벌 시총 TOP 10 기업의 주가 변화를 시각화합니다.")

# 3. 데이터 로드 함수
@st.cache_data
def load_stock_data(tickers, start_date, end_date):
    data = {}
    for ticker in tickers:
        try:
            # yfinance로 주가 데이터 다운로드
            df = yf.download(ticker, start=start_date, end=end_date)
            if not df.empty:
                data[ticker] = df['Adj Close'] # 수정 종가 사용
            else:
                st.warning(f"경고: {ticker} 에 대한 데이터를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"오류 발생 ({ticker}): {e}")
    return pd.DataFrame(data)

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
        st.warning("선택된 기업에 대한 주가 데이터를 가져오지 못했습니다.")
else:
    st.info("시각화할 기업을 선택해주세요.")
