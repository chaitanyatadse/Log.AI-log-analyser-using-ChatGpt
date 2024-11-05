import os
import streamlit as st
import openai
import faiss
import numpy as np
from dotenv import load_dotenv
import PyPDF2
import docx
from openai import OpenAI
import re
from htmltemplates import css, bot_template, user_template
from collections import Counter

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

# Apply CSS styling
st.write(css, unsafe_allow_html=True)

def get_log_embeddings(logs):
    response = client.embeddings.create(
        input=logs,
        model="text-embedding-ada-002"
    )
    embeddings = [data.embedding for data in response.data]
    return embeddings

class LocalVectorStore:
    def __init__(self, dimension):
        self.index = faiss.IndexFlatL2(dimension)
        self.logs = []
        self.ids = []

    def add(self, embeddings, logs):
        embeddings = np.array(embeddings).astype('float32')
        assert embeddings.shape[1] == self.index.d, "Embedding dimension mismatch"
        self.index.add(embeddings)
        self.logs.extend(logs)
        self.ids.extend(range(len(self.logs) - len(logs), len(self.logs)))

    def search(self, query_embedding, top_k=5):
        distances, indices = self.index.search(np.array([query_embedding]).astype('float32'), top_k)
        return [(self.logs[i], distances[0][j]) for j, i in enumerate(indices[0])]

# Initialize the vector store with the embedding dimension
vector_store = LocalVectorStore(dimension=1536)

def read_file(file):
    """Read content from the uploaded file based on its type."""
    if file.name.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
    elif file.name.endswith('.log'):
        text = file.read().decode('utf-8')
    else:
        text = ""
    return text

def chat_with_gpt(messages):
    """Communicate with GPT-3.5-turbo."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during chat with GPT: {e}")
        return f"Error in processing your request: {str(e)}"

def add_emojis(issue, count):
    """Add emojis based on the count of occurrences."""
    if count > 5:
        return f"{issue} 😡 ({count} times occurred)"
    elif count > 3:
        return f"{issue} 😠 ({count} times occurred)"
    elif count > 1:
        return f"{issue} 😟 ({count} times occurred)"
    else:
        return f"{issue} 🙂 ({count} times occurred)"

# Streamlit App
st.title("Logs.AI")

# Session state initialization
if 'logs' not in st.session_state:
    st.session_state.logs = None
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Upload file section with file size limit check
st.markdown("<h3>Upload a file:</h3>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("", type=["pdf", "docx", "log", "txt"], help="Max file size: 100MB")
file_uploaded_successfully = False

if uploaded_file:
    # Convert size in bytes to MB
    file_size_MB = uploaded_file.size / (1024 * 1024)

    if file_size_MB > 100:
        st.error("File size exceeds 100MB. Please upload a smaller file.")
    else:
        with st.spinner("Processing..."):
            # Proceed with file processing if size is within the limit
            document_text = read_file(uploaded_file)
            if document_text:
                st.session_state.logs = document_text.splitlines()
                if not st.session_state.embeddings:
                    st.session_state.embeddings = get_log_embeddings(st.session_state.logs)
                
                # Add logs and embeddings to the local vector store
                vector_store.add(st.session_state.embeddings, st.session_state.logs)
                
                file_uploaded_successfully = True
            else:
                st.error("Upload only valid file format")

def display_query_input():
    st.markdown("<h3>Ask your Query:</h3>", unsafe_allow_html=True)
    query = st.text_input("", key=f"query_input_{len(st.session_state.query_history)}")
    if st.button("Generate", key=f"generate_button_{len(st.session_state.query_history)}"):
        if query:
            with st.spinner("Generating..."):
                if 'query_embeddings' not in st.session_state:
                    st.session_state.query_embeddings = {}
                
                if query not in st.session_state.query_embeddings:
                    query_embedding = get_log_embeddings([query])[0]
                    st.session_state.query_embeddings[query] = query_embedding
                else:
                    query_embedding = st.session_state.query_embeddings[query]

                # Check if the query is asking for the top n issues
                match = re.match(r'top (\d+) issues', query.lower())
                if match:
                    n = int(match.group(1))
                    log_counter = Counter(st.session_state.logs)
                    top_issues = log_counter.most_common(n)
                    top_issues_with_emojis = [add_emojis(issue, count) for issue, count in top_issues]
                    response = f"Top {n} Issues:\n\n" + "\n\n".join(top_issues_with_emojis)
                else:
                    # Search the logs
                    results = vector_store.search(query_embedding, top_k=5)
                    
                    # Prepare messages for GPT-3.5-turbo
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": f"Analyze the following logs and answer the query: {query}"},
                        {"role": "user", "content": "\n".join([log for log, _ in results])}
                    ]

                    # Get response from GPT-3.5-turbo
                    response = chat_with_gpt(messages)
                
                st.session_state.query_history.append((query, response))
                st.write(user_template.replace("{{MSG}}", query), unsafe_allow_html=True)
                st.write(bot_template.replace("{{MSG}}", response), unsafe_allow_html=True)
                display_query_input()

# Query the logs
if st.session_state.logs is not None and st.session_state.embeddings is not None:
    display_query_input()

    # Display previous queries and responses
    if st.session_state.query_history:
        st.write("")
        st.write("")
        st.write("### History")
        for i, (query, response) in enumerate(st.session_state.query_history):
            st.write(user_template.replace("{{MSG}}", query), unsafe_allow_html=True)
            st.write(bot_template.replace("{{MSG}}", response), unsafe_allow_html=True)
