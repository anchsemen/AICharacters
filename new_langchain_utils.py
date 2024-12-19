import os
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain.docstore.document import Document

from db import load_history_from_db, save_message_to_db, load_other_history_from_db
from utils import crop_message


async def summary_conversation(user_id: int, llm):
    history = load_other_history_from_db(user_id)

    text_splitter = RecursiveCharacterTextSplitter()

    conversation = "\n".join(f'{"Mia" if msg["sender"] == "ai" else "User"}: {msg["content"]}' for msg in history)

    texts = text_splitter.split_text(conversation)
    docs = [Document(page_content=t) for t in texts]

    chain = load_summarize_chain(llm, chain_type="map_reduce")
    summary = chain.run(docs)
    return summary


async def load_history_to_state(user_id):
    history = load_history_from_db(user_id)
    messages = []
    for message, sender in history:
        if sender == "user":
            messages.append(HumanMessage(content=message))
        elif sender == "ai":
            messages.append(AIMessage(content=message))
    return MessagesState(messages=messages)


async def run_llm(user_id: int, query: str):
    save_message_to_db(user_id, query, "user")

    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        model_name="gryphe/mythomax-l2-13b",
        max_tokens=150
    )

    # llm = ChatOpenAI(
    #     model='gpt-4o-mini',
    #     openai_api_key=os.environ["OPENAI_API_KEY"])

    SUMMARY = await summary_conversation(user_id, llm)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                f"You're a girl, and your name is Officer Mia. You are a sexy police officer who relies on her intuition. Situation: You stopped a user in a car for speeding, asked him to get out of the car and began to search him sexually. Describe the situation, what you see and what you do with the user, what punishments you have come up with for him and how you will tease him. You dominate the user. You work for the police, and the user is just a human being. Your answer consists of a description of the situation - you write it in ** -1 sentence. And then your answer is 2-3 sentences. The response length should not exceed **150 characters**, including spaces and punctuation marks. Answer in the first person and use the constructions 'I do...'. Use simple speech, as when posting porn in a messenger. You are a girl communicating with a man, responding in the first person of a girl, not from a man. You are ready to flirt, communicate on various topics, especially sexual ones. If the dialogue is about sex, then continue the topic of sex. The following is a summary of your previous conversation. Please continue the dialogue according to the context given in this summary: {SUMMARY} Write a short and concise response to the man's last message, taking into account the context of your communication. Use a modern conversational style. Keep in mind that you communicate via messenger."
            ),
            MessagesPlaceholder(variable_name="messages")
        ]
    )
    runnable = prompt_template | llm

    def call_model(state: MessagesState):
        response = runnable.invoke(state)
        return {"messages": [response]}

    workflow = StateGraph(state_schema=MessagesState)
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    memory = MemorySaver()
    config = {"configurable": {"thread_id": user_id}}

    app = workflow.compile(checkpointer=memory)
    current_state = await load_history_to_state(user_id)

    app.update_state(config, current_state)
    output = app.invoke({"messages": [HumanMessage(content=query)]}, config)
    result = await crop_message(output["messages"][-1].content)
    save_message_to_db(user_id, result, "ai")
    return result
