# gemini_connection.py
# Purpose: create the Gemini model (through LangChain) and provide one safe
# function for sending messages to it.
#
# Every other file that needs Gemini imports from here:
#     from agent import gemini_connection
#     reply_text = gemini_connection.ask_gemini(messages)
#
# The API key is read from .env (via config.py) and never leaves the backend.

from langchain_google_genai import ChatGoogleGenerativeAI

from config import config
from utils.logger import get_logger

# ChatGoogleGenerativeAI: LangChain's wrapper around Google's Gemini models.

logger = get_logger("gemini_connection")

# One shared model object, created on first use.
_gemini_model = None


class GeminiError(Exception):
    """
    Raised when Gemini cannot be used. The message is SAFE to show to the
    user: it never contains the API key or technical details.
    """
    pass


def get_gemini_model():
    """Create the Gemini chat model once and reuse it afterwards."""
    global _gemini_model

    if _gemini_model is not None:
        return _gemini_model

    if config.GOOGLE_API_KEY == "" or config.GOOGLE_API_KEY == "your_gemini_api_key":
        logger.error("GOOGLE_API_KEY is missing in .env")
        raise GeminiError("The AI service is not configured. Please set the API key in the backend settings.")

    if config.GEMINI_MODEL == "" or config.GEMINI_MODEL == "your_supported_gemini_model":
        logger.error("GEMINI_MODEL is missing in .env")
        raise GeminiError("The AI model name is not configured in the backend settings.")

    _gemini_model = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
        temperature=config.GEMINI_TEMPERATURE,
        timeout=config.GEMINI_TIMEOUT_SECONDS,
        max_retries=2,
    )
    logger.info("Gemini model created: " + config.GEMINI_MODEL)
    return _gemini_model


def get_text_from_response(response_message):
    """
    Extract plain text from the model's reply.

    The reply's .content is usually a string, but some Gemini models return
    a LIST of content blocks such as:
        [{"type": "text", "text": "Hello"}, ...]
    This function handles both shapes.
    """
    content = response_message.content

    if isinstance(content, str):
        return content.strip()

    text_parts = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(block["text"])

    return "".join(text_parts).strip()


def translate_error_to_safe_message(error):
    """
    Look at a technical exception and return a friendly message for the user.
    The full technical error is logged separately.
    """
    error_text = str(error).lower()

    if "429" in error_text or "quota" in error_text or "rate" in error_text or "resource_exhausted" in error_text:
        return "The AI service is receiving too many requests right now. Please wait a moment and try again."

    if "api key" in error_text or "api_key" in error_text or "401" in error_text or "403" in error_text or "permission" in error_text:
        return "The AI service rejected the request. Please check the API key in the backend settings."

    if "404" in error_text or "not found" in error_text:
        return "The configured AI model was not found. Please check the model name in the backend settings."

    if "timeout" in error_text or "timed out" in error_text or "deadline" in error_text:
        return "The AI service took too long to respond. Please try again."

    return "The AI service is temporarily unavailable. Please try again."


def ask_gemini(messages):
    """
    Send a list of LangChain messages to Gemini and return the reply text.

    'messages' is a list such as:
        [SystemMessage(content="You are ..."), HumanMessage(content="Hi")]

    Raises GeminiError (with a safe message) if anything goes wrong.
    """
    model = get_gemini_model()

    try:
        response_message = model.invoke(messages)
    except Exception as error:
        # Technical details go to the log file only.
        logger.error("Gemini request failed: " + str(error))
        raise GeminiError(translate_error_to_safe_message(error))

    reply_text = get_text_from_response(response_message)

    if reply_text == "":
        logger.error("Gemini returned an empty reply")
        raise GeminiError("The AI service returned an empty answer. Please try again.")

    return reply_text