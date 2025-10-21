import os
import traceback
from dotenv import load_dotenv
from pinecone import Pinecone
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pydantic import SecretStr

print("\n--- LOADING CHATBOT CORE MODULE ---")

# --- Path and Environment Variable Loading ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(BASE_DIR, '.env')

if not os.path.exists(dotenv_path):
    print(f"CRITICAL WARNING: .env file not found at {dotenv_path}. API connections will fail.")
load_dotenv(dotenv_path=dotenv_path)
print(f".env file check complete. Attempting to load vars.")

# --- Global Variables for Initialization Status ---
llm = None
vectorstore = None
qa_chain = None
initialization_error = None

print("\n--- STARTING CHATBOT CORE INITIALIZATION ---")

try:
    # 1. Initialize Groq LLM
    print("[Core Init 1/4] Initializing Groq LLM...")
    groq_api_key_str = os.environ.get("GROQ_API_KEY")
    if not groq_api_key_str:
        raise ValueError("GROQ_API_KEY not found in environment.")
    llm = ChatGroq(
        # Use SecretStr for better practice, though str might work depending on library version
        api_key=SecretStr(groq_api_key_str),
        model="llama-3.1-8b-instant" # Verify model availability on Groq
    )
    print("[Core Init 1/4] Groq LLM initialized.")

# 2. Initialize the "Converter" (Cohere Embeddings API)
    print("[Core Init Step 2/4] Initializing Cohere Embeddings...")
    cohere_api_key = os.environ.get("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY not found in environment. Add it to .env or Vercel vars.")
    # Use a Cohere embedding model (e.g., 'embed-english-v3.0')
    embeddings_model = CohereEmbeddings( # <-- MUST BE CohereEmbeddings
        cohere_api_key=cohere_api_key,
        model="embed-english-v3.0" # Or your chosen Cohere model
    )
    print("[Core Init Step 2/4] Cohere Embeddings initialized.")

    # 3. Initialize Pinecone Connection
    print("[Core Init 3/4] Connecting to Pinecone...")
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY not found in environment.")
    pc = Pinecone(api_key=pinecone_api_key)
    index_name = "flcs-chatbot"

    print(f"[Core Init 3/4] Checking if index '{index_name}' exists...")
    index_list_obj = pc.list_indexes()
    if index_name not in index_list_obj.names():
        raise ValueError(f"Pinecone index '{index_name}' does not exist. Run ingest script first.")
    print(f"[Core Init 3/4] Index '{index_name}' found. Connecting VectorStore...")
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings_model
        # namespace="your-namespace" # Optional
    )
    print("[Core Init 3/4] Connected to Pinecone index via VectorStore.")

    # 4. Setup Prompt and QA Chain
    print("[Core Init 4/4] Setting up Prompt Template and QA Chain...")

# Define a specific prompt template with Markdown instructions
    prompt_template = """You are an expert student counselor AI assistant for FLCS Consultancy, specializing ONLY in helping students study in Italy. Your knowledge comes *exclusively* from the official FLCS documents provided below in the 'Context' section.

    **Special Instructions for Greetings/Simple Interactions:**
    - If the user's input is a simple greeting, closing, or unrelated question, provide a brief, polite, standard conversational response (e.g., "Hello! How can I help you regarding studying in Italy?"). Do NOT search the context for these.

    **Instructions for Genuine Queries about Studying in Italy:**
    1.  Carefully analyze the user's 'Question'.
    2.  Base your *entire* answer *only* on the relevant text provided in the 'Context' section below.
    3.  If the context contains the answer, synthesize a helpful, comprehensive, and well-structured response.
    4.  **Formatting:**
        * **Use Markdown:** Employ standard Markdown for formatting (bolding `**like this**`, bullet points using `-` or `*`, numbered lists using `1.`, `2.`).
        * **Structure:** Break down information into logical paragraphs. Use bullet points or numbered lists for steps, requirements, or lists of items.
        * **Clarity:** Ensure the answer is easy to read and understand.
    5.  If the context does *not* contain the answer, *clearly* state: "Based on the provided FLCS documents, I don't have specific information about that topic."
    6.  Do NOT use any prior knowledge or information from outside the provided context. Do NOT make up answers.
    7.  Maintain the helpful and professional persona of an FLCS counselor.

    Context:
    {context}

    Question: {question}

    Helpful Answer (using Markdown formatting based *only* on FLCS documents provided, unless it's a simple greeting):"""

    QA_CHAIN_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_template,
    )

    retriever = vectorstore.as_retriever(search_kwargs={'k': 3}) # Retrieve top 3 chunks

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
        return_source_documents=False
    )
    print("[Core Init 4/4] RetrievalQA chain ready.")
    print("\n--- CHATBOT CORE INITIALIZED SUCCESSFULLY ---\n")

except Exception as e:
    initialization_error = e
    print(f"\n--- FATAL ERROR DURING CHATBOT CORE INITIALIZATION ---")
    traceback.print_exc()
    print(f"--- END OF INITIALIZATION ERROR ---")
    print("--- The chatbot will respond with an error message until this is fixed. ---")


# --- Chatbot Function ---
# --- Chatbot Function (Called by the API route) ---
def get_bot_response(query: str) -> str:
    """
    Processes a user query using the initialized RAG chain,
    handling simple greetings separately.
    """
    # --- ADD GREETING CHECK HERE ---
    simple_greetings = ["hi", "hello", "hey", "hii", "heyy", "yo", "greetings"]
    simple_closings = ["bye", "goodbye", "thanks", "thank you", "ok", "okay"]
    normalized_query = query.lower().strip().strip("!?.") # Clean up the query

    if normalized_query in simple_greetings:
        print("[Greeting Check] Detected simple greeting, returning standard response.")
        return "Hello! How can I assist you with your plans to study in Italy today?"
    if normalized_query in simple_closings:
         print("[Greeting Check] Detected simple closing, returning standard response.")
         return "You're welcome! Feel free to ask if you have more questions."
    # --- END GREETING CHECK ---

    # Check if the initialization failed earlier
    if not qa_chain:
        # ... (rest of the error handling remains the same) ...
        error_message = "Sorry, the chatbot system encountered an error during startup and is not available."
        if initialization_error:
             print(f"ERROR: get_bot_response called, but qa_chain is None due to startup error: {initialization_error}")
        else:
             print("ERROR: get_bot_response called, but qa_chain is None (reason unknown).")
        return error_message

    print(f"\n[API Request] Processing query: '{query}'")
    try:
        # === CORE LOGIC: Invoke the RAG chain ===
        # This part is now only reached if it's NOT a simple greeting
        response = qa_chain.invoke({"query": query})
        # ========================================

        # ... (rest of the function remains the same) ...
        result = response.get("result", "Sorry, I couldn't formulate a response based on the available documents.")
        print(f"[API Response] Generated response length: {len(result)}")
        return result

    except Exception as e:
        # ... (rest of the error handling remains the same) ...
        print(f"\n--- ERROR INVOKING QA CHAIN ---")
        traceback.print_exc()
        print(f"--- END OF QA CHAIN ERROR ---")
        return "Sorry, an unexpected error occurred while processing your request. Please try again."