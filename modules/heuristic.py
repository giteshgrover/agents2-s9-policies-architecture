from core.context import AgentContext
import re
import pdb

NOT_ALLOWED_WORDS = ["fuck", "shit", "ass", "bitch", "cunt", "damn", "dick", "fag", "faggot", "fuck", "shit", "ass", "bitch", "damn", "dick", "fag", "faggot"]
def heuristic_check_context(context: AgentContext) -> bool:
    """
    Check if the context is suitable for a heuristic check.
    """
    if(context.session_id is None):
        print("[Heuristic] Session ID is not set")
        return False

    if(context.step > context.agent_profile.strategy.max_steps):
        print("[Heuristic] Step is greater than max steps")
        return False

    # if(context.memory.get_session_items() is None):
    #     print("[Heuristic] Memory is not set")
    #     return False

    return True

def heuristic_check_input(user_input: str) -> bool:
    """
    Check if the user input is valid.
    """
    is_valid = valid_input(user_input)
    if not is_valid:
        print("[Heuristic] User input is not valid")
        return False
    return True

def heuristic_check_result(result: str) -> bool:
    """
    Check if the result is valid.
    """
    is_valid = valid_result(result)
    if not is_valid:
        print("[Heuristic] Result is not valid")
        return False

    return True

def heuristic_check_plan(plan: str) -> bool:
    """
    Check if the plan is valid.
    """
    is_solve_python_func = re.search(r"^\s*(async\s+)?def\s+solve\s*\(", plan, re.MULTILINE)
    
    if not is_solve_python_func:
        print("[Heuristic] Plan is not a Python function")
        return False

    # check if the python program is safe
    is_safe = check_python_safe(plan)
    if not is_safe:
        print("[Heuristic] Plan is not safe")
        return False

    return True

def check_python_safe(plan: str) -> bool:
    """
    Check if the Python program is safe.
    """
    return True

def valid_input(user_input: str) -> bool:
    """
    Check if the user input is valid.
    """
    if user_input is None or user_input.strip() == "":
        print("[Heuristic] User input is empty")
        return False

    pattern = r"\b(" + "|".join(map(re.escape, NOT_ALLOWED_WORDS)) + r")\b"
    if re.search(pattern, user_input.lower()):
        print("[Heuristic] User input contains not allowed words")
        pdb.set_trace()
        return False

    return True

def valid_result(result: str) -> bool:
    """
    Check if the result is valid.
    """
    return True