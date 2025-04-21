"""
OpenAI Integration Module for San Jose Safe Commute App
Provides unified OpenAI client initialization and handling
"""

import os
import logging
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openai_integration")

# Load environment variables
load_dotenv()

# Global OpenAI client instance
_client = None

def initialize_openai_client():
    """
    Initialize the OpenAI client instance with proper error handling.
    Creates a single global instance to be reused.
    """
    global _client
    
    # Check if we already have a valid client instance
    if _client is not None:
        return _client
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OpenAI API key not found in environment variables")
        if st:
            st.warning("OpenAI API key not found. Using simulated AI responses.")
        return None
    
    try:
        # Create the simplest client with just the API key, no extra parameters
        _client = OpenAI(api_key=api_key)
        
        # Validate client has expected attributes
        if not hasattr(_client, 'chat') or not hasattr(_client.chat, 'completions'):
            raise AttributeError("OpenAI client missing required attributes")
            
        logger.info("OpenAI client initialized successfully")
        return _client
    except Exception as e:
        # Log the error to console but don't display in the UI
        logger.error(f"Error creating OpenAI client: {str(e)}")
        # Don't show error in UI - just return None to use fallback
        return None

def get_completion(prompt, model="gpt-4o", temperature=0.7, max_tokens=500):
    """
    Get completion from OpenAI API with proper error handling.
    
    Args:
        prompt: The text prompt to send to OpenAI
        model: OpenAI model to use
        temperature: Controls randomness (0-1)
        max_tokens: Maximum length of response
        
    Returns:
        String containing the AI-generated text or error message
    """
    client = initialize_openai_client()
    
    # Handle case where client initialization failed
    if not client:
        return f"Unable to generate AI response: OpenAI client initialization failed."
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error generating completion: {str(e)}"
        logger.error(error_msg)
        return f"Unable to generate AI response: {str(e)}"

def get_chat_completion(messages, model="gpt-4o", temperature=0.7, max_tokens=500):
    """
    Get chat completion from OpenAI API with proper error handling.
    
    Args:
        messages: List of message objects with role and content
        model: OpenAI model to use
        temperature: Controls randomness (0-1)
        max_tokens: Maximum length of response
        
    Returns:
        String containing the AI-generated response or error message
    """
    client = initialize_openai_client()
    
    # Handle case where client initialization failed
    if not client:
        return f"Unable to generate AI response: OpenAI client initialization failed."
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error generating chat completion: {str(e)}"
        logger.error(error_msg)
        return f"Unable to generate AI chat response: {str(e)}"
