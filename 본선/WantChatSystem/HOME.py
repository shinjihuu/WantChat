import streamlit as st
from PIL import Image

st.set_page_config(page_title='₩antChat', page_icon='💲')


def main():
    st.markdown("<h1 style='text-align: center; color: black; font-size: 70px;'>₩antChat</h1>", unsafe_allow_html=True)
    image = Image.open('data\\wantchat.png')
    col1, col2, col3 = st.columns(3)
    with col2:
        st.image(image, width=500) 

    main_ft = st.selectbox('',["어떤 기능을 제공하고 있나요?","💙 ₩ANT", "💛 CHAT"])

    if main_ft == '💙 ₩ANT':
        st.text('당신이 💙WANT💙하는 ETF를 추천해드립니다!')
        st.text('왼쪽의 💙 ₩ANT 버튼을 눌러 시작하세요!')
    if main_ft == '💛 CHAT':
        st.text('ETF에 대한 모든 것을 💛CHAT💛하세요!')
        st.text('왼쪽의 💛 CHAT 버튼을 눌러 시작하세요!')



if __name__=='__main__':
    main()