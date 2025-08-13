# This file contains f-string templates for building prompts.

def SECTION_HEADER(title: str) -> str:
    return f"--- {title.upper()} ---"

def PROFILE_PRIMARY(name: str, profile: str) -> str:
    return f"**{name.upper()}'S PROFILE (PRIMARY SOURCE):** {profile or 'Not provided.'}"

def PROFILE_CONTEXT(name: str, profile: str) -> str:
    return f"**{name.upper()}'S PROFILE:** {profile or 'Not provided.'}"

def PROFILE_SECONDARY(name: str, profile: str) -> str:
    return f"**{name.upper()}'S PROFILE (SECONDARY):** {profile or 'Not provided.'}"

def CRITICAL_NOTICE(message: str) -> str:
    return f"(NOTE: {message})"

def TIME_GAP_NOTICE(state_type: str) -> str:
    messages = {
        'REENGAGING_DAY': '1-7 day gap. You are in SOFT RE-ENGAGEMENT mode.',
        'REENGAGING_WEEK': '1-4 week gap. You are in COLD RE-ENGAGEMENT mode.',
        'REENGAGING_MONTH': '1+ month gap. You are in RESURRECTION mode.'
    }
    return f"(Note: {messages.get(state_type, 'Re-engagement mode')})"

def MESSAGE_FORMAT(date: str, sender: str, content: str) -> str:
    return f"[{date or 'No Date'}] {sender}: {content}"