import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 글로벌 시총 TOP 10 기업 티커 (2025년 6월 기준 예상, 실제 시점에 따라 변동 가능)
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
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if df.empty:
                st.warning(f"⚠️ **{ticker}**: 해당 기간의 주가 데이터를 찾을 수 없거나 데이터가 비어 있습니다.")
                failed_tickers.append(ticker)
                continue # 다음 티커로 넘어감

            # 컬럼 확인 및 데이터 추출 로직 강화
            # 1순위: 'Adj Close' 컬럼이 있는지 확인
            if 'Adj Close' in df.columns:
                data[ticker] = df['Adj Close']
                successful_tickers.append(ticker)
            # 2순위: 'Close' 컬럼이 있는지 확인 (Adj Close가 없을 경우)
            elif 'Close' in df.columns:
                st.warning(f"⚠️ **{ticker}**: 'Adj Close' 컬럼이 없어 'Close' 컬럼으로 데이터를 사용합니다.")
                data[ticker] = df['Close']
                successful_tickers.append(ticker)
            # 3순위: 컬럼이 튜플 형태의 멀티인덱스이고 'Adj Close'가 포함된 경우
            # 이 경우는 현재 주어진 오류 메시지와는 다르게 'Adj Close'가 실제 존재할 때를 대비
            elif any(('Adj Close', t) in df.columns for t in df.columns.levels[1] if isinstance(df.columns, pd.MultiIndex)):
                adj_close_col_name = None
                for col_tuple in df.columns:
                    if isinstance(col_tuple, tuple) and 'Adj Close' in col_tuple:
                        adj_close_col_name = col_tuple
                        break
                if adj_close_col_name:
                    data[ticker] = df[adj_close_col_name]
                    successful_tickers.append(ticker)
                    st.warning(f"⚠️ **{ticker}**: 멀티인덱스 컬럼에서 'Adj Close'를 찾아 사용합니다.")
                else:
                    st.warning(f"⚠️ **{ticker}**: 멀티인덱스 컬럼에서 'Adj Close'를 찾을 수 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
                    failed_tickers.append(ticker)
            # 4순위: 컬럼이 튜플 형태의 멀티인덱스이고 'Close'가 포함된 경우
            elif any(('Close', t) in df.columns for t in df.columns.levels[1] if isinstance(df.columns, pd.MultiIndex)):
                close_col_name = None
                for col_tuple in df.columns:
                    if isinstance(col_tuple, tuple) and 'Close' in col_tuple:
                        close_col_name = col_tuple
                        break
                if close_col_name:
                    data[ticker] = df[close_col_name]
                    successful_tickers.append(ticker)
                    st.warning(f"⚠️ **{ticker}**: 멀티인덱스 컬럼에서 'Adj Close' 대신 'Close'를 찾아 사용합니다.")
                else:
                    st.warning(f"⚠️ **{ticker}**: 멀티인덱스 컬럼에서 'Close'를 찾을 수 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
                    failed_tickers.append(ticker)
            else:
                st.warning(f"⚠️ **{ticker}**: 'Adj Close' 또는 'Close' 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
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
        # 데이터프레임이 비어있지 않고, 첫 행이 모두 NaN이 아닌지 확인
        if not stock_data.empty and not stock_data.iloc[0].isnull().all():
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
