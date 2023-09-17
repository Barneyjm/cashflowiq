import streamlit as st
import pandas as pd 
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from collections import Counter
import random

from langchain.agents import initialize_agent, AgentType, Tool, create_csv_agent
from langchain.memory import ConversationBufferMemory


NEW_CHAT_START = [{"role": "assistant", "content": "Upload your transactions file to the left and I'll get started!"}]
BUDGET_PROMPT = """
You're a friendly and talkative chatbot who is an expert at helping whoever talks to you analyze their spending habits. 
You're very accomodating to requests and want to help whoever talks to you save money while still enjoying their lifestyle. 
The person you're talking to can't see your thoughts so be sure to include any important or pertinent information within your thoughts in your final answer.
Format your responses in Markdown when it makes sense to do so.
"""
NEW_BUDGET = Counter({"total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_cost": 0
    })

LOADING_THOUGHTS = [
    "Calculating... CashFlowIQ is figuring out how to turn pennies into dollars 💰✨",
    "Hold onto your wallet... CashFlowIQ is counting virtual piggy bank coins 🐖🏦",
    "Loading... CashFlowIQ is learning to do the financial fandango 💃💸",
    "Just a moment... CashFlowIQ is auditing its virtual cookie jar 🍪💼",
    "Cha-ching! CashFlowIQ is deciphering the secret language of dollar bills 💵🔍",
    "Wait for it... CashFlowIQ is deciding between stocks and memes 📈🚀",
    "One sec... CashFlowIQ is negotiating with virtual financial gurus 🕊️💼",
    "Loading... CashFlowIQ is exploring the digital treasure map 🗺️💰",
    "Counting... CashFlowIQ is practicing its money magic tricks 🎩✨",
    "Hang in there... CashFlowIQ is budgeting for intergalactic vacations 🌌✈️"
]

def get_random_thought():
    return LOADING_THOUGHTS[random.randint(0, len(LOADING_THOUGHTS)-1)]
      

def new_chat():
    st.session_state["messages"] = NEW_CHAT_START

def add_assistant_response(response, cb=None):
    if cb:
        st.session_state["token_usage"] += parse_cb(cb)
    if response.startswith('st.'):
        eval(response) 
    else:
        msg = {"role": "assistant", "content": response}
        st.session_state.messages.append(msg)
        st.chat_message("assistant").write(msg["content"])
    

def add_user_prompt(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

def parse_cb(callback):
    return Counter({
        "total_tokens": callback.total_tokens,
        "prompt_tokens": callback.prompt_tokens,
        "completion_tokens": callback.completion_tokens,
        "total_cost": callback.total_cost
    })

if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []

if "conversation_memory" not in st.session_state:
    st.session_state["conversation_memory"] = ConversationBufferMemory(memory_key="chat_history")

if "token_usage" not in st.session_state: 
    st.session_state["token_usage"] = NEW_BUDGET
 

with st.sidebar:
    st.markdown("# CashFlowIQ")
    st.markdown("---")
    st.markdown("CashFlowIQ can analyze your personal finance transactions and help you save money!")
    # openai_api_key = st.sidebar.text_input("OpenAI API Key", key="chatbot_api_key", type="password", autocomplete="off")
    openai_api_key = st.secrets.openai.api_key
    uploaded = st.file_uploader("Upload Transactions")
    st.sidebar.button("New Chat", on_click=new_chat, type="primary")
    st.markdown("---")
    if "token_usage" in st.session_state:
        st.text_input(disabled=True, label="Total Tokens", value=st.session_state['token_usage'].get('total_tokens'))
        st.text_input(disabled=True, label="Prompt Tokens", value=st.session_state['token_usage'].get('prompt_tokens'))
        st.text_input(disabled=True, label="Completion Tokens", value=st.session_state['token_usage'].get('completion_tokens'))
        st.text_input(disabled=True, label="Total Cost (USD)", value="$"+str(st.session_state['token_usage'].get('total_cost')))
    st.sidebar.button("Refresh Token Data")


if uploaded is not None and "agent" not in st.session_state and openai_api_key:
    st.session_state["model_id"] = "gpt-4"
    st.session_state["llm"] = ChatOpenAI(model_name=st.session_state["model_id"], openai_api_key=openai_api_key, temperature=0)
    tools = []
    st.session_state["agent"] = create_csv_agent(
                path=uploaded,
                tools=tools,
                llm=st.session_state["llm"],
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=st.session_state["conversation_memory"],
                handle_parsing_errors=True,
                verbose=False, 
                max_iterations=5
            )

    add_assistant_response("Thanks for uploading that! I'll start crunching the numbers right away...", None)
    intial_prompts = [
        # "Describe the data in the file I just uploaded?",
        # "How many records are in the file I uploaded?",
        "What are my top 5 expense categories?",
        "What are my most common vendor transactions?",
        # "How has my spending in groceries changed over the year?",
        # "Are there any unusual or suspicious transactions in my accounts?",
        # "What are the columns in the file i uploaded?",
        # "Use the pandas df.describe() function on the dataframe and provide your thoughts and analysis in your final answer.",
        # "What's the total amount of money spent in the file i uploaded?",
        # "How much money do is spent in a typical month?"
        # "Generate a single line of python code not surrounded by quotes to draw a streamlit line chart using the object 'uploaded'. do not explain your response or ask about follow up questions. streamlit is already imported and available as 'st'. return only valid, executable python code that starts with the characters 'st.'. For example, here's a working line that your response should always look like: st.line_chart(pd.read_csv(uploaded), x=\"Date\", y=\"Amount\")"
    ]
    for prompt in intial_prompts:
        add_user_prompt(prompt)
        with st.spinner(text=get_random_thought()):
            with get_openai_callback() as cb:
                add_assistant_response(st.session_state["agent"].run(BUDGET_PROMPT + prompt), cb)
    outro = "Thanks! What are 3 other questions I should ask you about my transactions?"
    
    add_user_prompt(outro)
    with st.spinner(text=get_random_thought()):
        with get_openai_callback() as cb:
            add_assistant_response(st.session_state["agent"].run(BUDGET_PROMPT + outro), cb)

if "messages" not in st.session_state:
    st.session_state["messages"] = NEW_CHAT_START

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(disabled=uploaded is None):
    if not openai_api_key.startswith('sk-'):
        st.warning('Please enter your OpenAI API key!', icon='⚠')
    if uploaded is None:
        st.toast("Please upload your transactions file to use CashFlowIQ!")
    add_user_prompt(prompt)

    if uploaded is not None and "agent" in st.session_state:
        with st.spinner(text=get_random_thought()):
            with get_openai_callback() as cb:
                add_assistant_response(st.session_state["agent"].run(BUDGET_PROMPT + prompt), cb)


    