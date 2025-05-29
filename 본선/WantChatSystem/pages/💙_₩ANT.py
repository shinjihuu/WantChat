import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from service import *

def etf_recommend():
    st.title('💙 ₩ANT')
    st.text('당신이 💙WANT💙하는 ETF를 추천해드립니다!')
    st.text('배당수익이란? 특정 주기로 ETF 투자자에게 주어지는 배당금으로 얻는 수익입니다.')
    st.text('매매수익이란? 매입한 ETF의 시세차이로 얻는 수익입니다.')

    # 수익 방식 선택
    col1, col2 = st.columns(2)
    with col1:
        if st.button('배당수익'):
            st.session_state['revenue_type'] = '배당수익'
    with col2:
        if st.button('매매수익'):
            st.session_state['revenue_type'] = '매매수익'

    # 매매수익 선택 시
    if st.session_state.get('revenue_type') == '매매수익':

        # sector 선택
        sct_lst = ydf['ser_cfc_nm'].replace('NONE', '-').fillna('-').unique().tolist()
        sct_lst.remove('-')
        sct_lst.append('상관없음')
        sector = st.selectbox('추천될 ETF가 포함하길 원하는 sector를 선택해주세요', sct_lst)
        sector_pct = st.slider(f"{sector} 산업이 몇 퍼센트 이상 차지하길 원하십니까?", min_value=0, max_value=100, step=1, value=10)
        
        if st.pills(' ',options=["다음"], key='next1'):
            st.session_state['sector_selected'] = sector
            st.session_state['sector_percent'] = sector_pct
            st.session_state['svc1'] = service1(sector, sector_pct)  
            
        # 주식 선택
        if 'sector_selected' in st.session_state:
            stk = st.text_input('추천될 ETF가 포함하길 원하는 주식을 입력해주세요', help="없다면 '상관없음'을 체크해주세요")
            nomatter = st.checkbox('상관없음', key='no_matter_stk')
            stk_pct = st.slider(f"{stk} 주식을 몇 퍼센트 이상 보유하길 원하십니까?", min_value=0, max_value=100, step=1, value=10)
            st.session_state['svc2'] = list(set(service2(stk, stk_pct)) & set(st.session_state['svc1']))

            if nomatter or not stk:
                st.session_state['svc2'] = st.session_state['svc1']
            
            # 시각화 기간 입력
            if 'svc2' in st.session_state and st.pills(' ',options=["다음"], key="next2"):
                vis_mon = st.number_input('조건에 해당하는 ETF의 시각화 자료입니다. 분석할 기간을 결정해주세요.', 1, 36, 1)

                if st.pills(' ',options=["다음"], key="next3"):
                    st.session_state['vis_mon'] = vis_mon
                    svc34 = service34(st.session_state['svc2'],st.session_state['vis_mon'])
                    plt3, plt4 = st.columns(2)
                    with plt3:
                        st.bar_chart(svc34, x="Ticker",y="Market_Price")
                    with plt4:
                        c=(alt.Chart(svc34).mark_circle(color="orange")
                            .encode(x="Volatility",y="Return",tooltip=["Ticker"],color='Ticker'))
                        c_x = svc34['Volatility'].mean()
                        c_y = 0
                        vline = alt.Chart(pd.DataFrame({'x': [c_x]})).mark_rule(color='red').encode(x='x:Q')
                        hline = alt.Chart(pd.DataFrame({'y': [c_y]})).mark_rule(color='blue').encode(y='y:Q')
                        offset = max((svc34['Volatility']-c_x).abs().max(), (svc34['Return']-c_y).abs().max()) 
                        chart = alt.Chart(svc34).mark_circle(size=80).encode(
                            x=alt.X('X:Q', scale=alt.Scale(domain=[c_x-offset, c_x+offset])),
                            y=alt.Y('Y:Q', scale=alt.Scale(domain=[c_y-offset, c_y+offset])),
                        )
                        st.altair_chart(c+vline+hline+chart)
                        
                    fin_lst = st.multiselect('분석하고 싶은 ETF의 티커를 골라주세요',svc34['Ticker'].tolist(),svc34['Ticker'].tolist())
                    
                    # 모델링 시작
                    if st.pills(' ',options=['모델링 시작!']):
                        best, pct = lstm_model(fin_lst)
                        st.markdown('## 당신의 성향에 꼭 맞는 :orange[ETF]는!!!')
                        st.markdown(f'# {best}입니다~')
                        st.markdown(f'#### :green[{pct[0][0]:.2f}]%의 확률로 한 달 내에 주가가 상승할 것으로 예측됩니다.')
                    
                        svc6 = service6(best)
                        plt6 = px.pie(svc6,values='wht_pct',names='tck_iem_cd',title=f'{best}의 구성정보')
                        st.plotly_chart(plt6)

                        
                        

    # 배당수익 선택 시
    elif 'revenue_type' in st.session_state and st.session_state['revenue_type'] == '배당수익':

        st.text('')
        st.text('우선순위를 선택해주세요.')

        # 우선 순위 성장률/수익률 선택
        col1, col2 = st.columns(2)
        with col1:
            if st.button('성장률'):
                st.session_state['priority'] = '1'
        with col2:
            if st.button('수익률'):
                st.session_state['priority'] = '2'

        # 배당 주기 선택
        if 'priority' in st.session_state:
            st.text('')
            st.text('원하는 배당 주기를 선택해주세요')
            period_options = ['1개월', '3개월', '6개월', '1년', '상관없음']
            col_periods = st.columns(len(period_options))
            for i, period in enumerate(period_options):
                with col_periods[i]:
                    if st.button(period):
                        st.session_state['period'] = period

            if 'period' in st.session_state:
                svc5 = service5(st.session_state['priority'], st.session_state['period'], div)
                st.bar_chart(svc5,y='가중치_총점',x='ETF_티커',color='#ffd966')
                best = svc5[svc5['가중치_총점']==max(svc5['가중치_총점'])]['ETF_티커']
                st.markdown('## 당신의 성향에 꼭 맞는 :orange[ETF]는!!!')
                st.markdown(f'# {best.values[0]}입니다~')
 

if __name__ == '__main__':
    etf_recommend()
