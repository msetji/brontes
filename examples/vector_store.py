from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document


CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/postgres"

COLLECTION_NAME = "embeddings"

embeddings = OpenAIEmbeddings()


store = PGVector(
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    embedding_function=embeddings,
    use_jsonb=True
)

# store.add_documents([Document(page_content="AHU 1 is a 1000 ton unit. AHU 2 is a 2000 ton unit. AHU 3 is a 3000 ton unit. AHU 4 is a 4000 ton unit. AHU 5 is a 5000 ton unit. AHU 6 is a 6000 ton unit. AHU 7 is a 7000 ton unit. AHU 8 is a 8000 ton unit. AHU 9 is a 9000 ton unit. AHU 10 is a 10000 ton unit. AHU 11 is a 11000 ton unit. AHU 12 is a 12000 ton unit. AHU 13 is a 13000 ton unit. AHU 14 is a 14000 ton unit. AHU 15 is a 15000 ton unit. AHU 16 is a 16000 ton unit. AHU 17 is a 17000 ton unit. AHU 18 is a 18000 ton unit. AHU 19 is a 19000 ton unit. AHU 20 is a 20000 ton unit. AHU 21 is a 21000 ton unit. AHU 22 is a 22000 ton unit. AHU 23 is a 23000 ton unit. AHU 24 is a 24000 ton unit. AHU 25 is a 25000 ton unit. AHU 26 is a 26000 ton unit. AHU 27 is a 27000 ton unit. AHU 28 is a 28000 ton unit. AHU 29 is a 29000 ton unit. AHU 30 is a 30000 ton unit. AHU 31 is a 31000 ton unit. AHU 32 is a 32000 ton unit. AHU 33 is a 33000 ton unit. AHU 34 is a 34000 ton unit. AHU 35 is a 35000 ton unit. AHU 36 is a 36000 ton unit. AHU 37 is a 37000 ton unit. AHU 38 is a 38000 ton unit. AHU 39 is a 39000 ton unit. AHU 40 is a 40000 ton unit. AHU 41 is a 41000 ton unit. AHU 42 is a 42000 ton unit. AHU")])



docs = store.similarity_search_with_score("AHU 1")


print(docs)


