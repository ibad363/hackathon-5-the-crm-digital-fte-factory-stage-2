from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, RunConfig
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

external_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

model = OpenAIChatCompletionsModel(
    model="qwen/qwen3.6-plus-preview:free",
    openai_client=external_client,
)

config = RunConfig(
    model=model,
    model_provider=external_client, # type: ignore
    tracing_disabled=True,
)