import streamlit as st
import requests
import json
import base64
from PIL import Image
import io

# Set page configuration
st.set_page_config(
    page_title="Qwen2.5 VL Assistant", 
    page_icon="🤖",
    layout="wide"
)

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# App title and description
st.title("🤖 Qwen2.5 VL 72B Chatbot")
st.markdown("""
This application uses OpenRouter to access the Qwen2.5 VL 72B Instruct model.
Upload images and chat with the multimodal AI assistant!
""")

# Sidebar for API key input
with st.sidebar:
    st.header("Configuration")
    
    # API key input
    api_key = st.text_input("Enter your OpenRouter API Key:", 
                           value=st.session_state.api_key,
                           type="password",
                           help="Get your API key from https://openrouter.ai/")
    
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
    
    st.markdown("---")
    #st.markdown("### About")
    #st.markdown("""
    #- Qwen2.5 VL 72B is a multimodal model that can understand both text and images
    #- OpenRouter provides access to this model through their API
    #- Images are encoded in base64 format for API transmission
    #""")
    
    # Clear chat button
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# Function to encode image to base64
def encode_image(uploaded_file):
    if uploaded_file is not None:
        # Read the file and encode it
        bytes_data = uploaded_file.getvalue()
        base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
        return base64_encoded
    return None

# Function to make API call to OpenRouter
def generate_response(messages):
    if not st.session_state.api_key:
        st.error("Please enter an OpenRouter API key in the sidebar")
        return "Error: API key is required"
    
    headers = {
        "Authorization": f"Bearer {st.session_state.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen/qwen2.5-vl-72b-instruct",
        "messages": messages,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"Error {response.status_code}: {response.text}")
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        st.error(f"Exception occurred: {str(e)}")
        return f"Error: {str(e)}"

# Display chat messages
st.markdown("### Conversation")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user" and "image" in message:
            # Display the image
            st.image(message["image"], caption="Uploaded Image")
            st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# File uploader for images
uploaded_file = st.file_uploader("Upload an image to discuss with the model", type=["jpg", "jpeg", "png"])
image_placeholder = None

if uploaded_file:
    image = Image.open(uploaded_file)
    image_placeholder = st.image(image, caption="Preview of uploaded image")

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Hide image preview after sending
    if image_placeholder:
        image_placeholder.empty()
    
    # Add user message to chat history
    user_message = {"role": "user", "content": user_input}
    
    # If an image was uploaded, encode it and add to the message
    if uploaded_file:
        base64_image = encode_image(uploaded_file)
        
        # Save image to display in chat history
        user_message["image"] = uploaded_file
        
        # Format message for API with image
        api_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_input},
                {"type": "image_url", 
                 "image_url": {"url": f"data:image/{uploaded_file.type.split('/')[1]};base64,{base64_image}"}}
            ]
        }
    else:
        # Text-only message for API
        api_message = {"role": "user", "content": user_input}
    
    # Add user message to the chat history
    st.session_state.messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        if "image" in user_message:
            st.image(user_message["image"], caption="Uploaded Image")
        st.markdown(user_input)
    
    # Get API-formatted message history
    api_messages = []
    for msg in st.session_state.messages[:-1]:  # Exclude the message we just added
        if msg["role"] == "user" and "image" in msg:
            # This is a message with an image, we need to reconstruct it for the API
            # We're skipping this for simplicity as we'd need to re-encode old images
            # In a production app, you'd store the base64 encoded images
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        else:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add the new message with image if present
    api_messages.append(api_message)
    
    # Get response from OpenRouter API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(api_messages)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Clear the file uploader
    uploaded_file = None

# Instruction footer
st.markdown("---")
st.caption("Enter your message and optionally upload an image to interact with Qwen2.5 VL 72B Instruct model.")
