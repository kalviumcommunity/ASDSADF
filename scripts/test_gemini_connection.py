# filepath: /home/kali/work/kalvium/ASDSADF/scripts/test_gemini_connection.py
import sys
import os
import asyncio
import traceback
from importlib import import_module

# Ensure project root on sys.path so src imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def mask_key(k: str) -> str:
    if not k:
        return "<empty>"
    if len(k) <= 8:
        return "<redacted>"
    return f"{k[:4]}...{k[-4:]}"

def print_env():
    print("="*80)
    print("ENV VARS (masked):")
    print("GEMINI_API_KEY:", mask_key(os.environ.get("GEMINI_API_KEY", "")))
    print("GEMINI_MODEL:", os.environ.get("GEMINI_MODEL", ""))
    print("CHROMA_PERSIST_DIRECTORY:", os.environ.get("CHROMA_PERSIST_DIRECTORY", ""))
    print()

async def run_test():
    try:
        gemini_module = import_module("src.gemini_client")
    except Exception as e:
        print("Failed importing src.gemini_client:", repr(e))
        traceback.print_exc()
        return False

    GeminiClient = getattr(gemini_module, "GeminiClient", None)
    if GeminiClient is None:
        print("GeminiClient class not found in src.gemini_client")
        return False

    client = None
    # Try several instantiation strategies to match repo variants
    try:
        client = GeminiClient()  # prefer no-arg if available
        print("Instantiated GeminiClient() without args")
    except TypeError as e:
        print("GeminiClient() requires args, trying with None:", repr(e))
        try:
            client = GeminiClient(None)
            print("Instantiated GeminiClient(None)")
        except Exception as e2:
            print("Failed to instantiate GeminiClient with None:", repr(e2))
            # Try to import RAGSystem and pass a minimal instance (without heavy initialize)
            try:
                rag_mod = import_module("src.rag_system")
                RAGSystem = getattr(rag_mod, "RAGSystem", None)
                if RAGSystem:
                    rag = RAGSystem()
                    client = GeminiClient(rag)
                    print("Instantiated GeminiClient with RAGSystem instance (did not call initialize())")
                else:
                    print("RAGSystem class not found; cannot instantiate GeminiClient")
                    return False
            except Exception as e3:
                print("Failed to import/create RAGSystem:", repr(e3))
                traceback.print_exc()
                return False
    except Exception as e:
        print("Unexpected error instantiating GeminiClient:", repr(e))
        traceback.print_exc()
        return False

    # Call test_connection
    try:
        if not hasattr(client, "test_connection"):
            print("GeminiClient has no test_connection method; attempting simple generate_response call as fallback.")
            # Try generate_response if available
            if hasattr(client, "generate_response"):
                res = await client.generate_response("Hello, respond with OK", system_instruction="Respond with exactly: OK")
                print("generate_response result (fallback):", res)
                return "OK" in (res or "")
            else:
                print("No generate_response available; cannot test connection.")
                return False

        ok = await client.test_connection()
        print("test_connection result:", ok)
        return ok
    except Exception as e:
        print("Error while calling test_connection():", repr(e))
        traceback.print_exc()
        return False

def main():
    print_env()
    try:
        ok = asyncio.run(run_test())
        if not ok:
            print("\nGemini connectivity test failed. Check GEMINI_API_KEY in .env and network access. If you do not have a valid key, set GEMINI_API_KEY to an empty string or modify src/asdsadf_agent.py to bypass Gemini for local testing.")
            sys.exit(2)
        else:
            print("\nGemini connectivity OK")
            sys.exit(0)
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()