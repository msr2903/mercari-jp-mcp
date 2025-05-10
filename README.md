## Demo
<img src="/assets/demo.gif" width="600" height="600"/>

## Requirements

- Python 3.11 or higher
- Dependencies as listed in `pyproject.toml`, including:
  - mcp
  - mercari
  - pydantic
    
## Pre-setup

1. uv
   https://docs.astral.sh/uv/getting-started/installation/

2. Microsoft C++ Build Tools (For Windows)
   https://visualstudio.microsoft.com/visual-cpp-build-tools/

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/msr2903/mercari-jp-mcp.git
   cd mercari-jp-mcp
   ```

2. Create and activate a virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

## Usage

### Development Mode

You can test the server with MCP Inspector by running:

```bash
uv run server.py
```

You can also test to input manually the query, exclude keywords, min and max price by running:

```bash
uv run check_server.py
```

This will start the server and allow you to test the available tools.

### Integration with Claude for Desktop

To integrate this server with Claude for Desktop:

1. Install Claude for Desktop to your local machine.
2. Install VS Code to your local machine. Then run the following command to open the `claude_desktop_config.json` file:
   - MacOS: `code ~/Library/Application\ Support/Claude/claude_desktop_config.json`
   - Windows: `code $env:AppData\Claude\claude_desktop_config.json`

3. Edit the Claude for Desktop config file, located at:
   - macOS: 
     ```json
     {
       "mcpServers": {
         "mercari": {
           "command": "uv",
           "args": [
             "--directory",
             "/ABSOLUTE/PATH/TO/PARENT/FOLDER/mercari-jp-mcp",
             "run",
             "server.py"
           ]
         }
       }
     }
     ```
   - Windows:
     ```json
     {
       "mcpServers": {
         "mercari": {
           "command": "uv",
           "args": [
             "--directory",
             "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\mercari-jp-mcp",
             "run",
             "server.py"
           ]
         }
       }
     }
     ```

   - **Note**: You may need to put the full path to the uv executable in the command field. You can get this by running `which uv` on MacOS/Linux or `where uv` on Windows.

4. Restart Claude for Desktop

## Thanks
This work would not have been possible without amazing open source projects, including (but not limited to):

- jlowin/fastmcp (https://github.com/jlowin/fastmcp)
- marvinody/mercari (https://github.com/marvinody/mercari/)

Thank you to the authors of these projects for making them available to the community!
