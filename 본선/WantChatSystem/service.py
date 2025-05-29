import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil.relativedelta import relativedelta
import yfinance as yf
import numpy as np
from sklearn.preprocessing import StandardScaler
import altair as alt
import plotly.express as px
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import LSTM, Dropout, Dense, Bidirectional



#### 데이터칸
# streamlit에서 오류난다면 data 폴더 안에 있는 해당 파일 우클릭 > 경로 복사 복붙해주시길 바랍니다.
@st.cache_data
def load_data():
    div = pd.read_csv('data/final_merge.csv')
    hld = pd.read_csv('data/NH_CONTEST_DATA_ETF_HOLDINGS.csv', encoding='cp949')
    ydf = pd.read_excel('data/new_df.xlsx')
    return div, hld, ydf

div, hld, ydf = load_data()


def service1(sec, percent=0):
    if sec == '상관없음':
        lst = ydf['etf_tck_cd'].tolist()
    else:
        sec_df = ydf[ydf['ser_cfc_nm'] == sec]
        groupby_df = sec_df.groupby(['etf_tck_cd'])[['wht_pct']].sum().reset_index()
        per_df = groupby_df[groupby_df['wht_pct'] > percent]
        lst = per_df['etf_tck_cd'].tolist()
    return lst

def service2(tck_cd, percent=0, cnt=100):
    tck_df = ydf[ydf['tck_iem_cd'] == tck_cd]
    per_df = tck_df[tck_df['wht_pct'] > percent]
    sort_df = per_df.sort_values(by='wht_pct', ascending=False).reset_index()[:cnt]
    return sort_df['etf_tck_cd']

def service34(ticker_list, period=1):
    """
    통합된 market_price 및 변동성/수익률 분석
    - 티커 리스트 길이가 10 이상일 경우 상위 10개 정렬.
    - 좌측에는 market_price, 우측에는 변동성/수익률 그래프.
    """
    if len(ticker_list) < 1:
        raise ValueError("티커 리스트가 비어있습니다.")

    # 데이터 저장용 리스트
    market_prices, volatilities, returns = [], [], []

    today = pd.Timestamp.now()
    end_date = today.strftime('%Y-%m-%d')
    start_date = (today - pd.DateOffset(months=period)).strftime('%Y-%m-%d')

    for ticker in ticker_list:
        try:
            # 티커별 데이터 다운로드
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if data.empty:
                continue

            # market_price 계산 (종가의 평균값)
            market_prices.append(data['Close'].mean())

            # 변동성 계산
            volatilities.append(data['Close'].var())

            # 수익률 계산
            returns.append((data['Close'].iloc[-1] / data['Open'].iloc[0] - 1) * 100)
        except Exception as e:
            print(f"{ticker} 처리 중 오류 발생: {e}")
            continue

    # DataFrame으로 변환
    analysis_df = pd.DataFrame({
        'Ticker': ticker_list,
        'Market_Price': market_prices,
        'Volatility': volatilities,
        'Return': returns
    })

    # 티커 리스트 길이가 10 이상일 경우 상위 10개 선별
    if len(ticker_list) >= 10:
        # 표준화
        scaler = StandardScaler()
        analysis_df[['Standardized_Market_Price', 'Standardized_Return']] = scaler.fit_transform(
            analysis_df[['Market_Price', 'Return']]
        )

        # 가중치 점수 계산
        analysis_df['Score'] = (
            analysis_df['Standardized_Market_Price'] * 0.5 +
            analysis_df['Standardized_Return'] * 0.5
        )

        # 상위 10개 정렬
        analysis_df = analysis_df.sort_values(by='Score', ascending=False).head(10)

    # 상위 티커 리스트 반환
    return analysis_df

def service5(priority, dividend_period, final_merge):
    # 연간 배당 수익률 계산
    final_merge['연간_배당수익률'] = final_merge.apply(
        lambda row: row['배당금'] * (12 if row['배당주기'] == '1개월' else
                                    2 if row['배당주기'] == '6개월' else
                                    4 if row['배당주기'] == '3개월' else
                                    1),
        axis=1
    )

    # 우선순위 설정
    weights = {
        '1': {'growth': 0.7, 'yield': 0.2, 'fcf': 0.1, 'payout': 0.1},
        '2': {'growth': 0.2, 'yield': 0.7, 'fcf': 0.1, 'payout': 0.1}
    }[priority]

    # 표준화
    scaler = StandardScaler()
    cols_to_scale = ['연평균배당성장률', '연간_배당수익률', 'free_cash_flow', 'Dividend_Payout_Ratio']
    final_merge[[f'표준화_{col}' for col in cols_to_scale]] = scaler.fit_transform(final_merge[cols_to_scale])

    # 가중치 총점 계산
    final_merge['가중치_총점'] = (
        final_merge['표준화_연평균배당성장률'] * weights['growth'] +
        final_merge['표준화_연간_배당수익률'] * weights['yield'] +
        final_merge['표준화_free_cash_flow'] * weights['fcf'] +
        final_merge['표준화_Dividend_Payout_Ratio'] * weights['payout']
    )

    # 배당 주기에 따른 필터링
    if dividend_period != '상관없음':
        final_merge = final_merge[final_merge['배당주기'] == dividend_period]

    # 정렬 및 결과 반환
    sorted_etfs = final_merge.sort_values(by='가중치_총점', ascending=False).head(20)
    return sorted_etfs[['ETF_티커', '연간_배당수익률', '연평균배당성장률', '가중치_총점']]


def service6(etf):
    sort_df = ydf[ydf['etf_tck_cd'] == etf]
    sort_df['tck_iem_cd'] = sort_df.apply(lambda x: 'etc.' if x['wht_pct'] <= 1 else x['tck_iem_cd'], axis=1)
    df_g = sort_df.groupby('tck_iem_cd')['wht_pct'].sum().reset_index()
    return df_g


def lstm_model(lst):
    result = {}
    for tck in lst:
        # 데이터 정리
        data = yf.download(tck, start='2022-01-01', end='2024-10-31',progress=False)[['Close']]
        data['Target'] = np.where(data['Close'].shift(-20) > data['Close'], 1, 0)
        data = data[data.index < '2024-09-30']

        # 표준화
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data[['Close']])

        # 시퀀스 데이터 생성
        def create_dataset(data, time_step=1):
            X, y = [], []
            for i in range(len(data) - time_step):
                X.append(data[i:(i + time_step), 0])  # Close 데이터
                y.append(data[i + time_step, 1])      # Target 데이터
            return np.array(X), np.array(y)

        # 데이터 배열로 변환
        scaled_data = data[['Close', 'Target']].values

        time_step = 20
        X, y = create_dataset(scaled_data, time_step)

        # X의 형태를 맞추기 위해 reshape
        X = X.reshape(X.shape[0], X.shape[1], 1)

        # 훈련 세트와 테스트 세트로 분리
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 모델
        model = Sequential()
        model.add(Bidirectional(LSTM(64, return_sequences=True), input_shape=(X_train.shape[1], X_train.shape[2])))
        model.add(Dropout(0.2))
        model.add(Bidirectional(LSTM(32, return_sequences=False)))
        model.add(Dropout(0.2))
        model.add(Dense(1, activation='sigmoid'))

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2)
        
        # 성능
        _, acc = model.evaluate(X_test,y_test)
        accuracy = acc * 100
        
        if accuracy > 50:
            
            # 미래 데이터 예측
            # 예시로 최근 데이터 20일을 가져와서 예측
            last_20_days = data[-time_step:][['Close']].values  # 마지막 20일의 종가
            last_20_days = scaler.transform(last_20_days)  # 정규화
            last_20_days = last_20_days.reshape(1, time_step, 1)  # (1, 20, 1) 형태로 변환

            # 예측
            future_prediction = model.predict(last_20_days) *100
            
            #저장
            result[tck] = future_prediction.round(2)
        
        max_key = max(result, key=result.get)  # 가장 큰 값을 가진 키
        max_value = result[max_key] 

    return max_key, max_value
        