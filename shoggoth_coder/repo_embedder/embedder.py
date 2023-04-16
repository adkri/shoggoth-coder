import chromadb
import openai
import os
import tiktoken

from chromadb.config import Settings
from pathlib import Path
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_not_exception_type
from shoggoth_coder.repo_embedder.metadata_extractors.extractor import get_metadata_extractor, metadata_to_amalgamation

OPENAI_KEY = os.environ.get('OPENAI_API_KEY')

# Set up OpenAI API
openai.api_key = OPENAI_KEY

EMBEDDING_MODEL = 'text-embedding-ada-002'
EMBEDDING_CTX_LENGTH = 8191
EMBEDDING_ENCODING = 'cl100k_base'

SUPPORTED_LANGUAGES = ['py', 'js']

def truncate_text_tokens(text, encoding_name=EMBEDDING_ENCODING, max_tokens=EMBEDDING_CTX_LENGTH):
    """Truncate a string to have `max_tokens` according to the given encoding."""
    encoding = tiktoken.get_encoding(encoding_name)
    return encoding.encode(text)[:max_tokens]

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6), retry=retry_if_not_exception_type(openai.InvalidRequestError))
def generate_embeddings(text_or_tokens, model=EMBEDDING_MODEL):
    return openai.Embedding.create(input=text_or_tokens, model=model)["data"][0]["embedding"]


def create_repo_embedding(repo_name, repo_path):
    # setup chroma dir
    repo_embedding_cache_dir = f"./.cache/chroma-embeddings-{repo_name}" 

    # Set up ChromaDB client and collection
    chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet",
    persist_directory=repo_embedding_cache_dir))
    collection = chroma_client.get_or_create_collection(name=repo_name)

    indexed_data = []

    all_files = Path(repo_path).rglob("*")
    for file in all_files:
        file_path = str(file)
        file_ext = os.path.splitext(file_path)[1][1:]
        file_name = file_path.split(os.sep)[-1]
        file_path_key = os.sep.join(file_path.split(os.sep)[2:])

        try:
            metadata_extractor = get_metadata_extractor(file_ext)
        except ValueError:
            continue # skip unsupported files

        # Read the code from the file
        with open(file_path, "r", encoding="utf-8") as source:
            code = source.read()
        if code == "":
            print(f"Skipping {file_name} as it is empty")
            continue

        metadata = metadata_extractor.extract_metadata(file_path)
        metadata_str = f"##{file_name}({file_path_key})\n{metadata_to_amalgamation(metadata)}"

        indexed_data.append((None, code, file_name, metadata_str, file_path_key))

    chunked_indexes = []
    for i in range(0, len(indexed_data), 5):
        chunked_indexes.append(indexed_data[i:i+5])

    for chunk in chunked_indexes:
        combined_code = '\n\n'.join([code for _, code, _, _, _ in chunk])
        combined_metadata_amal = '\n\n'.join([metadata for _, _, _, metadata, _ in chunk])
        combined_file_name = ':'.join([file_name for _, _, file_name, _, _ in chunk])

        existing = collection.get(ids=[combined_file_name])
        if len(existing["ids"]) != 0:
            print(f"Skipping {combined_file_name} as it already exists in ChromaDB collection")
            continue


        print(f"Generation embedding for combined files {combined_file_name}")
        # Generate embeddings for the code
        truncated_code = truncate_text_tokens(combined_code)
        embeddings = generate_embeddings(truncated_code)
        # print(embeddings)
        # print(f"The combined metadata is {combined_metadata_amal}")

        collection.add(
            embeddings=[embeddings],
            documents=[combined_code],
            metadatas=[{"metadata_amal" : combined_metadata_amal}],
            ids=[combined_file_name]
        )
    chroma_client.persist()


def search_repo_embeddings(query, repo_name):
    # Set up ChromaDB client and collection
    repo_embedding_cache_dir = f"./.cache/chroma-embeddings-{repo_name}" 
    chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet",
    persist_directory=repo_embedding_cache_dir))
    collection = chroma_client.get_or_create_collection(name=repo_name)

    # Generate embeddings for the code
    embeddings = generate_embeddings(query)
    cnt = collection.count()
    n_results = min(cnt, 3)
    result = collection.query(query_embeddings=[embeddings], n_results=n_results)
    res_metadatas = result["metadatas"] [0]
    metadata_amal = [item["metadata_amal"] for item in res_metadatas]
    return "\n".join(metadata_amal)


def debug_search(repo_name):
    while True:
        print("Enter a query to search for")
        user_query = input("> ")

        result = search_repo_embeddings(user_query, repo_name)
        print(f"The metadata amalgamation is \n{result}")

def debug_create_repo_embedding(repo_name):
    create_repo_embedding(repo_name, f".cache/repo/{repo_name}")

    # repo_embedding_cache_dir = f"./.cache/chroma-embeddings-{repo_name}" 
    # Set up ChromaDB client and collection
    # chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet",
    # persist_directory=repo_embedding_cache_dir))
    # # collection = chroma_client.get_or_create_collection(name=repo_name)

if __name__ == "__main__":
    ## debugging code
    repo_name = "repo-name"
    debug_search(repo_name)
   