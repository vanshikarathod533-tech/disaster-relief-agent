import re
import json
import logging
from typing import Any, Generator

from google.adk import Context, Workflow, Event
from google.adk.events import RequestInput
from google.adk.workflow import node
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.apps import App
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types

from app.config import config

# Security audit logging configuration
logging.basicConfig(level=logging.INFO)
audit_logger = logging.getLogger("security_audit")

# -----------------------------------------------------------------------------
# MCP Server Toolsets
# -----------------------------------------------------------------------------
mcp_toolset_safety = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "app.mcp_server"]
        )
    ),
    tool_filter=["get_weather_alerts", "get_supply_checklist"]
)

mcp_toolset_resources = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "app.mcp_server"]
        )
    ),
    tool_filter=["get_shelters", "get_hospitals"]
)

# -----------------------------------------------------------------------------
# Specialized Sub-Agents
# -----------------------------------------------------------------------------
safety_guide = Agent(
    name="safety_guide",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an expert Safety and Evacuation Guide. Your role is to provide immediate, "
        "actionable safety guidelines, weather/hazard warnings, and evacuation protocols based on the disaster type and location. "
        "Use the available weather alert tools or checklists if needed, and respond clearly with step-by-step instructions. "
        "Be direct, calm, and focus on preservation of life."
    ),
    tools=[mcp_toolset_safety]
)

resource_locator = Agent(
    name="resource_locator",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an expert Resource Locator. Your role is to find nearby emergency shelters, hospitals, "
        "and medical stations. Provide precise descriptions of capacities, coordinates (if available), "
        "pets allowed status, and other details from your tools. "
        "Use the tools get_shelters and get_hospitals to find resources. "
        "Be extremely detailed and accurate."
    ),
    tools=[mcp_toolset_resources]
)

# -----------------------------------------------------------------------------
# Orchestrator Agent
# -----------------------------------------------------------------------------
orchestrator = Agent(
    name="orchestrator",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the main coordinator of the Disaster Relief Multi-Agent System. "
        "Your task is to analyze the user's emergency request, location, and any special needs. "
        "You must delegate tasks to:\n"
        "1. safety_guide: to get safety, evacuation, and weather guidance.\n"
        "2. resource_locator: to get shelter and hospital locations.\n"
        "Delegate tasks to both agents using your tools. Combine the responses from safety_guide and "
        "resource_locator into a single, comprehensive emergency response plan. "
        "Structure the final response with clear sections: Actions, Shelters & Hospitals, Supply Checklist, and Alert Status."
    ),
    tools=[
        AgentTool(agent=safety_guide, skip_summarization=False),
        AgentTool(agent=resource_locator, skip_summarization=False)
    ]
)

# -----------------------------------------------------------------------------
# Workflow Function Nodes
# -----------------------------------------------------------------------------
@node(name="security_checkpoint")
def security_checkpoint(ctx: Context, node_input: str) -> Event:
    """Validates the input for safety violations and scrubs PII."""
    # 1. PII Scrubbing (Regex)
    phone_pattern = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    cleaned_input = phone_pattern.sub("[REDACTED_PHONE]", node_input)
    cleaned_input = email_pattern.sub("[REDACTED_EMAIL]", cleaned_input)
    pii_found = (cleaned_input != node_input)
    
    # 2. Prompt Injection Detection
    injection_keywords = ["ignore previous instructions", "override system", "you are now", "developer mode", "jailbreak"]
    injection_detected = any(kw in cleaned_input.lower() for kw in injection_keywords)
    
    # 3. Domain-Specific Rule: Must have emergency context
    emergency_keywords = ["flood", "earthquake", "cyclone", "wildfire", "storm", "hurricane", "tsunami", "emergency", "help", "shelter", "rescue"]
    has_emergency = any(kw in cleaned_input.lower() for kw in emergency_keywords)
    
    # Audit log entry
    audit_data = {
        "pii_found": pii_found,
        "injection_detected": injection_detected,
        "emergency_validated": has_emergency,
        "severity": "INFO"
    }
    
    if injection_detected:
        audit_data["severity"] = "CRITICAL"
        audit_data["reason"] = "Prompt injection attempt detected"
        audit_logger.warning(json.dumps(audit_data))
        ctx.state["security_audit"] = audit_data
        return Event(route="SECURITY_EVENT", output="CRITICAL: Prompt injection detected.")
        
    if not has_emergency:
        audit_data["severity"] = "WARNING"
        audit_data["reason"] = "No emergency-related keywords detected in the prompt"
        audit_logger.warning(json.dumps(audit_data))
        ctx.state["security_audit"] = audit_data
        
    audit_logger.info(json.dumps(audit_data))
    ctx.state["security_audit"] = audit_data
    
    return Event(route="SAFE", output=cleaned_input)


@node(name="security_event")
def security_event(ctx: Context, node_input: str) -> Event:
    """Gracefully handles security audit events."""
    return Event(output="Access Denied: The request contains potential security risks or policy violations.")


@node(name="check_special_needs")
def check_special_needs(ctx: Context, node_input: str) -> Generator[Any, Any, Any]:
    """Asks the user for special needs if not already specified in the prompt."""
    ctx.state["original_prompt"] = node_input
    
    keywords = ["medical", "elderly", "infant", "baby", "pet", "dog", "cat", "wheelchair", "mobility", "special needs"]
    has_special_needs = any(kw in node_input.lower() for kw in keywords)
    
    if not has_special_needs:
        # Pause execution to ask the user
        yield RequestInput(
            message="Do you or anyone in your group have special needs (e.g., medical conditions, mobility issues, infants, or pets)? If none, please reply with 'none'."
        )
    else:
        yield Event(output=node_input)


@node(name="process_user_response")
def process_user_response(ctx: Context, node_input: str) -> str:
    """Processes user response for special needs and passes to orchestrator."""
    original_prompt = ctx.state.get("original_prompt", "")
    
    if node_input == original_prompt:
        ctx.state["special_needs"] = "None or already provided"
        return original_prompt
    else:
        ctx.state["special_needs"] = node_input
        return f"User Emergency Request: {original_prompt}\nGroup Special Needs: {node_input}"


@node(name="aggregator")
def aggregator(ctx: Context, node_input: str) -> str:
    """Aggregates the final output and adds a standard safety disclaimer."""
    disclaimer = (
        "\n\n---\n"
        "⚠️ **Disclaimer:** This information is generated by an AI assistant using local data. "
        "For critical emergencies, always follow instructions from local authorities and contact official emergency services."
    )
    return f"{node_input}{disclaimer}"

# -----------------------------------------------------------------------------
# Workflow Definition
# -----------------------------------------------------------------------------
root_agent = Workflow(
    name="disaster_relief_workflow",
    edges=[
        ("START", security_checkpoint),
        (security_checkpoint, {
            "SAFE": check_special_needs,
            "SECURITY_EVENT": security_event
        }),
        (check_special_needs, process_user_response),
        (process_user_response, orchestrator),
        (orchestrator, aggregator),
        (security_event, aggregator)
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)
