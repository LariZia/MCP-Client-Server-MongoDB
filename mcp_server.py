
from mcp.server.fastmcp import FastMCP
import asyncio
from dotenv import load_dotenv
import os
import logging
import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
import json
from pprint import pprint 
import ast
import re
from datetime import datetime # Import datetime for serialization
from bson import ObjectId # Import ObjectId for serialization

load_dotenv()
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize MongoDB client
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client["sample_mflix"]


# MCP app setup
mcp = FastMCP("Python360")

# Google Gemini setup
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))



# --- Helper function for JSON serialization ---
def serialize_doc(doc):
    """
    Recursively converts ObjectId and datetime objects in a MongoDB document
    to string and ISO 8601 string respectively, for JSON serialization.
    """
    if isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    elif isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_doc(elem) for elem in doc]
    else:
        return doc

@mcp.tool()
async def query_mongodb_nl(prompt: str, collection_name: str = "mycollection") -> str:
    """
    Takes a natural language prompt, generates a MongoDB query, and runs it.

    Args:
        prompt (str): User's natural language request.
        collection_name (str): MongoDB collection to search.

    Returns:
        str: Query results or error message.
    """
    try:
        # Step 1: Generate the query using Gemini
        system_prompt = (
            "You are a MongoDB query generator. Given a natural language instruction, "
            "generate only a valid MongoDB query as a JSON object, not Python. Use double quotes. (no explanations). "
            "Assume typical document fields like `name`, `age`, `email`, `created_at`, `city`."
        )
        gemini_response = gemini.generate_content([system_prompt, prompt])
        query_code_raw = gemini_response.text.strip()
        logging.info(f"Gemini raw response (query_code_raw):\n{query_code_raw}")

        collection = db[collection_name]
        
        json_str_to_parse = query_code_raw

        # Attempt to extract JSON from a markdown code block first (e.g., ```json{...}```)
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", query_code_raw, re.DOTALL)
        if json_match:
            json_str_to_parse = json_match.group(1)
            logging.info(f"Extracted JSON from markdown block:\n{json_str_to_parse}")
        else:
            logging.info(f"No markdown block found. Attempting to parse raw string directly.")

        parsed_query_spec = {}
        try:
            # Try parsing as JSON first
            parsed_query_spec = json.loads(json_str_to_parse)
            logging.info(f"Successfully parsed with json.loads: {parsed_query_spec}")
        except json.JSONDecodeError as e_json:
            logging.warning(f"json.loads failed: {e_json}. Trying ast.literal_eval...")
            try:
                # Fallback to ast.literal_eval for Python-style dictionaries (e.g., with single quotes)
                parsed_query_spec = ast.literal_eval(json_str_to_parse)
                logging.info(f"Successfully parsed with ast.literal_eval: {parsed_query_spec}")
            except (ValueError, SyntaxError) as e_ast:
                logging.error(f"Failed to parse query from Gemini. JSONDecodeError: {e_json}, LiteralEvalError: {e_ast}")
                return (f"Failed to parse query from Gemini. Expected valid JSON or Python dictionary. "
                        f"Raw content received: '{query_code_raw}'. "
                        f"Errors: JSON ({e_json}), Python literal ({e_ast})")

        if not isinstance(parsed_query_spec, dict):
            return (f"Failed to parse query from Gemini: Expected a dictionary, but got "
                    f"{type(parsed_query_spec).__name__}. Raw content: '{query_code_raw}'")

        # --- Determine operation: aggregate or find ---
        results = []
        if "aggregate" in parsed_query_spec and isinstance(parsed_query_spec["aggregate"], list):
            logging.info("Detected an aggregation pipeline.")
            pipeline = parsed_query_spec["aggregate"]
            
            # Ensure pipeline is not empty to avoid errors
            if not pipeline:
                return "Error: Aggregation pipeline is empty."
            
            cursor = collection.aggregate(pipeline)
            async for doc in cursor:
                results.append(serialize_doc(doc)) # Apply serialization
        else:
            # Assume a simple find operation if 'aggregate' key is not present
            # The previous prompt resulted in {"filter": {}, "limit": 10} for find operations
            # If Gemini gives {"$match": {}, "$limit": 10} for find, adjust keys accordingly
            logging.info("Detected a find-like operation. Extracting filter and limit.")
            
            # Prioritize 'filter' (from our ideal prompt response)
            # If 'filter' not present, check for '$match' (from aggregation-like response)
            query_filter = parsed_query_spec.get("filter", parsed_query_spec.get("$match", {}))
            
            # Prioritize 'limit' (from our ideal prompt response)
            # If 'limit' not present, check for '$limit' (from aggregation-like response)
            find_limit = parsed_query_spec.get("limit", parsed_query_spec.get("$limit", 0))

            if not isinstance(query_filter, dict):
                logging.warning(f"'filter' field was not a dictionary. Defaulting to {{}}. Filter was: {query_filter}")
                query_filter = {}

            cursor = collection.find(query_filter)
            if isinstance(find_limit, int) and find_limit > 0:
                cursor = cursor.limit(find_limit)
            
            async for doc in cursor:
                results.append(serialize_doc(doc)) # Apply serialization


        # Return results as a JSON string
        return json.dumps(results) if results else "No documents found."

    except Exception as e:
        logging.error(f"An unexpected error occurred in query_mongodb_nl: {e}", exc_info=True)
        return f"Error executing MongoDB query: {e}"


# Run server
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.sleep(0.1))  # Init async context
    mcp.run()
