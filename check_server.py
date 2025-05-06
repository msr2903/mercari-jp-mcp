# check_server.py
import asyncio
import json
import logging
from fastmcp import Client
from fastmcp.exceptions import ClientError

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_checker")

# --- Configuration ---
SERVER_FILE = "server.py"
TOOL_TO_CALL = "search_mercari_jp"

# --- Parameters for the Tool Call ---
SEARCH_PARAMS = {
    "keyword": "iPhone15 Pro 256GB",
    "exclude_keywords": "11 12 13 14 16 ジャンク max", # "junk" in Japanese
    "min_price": 100000,
    "max_price": 150000
}

async def check_server():
    """
    Connects to the FastMCP server, checks if the expected tool is available,
    and attempts to call the tool with specific parameters.
    """
    logger.info(f"Attempting to connect to server script: {SERVER_FILE}")
    tool_found = False
    tool_call_successful = False
    final_status = "FAILURE" # Default to failure

    try:
        # Create a client targeting the server file (implies stdio transport)
        async with Client(SERVER_FILE) as client:
            logger.info("Successfully connected to the server.")

            # --- Check 1: List Tools ---
            logger.info("Listing available tools...")
            try:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                logger.info(f"Found tools: {tool_names}")

                if TOOL_TO_CALL in tool_names:
                    logger.info(f"Expected tool '{TOOL_TO_CALL}' found.")
                    tool_found = True
                else:
                    logger.error(f"FAILURE: Expected tool '{TOOL_TO_CALL}' NOT found.")
                    print("\n--- Server Check Result: FAILURE ---")
                    print(f"Connected to the server, but the expected tool '{TOOL_TO_CALL}' was not found.")
                    print(f"Available tools: {tool_names}")
                    return # Exit if tool not found

            except ClientError as e:
                logger.error(f"FAILURE: Error while listing tools: {e}")
                print("\n--- Server Check Result: FAILURE ---")
                print(f"Connected to the server, but failed to list tools: {e}")
                return # Exit on listing error
            except Exception as e:
                 logger.error(f"FAILURE: An unexpected error occurred while listing tools: {e}", exc_info=True)
                 print("\n--- Server Check Result: FAILURE ---")
                 print(f"An unexpected error occurred: {e}")
                 return # Exit on unexpected error

            # --- Check 2: Call the Tool (if found) ---
            if tool_found:
                logger.info(f"Attempting to call tool '{TOOL_TO_CALL}' with params: {SEARCH_PARAMS}")
                try:
                    results = await client.call_tool(
                        TOOL_TO_CALL,
                        SEARCH_PARAMS
                    )
                    logger.info(f"Tool '{TOOL_TO_CALL}' executed.")
                    tool_call_successful = True # Mark as successful if call doesn't raise ClientError

                    # Process and print results
                    if results:
                        items_list_json = results[0].text
                        items_list = json.loads(items_list_json)

                        if items_list:
                            logger.info(f"Tool call successful. Found {len(items_list)} items:")
                            print("\n--- Mercari Search Results (First 10) ---")
                            for item in items_list[:10]:
                                print(f"- {item['name']} ({item['price']} JPY): {item['url']}")
                            if len(items_list) > 10:
                                print(f"... and {len(items_list) - 10} more.")
                        else:
                            logger.info("Tool call successful, but no items found matching the criteria.")
                            print("\n--- Mercari Search Results ---")
                            print("No items found matching the criteria.")
                    else:
                         logger.warning("Tool call successful, but returned no results content.")
                         print("\n--- Mercari Search Results ---")
                         print("Tool executed but returned no results.")

                except ClientError as e:
                    # This catches errors reported *by the tool* via MCP
                    logger.error(f"FAILURE: Tool '{TOOL_TO_CALL}' reported an error: {e}")
                    print("\n--- Server Check Result: FAILURE ---")
                    print(f"The tool '{TOOL_TO_CALL}' executed but reported an error: {e}")
                except Exception as e:
                    # This catches other errors during the call (e.g., client-side issues)
                    logger.error(f"FAILURE: An unexpected error occurred while calling tool '{TOOL_TO_CALL}': {e}", exc_info=True)
                    print("\n--- Server Check Result: FAILURE ---")
                    print(f"An unexpected error occurred while calling the tool: {e}")

            # --- Final Status ---
            if tool_found and tool_call_successful:
                final_status = "SUCCESS"
                print("\n--- Server Check Result: SUCCESS ---")
                print(f"The server is running, '{TOOL_TO_CALL}' tool is available and was called successfully.")
            elif tool_found and not tool_call_successful:
                # Already printed failure message in the except block
                pass
            # else: tool not found, already printed failure


    except ConnectionRefusedError:
        logger.error(f"FAILURE: Connection refused. Is the server script ({SERVER_FILE}) running?")
        print("\n--- Server Check Result: FAILURE ---")
        print(f"Could not connect. Make sure '{SERVER_FILE}' is running in another terminal.")
    except FileNotFoundError:
         logger.error(f"FAILURE: Server script '{SERVER_FILE}' not found in the current directory.")
         print("\n--- Server Check Result: FAILURE ---")
         print(f"Server script '{SERVER_FILE}' not found. Make sure it's in the same directory or provide the correct path.")
    except Exception as e:
        logger.error(f"FAILURE: An unexpected error occurred during connection: {e}", exc_info=True)
        print("\n--- Server Check Result: FAILURE ---")
        print(f"An unexpected error occurred during connection: {e}")

if __name__ == "__main__":
    asyncio.run(check_server())
