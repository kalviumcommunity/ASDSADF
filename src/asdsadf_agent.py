import time
import logging
from typing import Optional, Dict, Any, List

from src.gemini_client import GeminiClient
from src.rag_system import RAGSystem
from src.models import UserQuery, QueryResponse
from src.config import settings

logger = logging.getLogger(__name__)


class ASDSADFAgent:
    def __init__(self):
        # Initialize RAG system instance first; GeminiClient requires rag_system
        self.rag = RAGSystem()
        # Instantiate GeminiClient with rag_system to match expected signature
        # Delay heavy initialization/testing to initialize()
        try:
            self.gemini = GeminiClient(self.rag)
        except TypeError:
            # If GeminiClient signature changed, try keyword form
            try:
                self.gemini = GeminiClient(rag_system=self.rag)
            except Exception as e:
                # Fall back to None and let initialize handle it
                logger.debug("GeminiClient construction deferred or failed: %s", e)
                self.gemini = None

        # Track whether Gemini is usable; if false we use local fallbacks
        self.gemini_available: bool = True
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.initialized = False

    async def initialize(self) -> bool:
        """
        Initialize RAG and test Gemini. If Gemini test fails (quota/network),
        start in degraded mode: RAG works and local fallbacks are used instead
        of Gemini. This avoids the server returning 500 "Agent not initialized".
        """
        # Initialize RAG system
        try:
            await self.rag.initialize()
            logger.info("RAG system initialized")
        except Exception as e:
            logger.error("Failed to initialize RAG system: %s", e)
            return False

        # Ensure GeminiClient exists and is constructed with rag
        if self.gemini is None:
            try:
                self.gemini = GeminiClient(self.rag)
            except TypeError:
                try:
                    self.gemini = GeminiClient(rag_system=self.rag)
                except Exception as e:
                    logger.error("Failed to construct GeminiClient: %s", e)
                    self.gemini = None

        # Test Gemini availability
        try:
            ok = await self._test_gemini()
            self.gemini_available = bool(ok)
            if not ok:
                logger.warning("Gemini API connection failed; entering degraded/local-fallback mode.")
            else:
                logger.info("Gemini API available.")
        except Exception as e:
            logger.error("Error during Gemini test: %s", e)
            self.gemini_available = False
            logger.warning("Entering degraded/local-fallback mode due to Gemini test error.")

        # Mark agent initialized regardless of Gemini status so API doesn't return 500
        self.initialized = True
        return True

    async def _test_gemini(self) -> bool:
        """
        Try a lightweight call to verify Gemini connectivity. Support different client APIs.
        """
        if not self.gemini:
            return False
        try:
            # Prefer an explicit test_connection method if present
            if hasattr(self.gemini, "test_connection"):
                res = await getattr(self.gemini, "test_connection")()
                return bool(res)
            # Try a tiny generate_response or generate call
            if hasattr(self.gemini, "generate_response"):
                try:
                    resp = await getattr(self.gemini, "generate_response")("OK", system_instruction="Reply with OK")
                    if resp and "OK" in str(resp):
                        return True
                except TypeError:
                    # maybe sync or different signature; try without system_instruction
                    resp = await getattr(self.gemini, "generate_response")("OK")
                    if resp and "OK" in str(resp):
                        return True
            # Last-resort: if gemini has synchronous test method
            if hasattr(self.gemini, "test"):
                res = getattr(self.gemini, "test")()
                return bool(res)
        except Exception as e:
            logger.error("Gemini test invocation failed: %s", e)
            return False
        return False

    def _is_roadmap_request(self, text: str) -> bool:
        keywords = ["roadmap", "learning path", "plan", "curriculum", "full-stack", "job-ready", "learning"]
        t = (text or "").lower()
        return any(k in t for k in keywords)

    async def process_query(self, request: UserQuery) -> QueryResponse:
        start = time.time()
        if not self.initialized:
            raise RuntimeError("Agent not initialized")

        # retrieve context
        try:
            retrieved: List[Dict[str, Any]] = await self.rag.search(request.message, top_k=settings.max_retrieval_results)
        except Exception as e:
            logger.warning("RAG search failed, continuing without context: %s", e)
            retrieved = []

        context = "\n---\n".join([f"Source: {r.get('source','')}\nTitle: {r.get('title','')}\nContent: {r.get('content','')[:1000]}" for r in retrieved])
        sources = list({r.get("source") for r in retrieved}) if retrieved else []

        # choose prompt and flow
        if self._is_roadmap_request(request.message):
            system_prompt = "You are ASDSADF, generate a learning roadmap in JSON following the schema. Provide phases, modules, resources. Use only free resources unless asked."
            schema_instruction = "Return JSON roadmap structure."

            # Use Gemini when available, fallback otherwise
            if self.gemini_available and self.gemini:
                try:
                    # detect structured method name variations
                    if hasattr(self.gemini, "generate_structured_response"):
                        res = await self.gemini.generate_structured_response(prompt=request.message, system_instruction=system_prompt, context=context, schema_instruction=schema_instruction)
                    elif hasattr(self.gemini, "generate_response"):
                        res_raw = await self.gemini.generate_response(request.message, system_instruction=system_prompt)
                        # If raw string returned, wrap minimally
                        res = {"text": res_raw}
                    else:
                        raise RuntimeError("No supported Gemini generation method found")
                except Exception as e:
                    logger.error("Error generating roadmap via Gemini: %s", e)
                    res = self._fallback_generate_roadmap(request, context)
            else:
                logger.info("Using local fallback generator for roadmap (Gemini unavailable).")
                res = self._fallback_generate_roadmap(request, context)

            # store roadmap in session if provided
            session_id = getattr(request, "session_id", None)
            if session_id:
                self.user_sessions.setdefault(session_id, {})["roadmap"] = res.get("roadmap") if isinstance(res, dict) else None

            processing_time = time.time() - start
            return QueryResponse(response=res, context_used=[context] if context else [], retrieval_sources=sources, processing_time=processing_time)

        # Non-roadmap Q/A path
        system_prompt = "You are ASDSADF, answer concisely and provide actionable steps. Return JSON with fields: explanation, key_points, next_steps."
        schema_instruction = 'Respond with JSON: {"explanation":"string","key_points":["string"],"next_steps":"string"}'

        if self.gemini_available and self.gemini:
            try:
                if hasattr(self.gemini, "generate_structured_response"):
                    res = await self.gemini.generate_structured_response(prompt=request.message, system_instruction=system_prompt, context=context, schema_instruction=schema_instruction)
                elif hasattr(self.gemini, "generate_response"):
                    res_raw = await self.gemini.generate_response(request.message, system_instruction=system_prompt)
                    res = {"text": res_raw}
                else:
                    raise RuntimeError("No supported Gemini generation method found")
            except Exception as e:
                logger.error("Error generating response via Gemini: %s", e)
                res = self._fallback_answer(request, context)
        else:
            logger.info("Using local fallback for Q/A (Gemini unavailable).")
            res = self._fallback_answer(request, context)

        processing_time = time.time() - start
        return QueryResponse(response=res, context_used=[context] if context else [], retrieval_sources=sources, processing_time=processing_time)

    # --- Fallback helpers for degraded/local mode ---

    def _fallback_generate_roadmap(self, request: UserQuery, context: str) -> Dict[str, Any]:
        """
        Generate a minimal roadmap JSON structure when Gemini is unavailable.
        This tries to be useful but is intentionally simple and deterministic.
        """
        # Basic heuristics: try to infer primary goal from message
        msg = (request.message or "").strip()
        primary_goal = "general software development"
        if "frontend" in msg.lower():
            primary_goal = "frontend developer"
        elif "full-stack" in msg.lower() or "full stack" in msg.lower():
            primary_goal = "full-stack developer"
        elif "react" in msg.lower():
            primary_goal = "React developer"

        # Get user profile from request if available
        current_level = "unknown"
        time_commitment = "unspecified"
        if hasattr(request, "user_profile") and request.user_profile:
            try:
                current_level = request.user_profile.get("current_level", "unknown")
                time_commitment = request.user_profile.get("time_commitment", "unspecified")
            except Exception:
                pass

        # assemble minimal roadmap
        roadmap = {
            "user_profile": {
                "current_level": current_level,
                "primary_goal": primary_goal,
                "timeline": "unspecified",
                "learning_style": "unspecified",
                "time_commitment": time_commitment
            },
            "roadmap": {
                "phases": [
                    {
                        "phase_id": 1,
                        "title": "Foundations",
                        "duration": "2-6 weeks",
                        "learning_objectives": ["Understand core concepts"],
                        "modules": [
                            {
                                "module_name": "Core Concepts",
                                "concepts": ["fundamentals"],
                                "resources": [
                                    {"type":"documentation","title":"MDN Web Docs","url":"https://developer.mozilla.org/","difficulty":"beginner","estimated_time":"varies"},
                                    {"type":"tutorial","title":"Free interactive tutorial","url":"https://www.freecodecamp.org/","difficulty":"beginner","estimated_time":"varies"}
                                ],
                                "hands_on_project": {
                                    "title":"Small foundation project",
                                    "description":"Build a small app to practice basics",
                                    "skills_practiced":["basics"],
                                    "deliverables":["repo","README"],
                                    "estimated_time":"1-2 weeks",
                                    "difficulty":"beginner"
                                },
                                "prerequisites":[],
                                "success_metrics":["Can explain core concepts"]
                            }
                        ]
                    },
                    {
                        "phase_id": 2,
                        "title": "Applied Learning",
                        "duration": "4-12 weeks",
                        "learning_objectives": ["Apply skills to projects"],
                        "modules": []
                    }
                ],
                "total_duration": "3 months (approx)",
                "difficulty_progression": ["beginner","intermediate"]
            },
            "milestone_checkpoints": ["Finish foundations project","Complete small applied project"],
            "next_steps": "Start with Phase 1: follow the listed resources and build the small project."
        }
        # Attach session_id if provided
        if getattr(request, "session_id", None):
            roadmap["session_id"] = request.session_id
        # Optionally include retrieved context snippet for user transparency
        if context:
            roadmap["context_preview"] = context[:2000]
        return roadmap

    def _fallback_answer(self, request: UserQuery, context: str) -> Dict[str, Any]:
        """
        Create a concise JSON answer when Gemini is unavailable.
        """
        msg = (request.message or "").strip()
        explanation = f"Received your query: {msg}. Gemini API is unavailable; returning a brief local suggestion."
        key_points = []

        if "roadmap" in msg.lower() or "learning" in msg.lower():
            key_points = [
                "Clarify your goal and time commitment",
                "Break learning into 3-4 progressive phases",
                "Prioritize hands-on projects"
            ]
            next_steps = "Provide your current skill level and weekly hours to get a tailored roadmap."
        else:
            key_points = ["Be specific about goal", "Ask for step-by-step plan or resources"]
            next_steps = "If you want more detail, try rephrasing with specifics (goal, timeline, weekly hours)."

        resp = {
            "explanation": explanation,
            "key_points": key_points,
            "next_steps": next_steps
        }
        if getattr(request, "session_id", None):
            resp["session_id"] = request.session_id
        if context:
            resp["context_preview"] = context[:1000]
        return resp


class ASASSDFAgent:
    """A slightly more featureful agent used by another API path.

    This class mirrors the same degraded-mode behavior and provides simple
    session handling and system-prompt loading.
    """

    def __init__(self):
        self.rag_system = RAGSystem()
        # Construct GeminiClient with rag_system to satisfy required arg
        try:
            self.gemini_client = GeminiClient(self.rag_system)
        except TypeError:
            try:
                self.gemini_client = GeminiClient(rag_system=self.rag_system)
            except Exception as e:
                logger.debug("ASASSDFAgent: GeminiClient construction failed: %s", e)
                self.gemini_client = None

        self.session_storage: Dict[str, Dict[str, Any]] = {}
        self.system_prompts = self._load_system_prompts()
        self.initialized = False
        self.api_quota_exceeded = False

    def _load_system_prompts(self) -> Dict[str, str]:
        prompts = {}
        prompts['zero_shot'] = "You are ASDSADF, provide helpful responses."
        prompts['one_shot'] = "You are ASDSADF, use the example to guide your response."
        prompts['multi_shot'] = "You are ASDSADF, use multiple examples to guide your response."
        prompts['dynamic'] = "You are ASDSADF, adapt your response based on context."
        prompts['chain_of_thought'] = "You are ASDSADF, think step by step."
        return prompts

    async def initialize(self) -> bool:
        try:
            await self.rag_system.initialize()
        except Exception as e:
            logger.error("ASASSDFAgent RAG init failed: %s", e)
            # still proceed in degraded mode
        # Test gemini_client if available
        if self.gemini_client:
            try:
                if hasattr(self.gemini_client, "test_connection"):
                    ok = await self.gemini_client.test_connection()
                elif hasattr(self.gemini_client, "generate_response"):
                    resp = await self.gemini_client.generate_response("OK", system_instruction="Reply with OK")
                    ok = resp and "OK" in str(resp)
                else:
                    ok = False
                self.api_quota_exceeded = not bool(ok)
                if self.api_quota_exceeded:
                    logger.warning("ASASSDFAgent: Gemini not available, using degraded mode.")
            except Exception as e:
                logger.error("ASASSDFAgent: Gemini test failed: %s", e)
                self.api_quota_exceeded = True
        else:
            self.api_quota_exceeded = True

        self.initialized = True
        return True

    async def process_query(self, query: UserQuery) -> Dict[str, Any]:
        if not self.initialized:
            raise RuntimeError("Agent not initialized")

        prompt_type = getattr(query, "prompt_type", None)
        prompt_key = prompt_type.value if hasattr(prompt_type, "value") else (prompt_type or "zero_shot")
        system_prompt = self.system_prompts.get(prompt_key, self.system_prompts.get('zero_shot'))
        enhanced = query.message or ""
        if getattr(query, "context", None):
            enhanced += f"\n\nContext: {query.context}"

        # Try Gemini if available
        if not self.api_quota_exceeded and self.gemini_client:
            try:
                if hasattr(self.gemini_client, "generate_response"):
                    response = await self.gemini_client.generate_response(enhanced, system_instruction=system_prompt)
                    return {"response": response, "session_id": getattr(query, "session_id", None)}
            except Exception as e:
                logger.error("Gemini error in ASASSDFAgent: %s", e)
                self.api_quota_exceeded = True

        # degraded fallback
        suggestion = "Gemini unavailable; provide more details or try again later."
        return {"error": "Gemini unavailable", "suggestion": suggestion, "session_id": getattr(query, "session_id", None)}

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        s = self.session_storage.get(session_id, {})
        return {"session_id": session_id, "exists": bool(s), "query_count": len(s.get('queries', []))}