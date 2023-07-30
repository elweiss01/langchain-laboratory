import os

import langchain
from dotenv import load_dotenv
from langchain.cache import InMemoryCache
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.question_answering.stuff_prompt import \
    CHAT_PROMPT as LG_PROMPT
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from app_prompt.git_book_prompt import GIT_BOOK_PROMPT
from app_prompt.tae_kim_prompt import TAE_KIM_PROMPT as TK_CHAT_PROMPT
from func_logger import configure_logging, log_output
from vectorstore import vectordb

# Initialize func_logger and load .env in CWD
configure_logging()
load_dotenv()

# Retrieve OpenAI API Key from .env file
openai_api_key = os.environ['OPENAI_API_KEY']

# When using Chat_Models the llm_cache will improve preformance
langchain.llm_cache = InMemoryCache()

# Initialize Memory Buffer for Conversation
memory = ConversationBufferMemory()

AVAILABLE_PROMPTS = ["LG_PROMPT - Gen Use",
                     "TK_CHAT_PROMPT",
                     "GIT_BOOK_PROMPT", ]

MODELS = ["gpt-3.5-turbo",
          "gpt-3.5-turbo-0613",
          "gpt-3.5-turbo-16k-0613",
          "gpt-4-0613",
          ]


@log_output(level='debug')
def get_query(model,
              query,
              collection_name,
              prompt="LG_PROMPT",
              k_value=4) -> str:
    llm = ChatOpenAI(streaming=True,
                     callbacks=[StreamingStdOutCallbackHandler()],
                     temperature=0,
                     openai_api_key=openai_api_key,
                     model=model,
                     )

    docsearch = vectordb_query(query, collection_name, k_value)
    response = chain_query(llm, query, docsearch, prompt)
    return response


@log_output(level='debug')
def vectordb_query(query, collection_name, k_value):
    db = vectordb(collection_name)
    docsearch = db.similarity_search(query, k=k_value)
    return docsearch


def prompt_selector(prompt):
    prompts = {"LG_PROMPT - Gen Use": LG_PROMPT,
               "TK_CHAT_PROMPT": TK_CHAT_PROMPT,
               "GIT_BOOK_PROMPT": GIT_BOOK_PROMPT,
               }
    if prompt not in prompts:
        raise ValueError(f"Invalid Prompt Name: {prompt}.")

    return prompts[prompt]


@log_output(level='debug')
def chain_query(llm, query, docsearch, prompt):
    prompt_template = prompt_selector(prompt)
    chain = load_qa_chain(llm, chain_type="stuff",
                          verbose=True,
                          prompt=prompt_template,
                          memory=memory,)

    return chain.run({"input_documents": docsearch, "question": query},)


if __name__ == "__main__":
    collection_name = input("Enter collection name of query: ")
    db = vectordb(collection_name)
    while True:
        query = input("What is your question? >>> ")
        docsearch = db.similarity_search(query=query, k=4)
        chain_query(llm=ChatOpenAI(streaming=True,
                                   callbacks=[StreamingStdOutCallbackHandler()],
                                   temperature=0,
                                   openai_api_key=openai_api_key),
                    query=query,
                    docsearch=docsearch,
                    prompt="LG_PROMPT - Gen Use")
