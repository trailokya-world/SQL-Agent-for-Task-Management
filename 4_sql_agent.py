from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit



username = "root"
password = "trailokya"
host = "localhost"
port = "3306"
database = "My_Tasks"
db_uri = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"


try:
    db = SQLDatabase.from_uri(db_uri)

    db.run("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(100) NOT NULL,
        description VARCHAR(100),
        status VARCHAR(20)
            CHECK (status IN ('pending', 'inprogress', 'completed'))
            DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # print("Database connected successfully!")
    # print(db.get_usable_table_names())

except Exception as e:
    print("Error:", e)



model = ChatGroq(model="openai/gpt-oss-20b")
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()



# memory = MemorySaver()
system_prompt = """

You are TaskBot, an AI assistant connected to a MySQL database.

You MUST use the SQL database tools whenever the user asks about tasks.

Available table:

tasks(id, title, description, status, created_at)

Rules:

1. For any task-related request, use the SQL tools first.

2. Never answer with generic help text if the user asks for data.

3. After INSERT, UPDATE, or DELETE, run a SELECT query to verify the change.

4. Limit SELECT results to 10 rows unless the user asks for more.

5. Order task lists by created_at DESC.

6. Present task lists in a clean markdown table.

7. Use only the existing schema; do not invent columns or tables.

8. If the user says "all tasks", execute:

SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10;

9. If the user says "add task X", execute an INSERT query.

10. If the user says "complete task X", execute an UPDATE query.

11. If the user says "delete task X", execute a DELETE query.

12. Do not ask what the user wants if the intent is already clear.

Examples:

User: "give me all tasks"

Action: Use SQL tool to fetch tasks.

User: "add task apply for Microsoft"

Action: Insert the task into the database.

User: "mark task 3 as completed"

Action: Update the status of task 3.

"""

@st.cache_resource
def get_agent():
    agent = create_agent(
        model=model,
        tools=tools,
        checkpointer=InMemorySaver(),
        system_prompt=system_prompt
    )
    return agent

agent = get_agent()

st.subheader("📜 TaskBot - Manage Your Tasks")

if "messages" not in st.session_state:
    st.session_state.messages = []
    
for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])

prompt = st.chat_input("Ask me to manage your task")

if prompt:
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user", "content":prompt})
    
    
    
    with st.chat_message("AI"):
        with st.spinner("processing..."):
            
            response = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            {"configurable": {"thread_id": "1"}}
            )
            
            result = response["messages"][-1].content
            
            st.markdown(result)
            
            st.session_state.messages.append({"role":"ai", "content":result})
 

        
    
    







































# print(db.run(" describe tasks"))


# print(db.run("SHOW TABLES;"))