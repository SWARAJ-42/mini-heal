import json

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.agent_tools import (
    get_container_status,
    check_health,
    get_recent_logs,
    inspect_source_file,
)
from app.incident_report import IncidentReport

MAX_TOOL_CALLS = 5

# The model can request only these functions.
AVAILABLE_TOOLS = {
    "get_container_status": get_container_status,
    "check_health": check_health,
    "get_recent_logs": get_recent_logs,
    "inspect_source_file": inspect_source_file,
}

# Function schemas tell the model what each tool does.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "get_container_status",
        "description": (
            "Check whether the configured MiniHeal Docker "
            "container is running. Use this when investigating "
            "container availability."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "check_health",
        "description": (
            "Check the configured MiniHeal health endpoint. "
            "Use this to investigate application and database "
            "health."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_recent_logs",
        "description": (
            "Retrieve the last 50 lines of logs from the "
            "configured MiniHeal Docker container. Use this "
            "to investigate errors and identify possible "
            "causes of application failures."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "inspect_source_file",
        "description": (
            "Read the contents of one allowlisted MiniHeal source "
            "file. Use this to understand the implementation behind "
            "an observed runtime error. Available files are "
            "app/main.py, app/database.py, and app/config.py."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "enum": [
                        "app/main.py",
                        "app/database.py",
                        "app/config.py",
                    ],
                }
            },
            "required": ["file_path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


SYSTEM_INSTRUCTIONS = """
You are MiniHeal's read-only incident investigation agent.

Your responsibility is to investigate the current state of
the MiniHeal application using the available diagnostic tools.

Rules:
- Use tools to gather evidence before drawing conclusions.
- You may call multiple tools when useful.
- Interpret tool results carefully.
- Distinguish observed facts from hypotheses.
- Never claim to have performed an action you did not perform.
- Never invent logs, metrics, or diagnostic evidence.
- Do not recommend that an action has already been executed.
- You have read-only access. You cannot restart containers,
  modify files, change configuration, or modify the database.

Produce a final incident report containing:
1. Diagnosis
2. Summary
3. Observed evidence
4. Likely hypotheses
5. Recommended next actions
6. Confidence level

Investigation strategy:
- Start by checking container status and application health.
- If the health endpoint reports an error, inspect recent logs.
- Use log messages as evidence, but distinguish them from
  confirmed root causes.
- Do not assume that the latest log entry explains the
  current incident.
- If evidence is insufficient, explicitly state what
  additional information is needed.

Source code investigation:
- Inspect source code only when runtime evidence suggests
  that understanding the implementation would help.
- Use app/main.py to understand health checks and API behavior.
- Use app/database.py to understand database configuration.
- Use app/config.py to understand runtime configuration.
- Never assume that reading source code proves that a
  particular failure occurred.
- Correlate source code with observed runtime evidence.

Final report requirements:
- Return a structured incident report.
- Use only observed evidence to support confirmed findings.
- Clearly separate hypotheses from confirmed findings.
- Never claim a configuration variable was enabled
  unless runtime evidence confirms it.
- Use UNKNOWN when the available evidence is insufficient
  to classify the incident.
- Recommendations must be read-only investigative steps.
"""



def execute_tool(name: str, arguments: str) -> dict:
    """Validate and execute an allowlisted tool."""

    if name not in AVAILABLE_TOOLS:
        return {
            "success": False,
            "error": f"Tool '{name}' is not allowed.",
        }

    try:
        parsed_arguments = json.loads(arguments)

        if not isinstance(parsed_arguments, dict):
            raise ValueError("Arguments must be a JSON object.")

        if name == "inspect_source_file":
            if set(parsed_arguments) != {"file_path"}:
                raise ValueError(
                    "Expected exactly one argument: file_path."
                )

            file_path = parsed_arguments["file_path"]

            if not isinstance(file_path, str):
                raise ValueError("file_path must be a string.")

            return inspect_source_file(file_path)

        # All other tools currently accept no arguments.
        if parsed_arguments:
            raise ValueError(
                "This tool does not accept arguments."
            )

        return AVAILABLE_TOOLS[name]()

    except (json.JSONDecodeError, ValueError) as error:
        return {
            "success": False,
            "error": f"Invalid tool arguments: {error}",
        }

    except Exception as error:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(error)[:500]}",
        }


def investigate(client=None) -> dict:
    """Run a bounded investigation and return its report and audit trace."""

    if client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        client = OpenAI(api_key=OPENAI_API_KEY)

    input_messages = [
        {
            "role": "user",
            "content": (
                "Investigate the current health of MiniHeal. "
                "Collect relevant evidence using your tools "
                "and produce an incident report."
            ),
        }
    ]

    tool_calls_executed = 0
    tool_trace = []

    while True:
        tool_choice = "none" if tool_calls_executed >= MAX_TOOL_CALLS else "auto"

        response = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=SYSTEM_INSTRUCTIONS,
            tools=TOOL_SCHEMAS,
            tool_choice=tool_choice,
            input=input_messages,
            text_format=IncidentReport,
        )

        function_calls = [
            item for item in response.output if item.type == "function_call"
        ]

        if not function_calls:
            report = response.output_parsed

            if report is None:
                raise RuntimeError(
                    "The model did not return a valid IncidentReport."
                )

            return {
                "report": report,
                "tool_trace": tool_trace,
            }

        input_messages.extend(response.output)

        for call in function_calls:
            if tool_calls_executed >= MAX_TOOL_CALLS:
                result = {
                    "success": False,
                    "error": "Maximum tool-call limit reached.",
                }
            else:
                result = execute_tool(
                    call.name,
                    call.arguments,
                )
                tool_calls_executed += 1

            tool_trace.append(
                {
                    "sequence": len(tool_trace) + 1,
                    "tool": call.name,
                    "arguments": call.arguments,
                    "result": result,
                    "success": result.get("success", False),
                }
            )

            input_messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result),
                }
            )
