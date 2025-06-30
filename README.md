
# MCP Server with MongoDB

This project demonstrates an MCP server that integrates with MongoDB. It communicates with a client via the Model Context Protocol (MCP), enabling seamless interaction with different services.

## Overview

This project includes the following features:
- MCP server with custom tool for fetching database data.
- Integration with Gemini generating responses.
- Real-time interaction through the MCP client.

## Project Structure

```
.
├── pyproject.toml          # Project configuration
├── README.md               # Project documentation
├── requirements.txt        # Project dependencies 
├── mcp_client.py           # MCP client implementation
├── mcp_server.py           # MCP server with custom tools
└── uv.lock                 # Dependency lock file
```

## Server Implementation

The server exposes the following tools:

1. **`query_mongodb_nl`** – A tool that fetches data from a connected MongoDb, User is to provide a query in natural language and a collection `collection_name` to fetch the data from it.


## Client Implementation

The client connects to the server, initializes a session, and can call the server’s tools. It interacts with the user, handling requests for interacting with a MongoDB

### Key Features:
- **User input handling:** The client listens for user input and sends requests to the server to invoke specific tools.
- **Tool execution:** The client sends requests to the server, which executes the respective tool and returns results like weather data or video summaries.

## Getting Started

### Prerequisites

- Python 3.9+
- uv (Python package manager)
- Environment variables for API keys:
  - `GEMINI_KEY`
  - `MONGODB_URI`


### Installation

```bash
# Install dependencies
uv add -r requirements.txt .
```

### Running the Example

1. Start the client (which will automatically start the server):

```bash
uv run mcp_client.py
```

2. The client will connect to the server, list available tools, and prompt you to input commands.

## Usage

The client can:
- fetch data from a MongoDB by a natural language user query.

## Example Interaction

```
Available tools: ['query_mongodb_nl']

You: find top 10 movies where genres "Western" . collection_name = movies


Assistant: Here are the top 10 movies with the genres "Western" from the "movies" collection:
1. The Great Train Robbery
2. Wild and Woolly
3. The Iron Horse
4. Clash of the Wolves
5. In Old Arizona
6. The Big Trail
7. Cimarron
8. Viva Villa!
9. Der Kaiser von Kalifornien
10. Of Human Hearts


You: Exit
Exiting...
```

## Test with MCP Inspector

To inspect the running server and monitor tool invocations:

1. Start the server using:

```bash
mcp dev mcp_server.py
```

2. Open the MCP Inspector at [http://localhost:5173](http://localhost:5173) to monitor incoming requests.

## Resources

This project uses:
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Official Documentation](https://modelcontextprotocol.io)



## License

This project is licensed under the MIT License - see the LICENSE file for details.
