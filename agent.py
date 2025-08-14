#agent.py

import logging
from dotenv import load_dotenv

from livekit import agents
from livekit.plugins import google
from config import settings
from utils.logger import setup_logging
from utils.language_support import language_manager
from special_function_tools import (
    # Enhanced functions
    register_patient,
    find_patient_enhanced,
    recommend_doctor,
    get_available_slots_enhanced,
    book_appointment_enhanced,
    reschedule_appointment_enhanced,
    cancel_appointment_enhanced,
    get_appointment_analytics,
    get_doctor_availability,
    
    register_patient_legacy,
    find_patient,
    get_available_slots,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
)


from instructions import AGENT_INSTRUCTION,SESSION_INSTRUCTION


load_dotenv()

# Setup logging
logger = setup_logging()


# ------------------ Enhanced Agent Class ------------------ #
class ApolloAssistAgent(agents.Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Leda", #Achernar,Vindemiatrix,Sulafat,Callirrhoe,Laomedeia,Zephyr
                temperature=0.7,  # Slightly more deterministic for appointment booking
            ),
            tools=[
                # Enhanced function tools
                agents.function_tool(register_patient),
                agents.function_tool(find_patient_enhanced),
                agents.function_tool(recommend_doctor),
                agents.function_tool(get_available_slots_enhanced),
                agents.function_tool(book_appointment_enhanced),
                agents.function_tool(reschedule_appointment_enhanced),
                agents.function_tool(cancel_appointment_enhanced),
                agents.function_tool(get_appointment_analytics),
                agents.function_tool(get_doctor_availability),
                
                # Legacy tools for backward compatibility
                agents.function_tool(register_patient_legacy),
                agents.function_tool(find_patient),
                agents.function_tool(get_available_slots),
                agents.function_tool(book_appointment),
                agents.function_tool(reschedule_appointment),
                agents.function_tool(cancel_appointment),
            ],
        )

# ------------------ Enhanced Entrypoint ------------------ #
async def entrypoint(ctx: agents.JobContext):
    """
    Enhanced entrypoint for the Apollo Assist LiveKit agent worker.
    """
    try:
        await ctx.connect()
        logger.info("LiveKit agent connected successfully")

        session = agents.AgentSession(
            allow_interruptions=True,
            # interrupt_speech_duration=1.5,  # Allow more natural interruptions
            # interrupt_silence_duration=1.0
        )

        await session.start(
            room=ctx.room,
            agent=ApolloAssistAgent(),
        )

        # Enhanced greeting with error handling
        try:
            await session.generate_reply(instructions=SESSION_INSTRUCTION)
            logger.info("Session started with greeting")
        except Exception as e:
            logger.error(f"Failed to generate initial greeting: {e}")
            # Fallback greeting
            await session.say("Hello, you are speaking with Apollo Assist. How may I help you today?")

    except Exception as e:
        logger.error(f"Agent entrypoint error: {e}")
        raise

if __name__ == "__main__":
    # Configure logging level based on environment
    log_level = logging.DEBUG if settings.RELOAD else logging.INFO
    logging.basicConfig(level=log_level)
    
    logger.info("Starting Apollo Assist Agent", 
               environment="development" if settings.RELOAD else "production")
    
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed to start: {e}")
        raise