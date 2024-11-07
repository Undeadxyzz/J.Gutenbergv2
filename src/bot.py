import os
import sys
import traceback

from botbuilder.core import MemoryStorage, TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from teams.ai.models import AzureOpenAIModelOptions, OpenAIModel, OpenAIModelOptions
from teams.ai.planners import ActionPlanner, ActionPlannerOptions
from teams.ai.prompts import PromptManager, PromptManagerOptions
from teams.state import TurnState

from my_data_source import MyDataSource
from config import Config
from git_utils import setup_repository, read_file_from_repo  # Import Git utility functions

config = Config()

# Create AI components
model: OpenAIModel

model = OpenAIModel(
    OpenAIModelOptions(
        api_key=config.OPENAI_API_KEY,
        default_model=config.OPENAI_MODEL_NAME,
    )
)
    
prompts = PromptManager(PromptManagerOptions(prompts_folder=f"{os.getcwd()}/prompts"))

my_data_source = MyDataSource('local-search')
prompts.add_data_source(my_data_source)

planner = ActionPlanner(
    ActionPlannerOptions(model=model, prompts=prompts, default_prompt="chat")
)

# Define storage and application
storage = MemoryStorage()
bot_app = Application[TurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=storage,
        adapter=TeamsAdapter(config),
        ai=AIOptions(planner=planner),
    )
)

@bot_app.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, state: TurnState):
    await context.send_activity("How can I help you today?")

@bot_app.message("update_repo")
async def handle_update_repo_command(context: TurnContext, state: TurnState):
    setup_repository()
    await context.send_activity("Repository has been updated.")

@bot_app.message("read_file")
async def handle_read_file_command(context: TurnContext, state: TurnState):
    # Expecting command format: "read_file <file_path>"
    command = context.activity.text
    try:
        _, file_path = command.split(" ", 1)
        file_content = read_file_from_repo(file_path)
        if file_content:
            await context.send_activity(f"Contents of {file_path}:\n{file_content}")
        else:
            await context.send_activity("File not found.")
    except ValueError:
        await context.send_activity("Please provide a file path with the command (e.g., 'read_file data/sample.txt').")

@bot_app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
