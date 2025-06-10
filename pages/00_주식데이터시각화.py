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
    series_list = []
    successful_tickers = []
    failed_tickers = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if df.empty:
                st.warning(f"⚠️ **{ticker}**: 해당 기간의 주가 데이터를 찾을 수 없거나 데이터가 비어 있습니다.")
                failed_tickers.append(ticker)
                continue

            # 컬럼 확인 및 데이터 추출 로직 강화
            selected_column_data = None
            
            if 'Adj Close' in df.columns:
                selected_column_data = df['Adj Close']
            elif 'Close' in df.columns:
                st.warning(f"⚠️ **{ticker}**: 'Adj Close' 컬럼이 없어 'Close' 컬럼으로 데이터를 사용합니다.")
                selected_column_data = df['Close']
            # 멀티인덱스 컬럼 처리 (이전에 구현된 로직 유지)
            elif isinstance(df.columns, pd.MultiIndex):
                adj_close_col_name = None
                close_col_name = None
                for col_tuple in df.columns:
                    if isinstance(col_tuple, tuple):
                        if 'Adj Close' in col_tuple:
                            adj_close_col_name = col_tuple
                        if 'Close' in col_tuple:
                            close_col_name = col_tuple
                
                if adj_close_col_name:
                    selected_column_data = df[adj_close_col_name]
                    st.warning(f"⚠️ **{ticker}**: 멀티인덱스 컬럼에서 'Adj Close'를 찾아 사용합니다.")
                elif close_col_name:
                    selected_column_data = df[close_col_name]
                    st.warning(f"⚠️ **{ticker}**: 멀티인덱스 컬럼에서 'Adj Close' 대신 'Close'를 찾아 사용합니다.")
            
            if selected_column_data is not None and not selected_column_data.empty:
                # Series에 티커 이름 할당 (pd.concat 시 컬럼명으로 사용)
                selected_column_data.name = ticker
                series_list.append(selected_column_data)
                successful_tickers.append(ticker)
            else:
                st.warning(f"⚠️ **{ticker}**: 유효한 주가 데이터를 추출할 수 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
                failed_tickers.append(ticker)

        except Exception as e:
            st.error(f"❌ **{ticker}**: 주가 데이터를 다운로드하는 중 오류가 발생했습니다: {e}")
            failed_tickers.append(ticker)

    if failed_tickers:
        st.error(f"다음 기업들의 데이터 로딩에 실패했습니다: **{', '.join(failed_tickers)}**")
    
    # 성공적으로 로드된 Series들을 하나의 DataFrame으로 합치기
    if series_list:
        # 모든 Series의 날짜 인덱스를 기준으로 외부 조인하여 합침
        # fillna(method='ffill')로 이전 값을 채우고, 이후 fillna(method='bfill')로 이후 값을 채움
        # .loc[start_date:end_date]로 처음 지정했던 날짜 범위로 잘라냄
        combined_df = pd.concat(series_list, axis=1, join='outer')
        
        # 날짜 인덱스를 정렬 (필요시)
        combined_df = combined_df.sort_index()

        # 전체 기간 동안의 모든 날짜 인덱스를 생성하여 reindex (주말/공휴일 등 비거래일 포함)
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        combined_df = combined_df.reindex(all_dates)

        # NaN 값 처리: 앞의 값으로 채우고, 앞의 값이 없으면 뒤의 값으로 채움
        combined_df = combined_df.fillna(method='ffill').fillna(method='bfill')

        # 처음 시작일부터 데이터가 없는 기업의 경우를 대비하여 모든 NaN 컬럼 제거
        combined_df = combined_df.dropna(axis=1, how='all')

        return combined_df
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
        # 첫 행이 모두 NaN인 경우 오류 방지 (예: 모든 데이터가 시작일부터 NaN인 경우)
        if not stock_data.iloc[0].isnull().all():
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
            st.warning("선택된 기업 중 유효한 주가 변화율을 계산할 수 있는 데이터가 없습니다. 주가 데이터가 너무 짧거나, 지정된 기간에 거래일이 없습니다.")

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
