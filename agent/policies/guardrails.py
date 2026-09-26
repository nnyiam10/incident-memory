ALLOWED_TOOLS = {"search_logs", "query_metrics", "get_deployments", "search_code", "run_sandbox_test"}

def authorize(tool: str, target: str) -> None:
    if tool not in ALLOWED_TOOLS:
        raise PermissionError(f"Tool {tool} is not available")
    if tool == "run_sandbox_test" and target != "sandbox":
        raise PermissionError("Tests may only execute against the sandbox")

