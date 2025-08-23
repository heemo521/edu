"""AI tutoring engine integration.

This module integrates with a locally running LLM via the Ollama API to generate
responses to user queries. If the Ollama service is unreachable or returns an
error, the module falls back to a simple heuristic-based reply to ensure the
application continues to respond gracefully.
"""

import os
import requests


# Base URL for the local Ollama API. The default points to the standard Ollama
# endpoint on localhost; override via the OLLAMA_BASE_URL environment variable
# if necessary (e.g. when running the model on a different host or port).
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# Name of the model to use. You can override this via the LLAMA_MODEL
# environment variable (e.g. "llama3", "llama2", "mistral").
LLAMA_MODEL = os.environ.get("LLAMA_MODEL", "llama3")

# System prompt used to steer the language model toward effective tutoring behavior.
# The prompt instructs the model to act as a Socratic tutor: ask clarifying questions,
# provide hints rather than direct answers, adapt to different subjects, and solicit
# feedback to improve the interaction.  Adjust this prompt to refine the tutor's
# tone and strategy.
SYSTEM_PROMPT = (
    "You are a helpful AI tutoring assistant. Your role is to guide students through learning "
    "topics by asking questions and helping them reason step by step rather than giving direct "
    "answers. When answering, first identify the subject (e.g., Algebra, Biology, Programming) "
    "and adapt your guidance accordingly. Provide hints and suggest key concepts from the "
    "relevant topic. Encourage the student to recall prior knowledge. After providing guidance, "
    "ask the student if the explanation was helpful and request feedback or a brief summary in "
    "their own words. This will help improve future lessons."
)


def _call_ollama(prompt: str) -> str:
    """Call the local Ollama API to generate a response.

    Args:
        prompt: The user's input or question.

    Returns:
        A string containing the generated response from the model.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": LLAMA_MODEL,
        "prompt": prompt,
        # disable streaming for simplicity; a streaming implementation could
        # iterate over the response chunks and build the reply progressively
        "stream": False,
    }
    # Use a reasonable timeout to prevent hanging on network issues
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # According to the Ollama API spec, the generated text is under the "response" key
    return data.get("response", "").strip()


def get_tutor_response(message: str) -> str:
    """Generate a response to a student's message using a local LLM.

    This function attempts to call the Ollama API to obtain a response from
    a locally hosted language model. If the API call fails for any reason,
    it falls back to a basic heuristic that encourages the student to think
    critically.

    Args:
        message: The student's input or question.

    Returns:
        A string containing the AI tutor's reply.
    """
    try:
        # Compose the prompt by prepending the system instructions to the student's message.
        # This helps the model understand its role and how to structure the reply.
        prompt = f"{SYSTEM_PROMPT}\n\nStudent: {message}\nTutor:"
        return _call_ollama(prompt)
    except Exception:
        # Fall back to a simple heuristic-based reply if the LLM call fails
        trimmed = message.strip()
        if trimmed.endswith("?"):
            return (
                "That's a great question! Let's break it down together. "
                "What do you think is the first step to solving it?"
            )
        return (
            "I see. Let's explore that. Can you explain how you arrived at this point? "
            "I'll guide you through the next steps."
        )