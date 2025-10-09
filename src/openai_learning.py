import os
import openai
from langchain_community.llms import OpenAI

# 需要导入openai和serp的API,like:
os.environ["OPENAI_API_KEY"] = "..."
os.environ["SERPAPI_API_KEY"] = "..."

# llm = OpenAI(temperature=0.9)
# text = "What would be a good company name for a company that makes colorful socks?"
# print(llm(text))

# from langchain.prompts import PromptTemplate
#
# prompt = PromptTemplate(
#     input_variables=["product"],
#     template="What is a good name for a company that makes {product}?",
# )
# print(prompt.format(product="colorful socks"))
#
# from langchain.chains import LLMChain
# chain = LLMChain(llm=llm, prompt=prompt)
# chain.run("colorful socks")


# from langchain.agents import load_tools
# from langchain.agents import initialize_agent
# from langchain.agents import AgentType
# from langchain.llms import OpenAI
#
# # First, let's load the language model we're going to use to control the agent.
# llm = OpenAI(temperature=0)
#
# # Next, let's load some tools to use. Note that the `llm-math` tool uses an LLM, so we need to pass that in.
# tools = load_tools(["serpapi", "llm-math"], llm=llm)
#
# # Finally, let's initialize an agent with the tools, the language model, and the type of agent we want to use.
# agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
#
# # Now let's test it out!
# agent.run("What was the high temperature in SF yesterday in Fahrenheit? What is that number raised to the .023 power?")


# from langchain import OpenAI, ConversationChain
# llm = OpenAI(temperature=0)
# conversation = ConversationChain(llm=llm, verbose=True)
# output = conversation.predict(input="can you speak chinese?")
# print(output)


# from langchain.chat_models import ChatOpenAI
# from langchain.schema import (
#     AIMessage,
#     HumanMessage,
#     SystemMessage
# )
# chat = ChatOpenAI(temperature=0)
# batch_messages = [
#     [
#         SystemMessage(content="You are a helpful assistant that translates English to Chinese."),
#         HumanMessage(content="Translate this sentence from English to Chinese. I love programming.")
#     ],
#     [
#         SystemMessage(content="You are a helpful assistant that translates English to Chinese."),
#         HumanMessage(content="Translate this sentence from English to Chinese. I love artificial intelligence.")
#     ],
# ]
# print(chat.generate(batch_messages))

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know."),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])
llm = ChatOpenAI(temperature=0)
memory = ConversationBufferMemory(return_messages=True)
conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm)
print(conversation.predict(input="Hi there!"))

# -> 'Hello! How can I assist you today?'
print(conversation.predict(input="I'm doing well! Just having a conversation with an AI."))

# -> "That sounds like fun! I'm happy to chat with you. Is there anything specific you'd like to talk about?"
print(conversation.predict(input="Tell me about yourself."))

# -> "Sure! I am an AI language model created by OpenAI. I was trained on a large dataset of text from the internet, which allows me to understand and generate human-like language. I can answer questions, provide information, and even have conversations like this one. Is there anything else you'd like to know about me?"