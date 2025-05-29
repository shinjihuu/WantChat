from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain_teddynote.messages import AgentStreamParser
import os
import pandas as pd
import streamlit as st

# openAI API key 입력
os.environ['OPENAI_API_KEY'] = 'API key 입력' 
folder_path = 'data' # streamlit에서 오류난다면 data 폴더 우클릭 > 경로 복사 복붙해주시길 바랍니다.


@st.cache_data
def df_file(folder_path):
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv') and f.startswith('NH')]
    dataframes = []

    for file_name in csv_files:
        path = os.path.join(folder_path, file_name)
        df = pd.read_csv(path, encoding='euc-kr')
        dataframes.append(df)
    
    return dataframes


dataframes = df_file(folder_path)
stream_parser = AgentStreamParser()


@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: lambda _: None})
def ask(query, dataframes, context):
    chat_model = ChatOpenAI(temperature=0, model='gpt-4o-mini')

    agent = create_pandas_dataframe_agent(
        chat_model,
        dataframes,
        verbose=False,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        allow_dangerous_code=True
    )
    
    full_query = " ".join([m["content"] for m in context]) + " " + query
    response = agent.run(full_query)
    return response



def chatbot():

    st.title("💛 CHAT")
    st.text('ETF에 대한 모든 것을 💛CHAT💛하세요!')

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    if prompt := st.chat_input("질문을 입력하세요:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        context = st.session_state.messages
        response = ask(prompt, dataframes, context)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.sidebar.button("초기화"):
        st.session_state.messages = [] 


if __name__ == "__main__":
    chatbot()
