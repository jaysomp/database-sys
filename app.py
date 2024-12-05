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
        conn = sqlite3.connect('ufc_database.db')
        cursor = conn.cursor()
        
        # Query to get all table names in SQLite
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
        # Close the connection
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
        
        # Get schema information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Build the description
        description = [f"Table: {table_name}"]
        description.append(f"Schema:")
        
        # Column details
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


def pandasai_tool(query):
    """Use this tool when asked questions about a dataset or data. The tool will answer the question using PandasAI. The same user query that is asked to you should be passed to this tool. If the output contains image then grab the file path of the output image and return it in your response"""

    llm = OpenAI(api_token=OPENAI_API_KEY)

    global selected_table
    connector = SqliteConnector(config={
        "database" : "ufc_database.db",
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


pandas_tool = Tool(
    name="pandas_tool",
    description=f"A tool to use when answering questions about the data. The tool will be used to query the data as well as plotting information from the data. If a file path is returned then you should return the file path in your response. Assume that the required table is selected by the user prior to asking the question do not worry about it. Assume that the table is changing unless being asked a clear follow up question look at this variable as well to see of the table has changed {selected_table} ",
    func=pandasai_tool,
    args_schema=Pandasainput
)


tools = [pandas_tool]
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
    # Visible message about table change
    st.session_state.messages.append({"role": "system", "content": f"Table changed to {selected_table}"})
    
    # Hidden system message with table description
    table_description = describe_table(selected_table)
    st.session_state.messages.append({"role": "system", "content": table_description, "visible": False})
    
    st.session_state.previous_table = selected_table

st.sidebar.markdown("<br>", unsafe_allow_html=True)

context_window_size = st.sidebar.slider("Context Window Size", 1, 10, 10)

# Modified message display loop to skip hidden messages
for message in st.session_state.messages:
    if message.get("visible", True):  # Show message only if visible flag is True
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