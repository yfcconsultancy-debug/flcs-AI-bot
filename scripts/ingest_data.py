import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
# Corrected import for loaders
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
# Corrected import for text_splitter needed update later
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore

# Build the path to the .env file (two directories up from 'scripts')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')

# Load the .env file from that specific path
load_dotenv(dotenv_path=dotenv_path)

# Initialize Pinecone
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

# Initialize Cohere Embeddings Model
print("Initializing Cohere Embeddings...")
cohere_api_key = os.environ.get("COHERE_API_KEY")
if not cohere_api_key:
    print("CRITICAL ERROR: COHERE_API_KEY not found. Check your .env file.")
    exit(1)
try:
    embeddings_model = CohereEmbeddings(
        cohere_api_key=cohere_api_key,
        model="embed-english-v3.0" # Must match core.py
    )
    print("Cohere Embeddings initialized.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Cohere Embeddings: {e}")
    traceback.print_exc()
    exit(1)

# Define index name
index_name = "flcs-chatbot"

# Check if index exists, create if not
if index_name not in pc.list_indexes().names():
    print(f"Creating index '{index_name}'...")
    pc.create_index(
        name=index_name,
        dimension=1024, # Dimension for all-MiniLM-L6-v2
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print("Index created.")
else:
    print(f"Index '{index_name}' already exists.")

# Point to data directory
DATA_PATH = os.path.join(BASE_DIR, "data/") # Use BASE_DIR for robustness
loader = DirectoryLoader(DATA_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True)

# Load documents
print("Loading documents...")
documents = loader.load()
if not documents:
    print(f"No PDF documents found in {DATA_PATH}. Exiting.")
    exit()
print(f"Loaded {len(documents)} documents.")

# Split documents
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = text_splitter.split_documents(documents)
print(f"Split documents into {len(chunks)} chunks.")

# Embed and upload to Pinecone
print("Embedding chunks and uploading to Pinecone...")
PineconeVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings_model,
    index_name=index_name
)
print("Data ingestion complete!")
