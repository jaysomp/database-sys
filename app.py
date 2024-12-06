from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)
import streamlit as st
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent, load_tools
from langchain_openai import ChatOpenAI
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import Tool
import os
import sys
from io import StringIO
from contextlib import redirect_stdout

from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM
from pandasai import SmartDataframe
from pandasai.llm import OpenAI
from pandasai.connectors import SqliteConnector

from pandasai.connectors import PostgreSQLConnector
from langchain.memory import ConversationBufferMemory
import time

import re

import psycopg2
from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent

load_dotenv()

global selected_table
selected_table = None

global context_window_size
context_window_size = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def get_table_names():
    try:
        import sqlite3
        conn = sqlite3.connect('ufc_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        return tables
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()

def describe_table(table_name: str) -> str:
    """
    Generate a simplified description of the table including only name and schema.
    """
    try:
        import sqlite3
        conn = sqlite3.connect('ufc_database.db')
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        description = [f"Table: {table_name}"]
        description.append(f"Schema:")
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_nullable = "NULL" if not col[3] else "NOT NULL"
            description.append(f"  {col_name} ({col_type}) {is_nullable}")
        
        return "\n".join(description)
        
    except Exception as e:
        return f"Error describing table: {str(e)}"
    finally:
        if conn:
            cursor.close()
            conn.close()


st_callback = StreamlitCallbackHandler(st.container())


llm = ChatOpenAI(model="gpt-4")

class Pandasainput(BaseModel):
    query: str = Field(description="should be a query for QA")

class SQLinput(BaseModel):
    query: str = Field(description="should be a query for QA")



def multi_table(query):
    """Use this function to query multiple tables in the SQLite database using SQL agent"""
    import sqlite3
    from langchain_community.utilities import SQLDatabase
    
    db = SQLDatabase.from_uri("sqlite:///ufc_data.db")
    
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True
    )
    
    result = agent_executor.invoke({"input": query})
    
    return result["output"]

def pandasai_tool(query):
    """Use this tool when asked questions about a dataset or data. The tool will answer the question using PandasAI. The same user query that is asked to you should be passed to this tool. If the output contains image then grab the file path of the output image and return it in your response"""

    llm = OpenAI(api_token=OPENAI_API_KEY)

    global selected_table
    connector = SqliteConnector(config={
        "database" : "ufc_data.db",
        "table" : selected_table 
    })

    sdf = SmartDataframe(connector, config={"llm": llm, "enable_cache": False})

    result = sdf.chat(query)

    if not isinstance(result, str):
        result = str(result)

    file_path_match = re.search(r'(\/[^\s]+(?:\.png|\.jpg|\.jpeg|\.gif))', result)
    
    if file_path_match:
        result = file_path_match.group(0)

    return result


sql_tool = Tool(
    name="sql_tool",
    description="Use this tool when you need to analyze UFC data across multiple tables or perform complex SQL operations. This tool can handle questions about fighter statistics, match outcomes, historical UFC data, and relationships between different aspects of UFC fights. Pass the natural language query directly to this tool.",
    func=multi_table,
    args_schema=Pandasainput
)

pandas_tool = Tool(
    name="pandas_tool",
    description=f"A tool specialized for analyzing and visualizing UFC fight data from the currently selected table ({selected_table}). Use this for creating plots of fighter statistics, analyzing fight outcomes, or getting specific insights from individual UFC data tables. The tool can generate visualizations of fight data and perform statistical analysis. If a file path is returned then you should return the file path in your response. Assume that the required table is selected by the user prior to asking the question. Look at this variable to see if the table has changed: {selected_table}",
    func=pandasai_tool,
    args_schema=Pandasainput
)


tools = [pandas_tool, sql_tool]
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def is_valid_file_path(file_path):
    return os.path.isfile(file_path)


if "messages" not in st.session_state:
    st.session_state.messages = []


if "previous_table" not in st.session_state:
    st.session_state.previous_table = None

table_names = get_table_names()

if not selected_table and table_names:
    selected_table = table_names[0]

selected_table = st.sidebar.selectbox("Select a table to query", table_names, index=table_names.index(selected_table))

if st.session_state.previous_table != selected_table:

    st.session_state.messages.append({"role": "system", "content": f"Table changed to {selected_table}"})
    
    table_description = describe_table(selected_table)
    st.session_state.messages.append({"role": "system", "content": table_description, "visible": False})
    
    st.session_state.previous_table = selected_table

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center; color: #FF4B4B; padding: 20px 0; 
    border-bottom: 2px solid #FF4B4B; margin-bottom: 30px;'>
        TKO Analytics
    </h1>
    """, 
    unsafe_allow_html=True
)

st.markdown("""
    <p style='text-align: center; color: #666666; margin-bottom: 30px;'>
        Analyze and Visualize UFC Fight Data
    </p>
    """, 
    unsafe_allow_html=True
)


context_window_size = st.sidebar.slider("Context Window Size", 1, 10, 10)

for message in st.session_state.messages:
    if message.get("visible", True):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Type your message here..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    conversation_history = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-context_window_size:]]
    )

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        
        start_time = time.time()
        
        response = agent_executor.invoke(
            {"input": conversation_history}, {"callbacks": [st_callback]}
        )
        
        end_time = time.time()
        response_time = end_time - start_time

        response_content = response["output"]

        st.session_state.messages.append({"role": "assistant", "content": response_content})

        if is_valid_file_path(response_content):
            st.image(response_content)
        else:
            if any(is_valid_file_path(part) for part in response_content.split()):
                image_path = next(part for part in response_content.split() if is_valid_file_path(part))
                st.image(image_path)
            else:
                st.markdown(response_content)
        
        st.markdown(
            f'''
            <p style="font-size:10px;">
                Time Elapsed: {response_time:.2f}s &nbsp; || &nbsp;
                Context Window: {context_window_size} &nbsp; || &nbsp;
                Context Table: {selected_table}
            </p>
            ''',
            unsafe_allow_html=True
        )