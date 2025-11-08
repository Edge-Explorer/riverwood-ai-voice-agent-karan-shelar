def build_system_prompt():
    return(
        "You are Riverwood AI, a warm, friendly real-estate voice assistant."
        "Greet politely, use casual Hindi/English phrases occasionally (eg., 'Namaste Sir, chai pee li?'),"
        "and provide short consise updates. Keep tone warm and slightly local."
    )
    
def compose_prompt(user_message, memory):
    """
    memory:list of past (user, assistant) tuples, newest last
    """""
    mem_text=""
    if memory:
        mem_text="Previous brief conversation:\n"
        for u, a in memory:
            mem_text+=f"uesr: {u}\nAssistant: {a}\n"
        mem_text+="\n"
    prompt=f"{build_system_prompt()}\n{mem_text}User: {user_message}\nAssistant:"
    return prompt
    