import asyncio
from pg_utils import init_pool   
from multi_agent_magentic import init_magentic_group_chat
import pwinput


if __name__ == "__main__":

    pw = pwinput.pwinput(prompt='Enter your Azure postgreSQL db password: ', mask='*')
    connection_pool = init_pool(pw)
    q = input("Ask a question: ")  # Get user input for the query

    final_res = asyncio.run(init_magentic_group_chat(q, connection_pool, True))
