import warnings
warnings.filterwarnings("ignore")
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from autogen_agentchat.agents import UserProxyAgent

import os

AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')
 
# define the llm_config to set to use your deployed model
# load model into chat completion client

def init_client():
    llm_config = {
        "provider": "AzureOpenAIChatCompletionClient",
        "config": {
            "model": "gpt-4",
            "azure_endpoint": AZURE_OPENAI_ENDPOINT,
            "azure_deployment": AZURE_OPENAI_DEPLOYMENT,
            "api_version" : "2024-12-01-preview",
            "api_key": AZURE_OPENAI_KEY,
            "seed": 42}
    }

    client = ChatCompletionClient.load_component(llm_config)
    return client


# functio to get schema from schema_agent
def get_shared_schema_info():
    if schema_agent.schema_info is None:
        schema_agent.get_schema()
    return schema_agent.schema_info

def initiate_planner_agent(client):
    planning_agent = AssistantAgent(
                    name ="planning_agent",
                    description="An agent for planning tasks, this agent should be the first to engage when given a new task.",
                    model_client=client,
                    system_message="""
                    You are a planning agent.
                    Your job is to break down complex tasks into smaller, manageable subtasks.
                    Start by calling the schema_agent to retrieve the database schema information if conversation history does not have it.
                    Let the schema_agent retrieve schema for all tables. Do not specify any table name.
                    Your team members are:
                        schema_agent: retrieves database schema information
                        shipment_agent: queries the shipment database based on the retrieved schema
                        concierge_agent: provides the final answer to the user based on the query results
                    You only plan and delegate tasks - you do not execute them yourself.

                    When assigning tasks, use this format:
                    1. <agent> : <task>

                    """,
                )
    return planning_agent

def create_shipment_agent(client, shipment_chain):
        
    shipment_agent = AssistantAgent(name="shipment_agent",
                                model_client=client,
                                description="Retrieves information from the shipment database.",
                                tools=[FunctionTool(name="shipment_query", func= shipment_chain.execute_query, description= "runs postgres query on shipment database")],
                                system_message=(
                            "Your role is to query the database using 'shipment_query'."
                            # "Use 'get_shared_schema_info' from schema_agent to retrieve schema information."
                            "PostgreSQL query should adhere to the schema iformation"
                            "Focus on the shipments tables and ensure that all shipments are tracked correctly."
                            "Conditions in query should not be case sensitive."
                            )
                            )
    return shipment_agent

def create_schema_agent(client, shipment_chain):
    schema_agent = AssistantAgent(name="schema_agent",
                                model_client=client,
                                description="Understands and shares database schema information.",
                                tools=[FunctionTool(name="get_schema_info", func = shipment_chain.get_schema_info, description="Retrieves the database schema and shares it")],
                                system_message=(
                                        "Your role is to run 'get_schema_info' to retrieve schema information. Do not do anything else."
                                        "If you could not retrieve the schema information, say 'I failed to get the schema information'"
                                    )
                                ) 
    return schema_agent  

def create_concierge_agent(client):
    concierge_agent = AssistantAgent(name="concierge_agent",
                                model_client=client,
                                description="Provides final answer to user",
                                system_message=(
                                    "Your role is to simplify the results for the user and provide the final answer. Only provide results after shipment_agent has completed its task."
                                ),
                            )
    return concierge_agent

def get_user_input(dummy_var): # have to pass a dummy variable to match the function signature
    return input("Ask a question or type 'bye' to end the conversation:")

def create_user_proxy():
    user_proxy_agent = UserProxyAgent("user_proxy", 
                        description="Interact with user",
                        input_func = get_user_input)
    return user_proxy_agent