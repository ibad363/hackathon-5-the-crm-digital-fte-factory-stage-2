from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, RunConfig
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NINEROUTER_API_KEY = os.getenv("NINEROUTER_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

if not NINEROUTER_API_KEY:
    raise ValueError("NINEROUTER_API_KEY environment variable not set")

# GEMINI

# external_client = AsyncOpenAI(
#     api_key=GEMINI_API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta",
# )

# model = OpenAIChatCompletionsModel(
#     # model="gemini-2.5-flash",
#     model="gemini-3.1-flash-lite-preview",
#     openai_client=external_client,
# )

# NINEROUTER

external_client = AsyncOpenAI(
    api_key=NINEROUTER_API_KEY,
    base_url="http://localhost:20128/v1",
)

model = OpenAIChatCompletionsModel(
    model="qw/qwen3-coder-plus",
    openai_client=external_client,
)

# OPENROUTER

# external_client = AsyncOpenAI(
#     api_key=OPENROUTER_API_KEY,
#     base_url="https://openrouter.ai/api/v1",
# )

# model = OpenAIChatCompletionsModel(
#     # model="qwen/qwen3.6-plus:free",
#     model="openai/gpt-oss-20b:free",
#     openai_client=external_client,
# )

config = RunConfig(
    model=model,
    model_provider=external_client, # type: ignore
    tracing_disabled=True,
)