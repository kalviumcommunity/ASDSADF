import google.generativeai as genai
import asyncio
import json
import re
import logging
from typing import Optional, Dict, Any

from src.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required in environment")
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        # conservative generation config
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            top_p=0.8,
            top_k=40,
            max_output_tokens=1024
        )

    async def generate_response(self, prompt: str, system_instruction: Optional[str]=None, context: Optional[str]=None) -> str:
        full = ""
        if system_instruction:
            full += f"SYSTEM:\n{system_instruction}\n\n"
        if context:
            full += f"CONTEXT:\n{context}\n\n"
        full += f"USER:\n{prompt}"
        try:
            resp = await asyncio.to_thread(self.model.generate_content, full, generation_config=self.generation_config)
            # resp may be object; try to get text
            text = getattr(resp, "text", None) or str(resp)
            return text
        except Exception as e:
            logger.error("Gemini generate error: %s", e)
            raise

    def _extract_json(self, text: str) -> str:
        if not text:
            raise ValueError("Empty response")
        text = text.strip()
        # remove triple-backtick fenced blocks if present
        if text.startswith("```"):
            # remove first fence
            parts = text.split("```", 2)
            if len(parts) >= 3:
                text = parts[1]
        # find first `{` and matching `}`
        start = text.find('{')
        if start == -1:
            # attempt to find JSON array
            start = text.find('[')
            if start == -1:
                return text
        # find matching bracket by counting
        stack = []
        end = None
        for i, ch in enumerate(text[start:], start):
            if ch in '{[':
                stack.append(ch)
            elif ch in '}]':
                if not stack:
                    continue
                opening = stack.pop()
                if (opening == '{' and ch == '}') or (opening == '[' and ch == ']'):
                    if not stack:
                        end = i + 1
                        break
        if end is None:
            # fallback: return full text
            return text
        return text[start:end]

    async def generate_structured_response(self, prompt: str, system_instruction: str, context: Optional[str]=None, schema_instruction: Optional[str]=None) -> Dict[str, Any]:
        instr = system_instruction or ""
        if schema_instruction:
            instr += "\n\n" + schema_instruction
        text = await self.generate_response(prompt=prompt, system_instruction=instr, context=context)
        try:
            json_text = self._extract_json(text)
            return json.loads(json_text)
        except Exception:
            # return raw text fallback inside a dict
            logger.warning("Failed to parse JSON, returning raw text")
            return {"raw_response": text}

    async def test_connection(self) -> bool:
        try:
            res = await self.generate_response("Hello, respond OK", system_instruction="Respond with exactly: OK")
            return "OK" in res
        except Exception as e:
            logger.error("Gemini test connection failed: %s", e)
            return False
import google.generativeai as genai
import json
import asyncio
from typing import Dict, Any, Optional, List
from src.config import settings
from src.rag_system import RAGSystem
import logging
import re

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google's Gemini API with RAG integration."""
    
    def __init__(self, rag_system: RAGSystem):
        """Initialize the Gemini client with RAG system."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        self.rag_system = rag_system
        
        # Configure generation parameters for JSON responses
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # Low temperature for consistent, factual responses
            top_p=0.8,
            top_k=40,
            max_output_tokens=4096,
        )
    
    async def generate_response(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        context: Optional[str] = None,
        use_rag: bool = True
    ) -> str:
        """
        Generate a response using Gemini API with optional RAG context.
        
        Args:
            prompt: User's query/prompt
            system_instruction: System-level instructions
            context: Additional context (if not using RAG)
            use_rag: Whether to use RAG for context retrieval
            
        Returns:
            Generated response string
        """
        try:
            # Get RAG context if enabled
            rag_context = ""
            if use_rag and self.rag_system:
                rag_results = await self.rag_system.search(
                    prompt, 
                    top_k=settings.max_retrieval_results
                )
                if rag_results:
                    rag_context = self._format_rag_context(rag_results)
            
            # Construct full prompt
            full_prompt = ""
            
            if system_instruction:
                full_prompt += f"SYSTEM INSTRUCTION:\n{system_instruction}\n\n"
            
            if rag_context:
                full_prompt += f"RELEVANT KNOWLEDGE:\n{rag_context}\n\n"
            
            if context:
                full_prompt += f"ADDITIONAL CONTEXT:\n{context}\n\n"
            
            full_prompt += f"USER QUERY:\n{prompt}"
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config=self.generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_structured_response(
        self, 
        prompt: str, 
        system_instruction: str,
        context: Optional[str] = None,
        use_rag: bool = True,
        schema_instruction: str = "Respond with valid JSON only. Do not include any text outside the JSON structure."
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON response.
        
        Args:
            prompt: User's query
            system_instruction: System instructions
            context: Additional context
            use_rag: Whether to use RAG for context retrieval
            schema_instruction: JSON schema instructions
            
        Returns:
            Parsed JSON response as dictionary
        """
        try:
            # Add JSON format instruction
            enhanced_system = f"{system_instruction}\n\n{schema_instruction}"
            
            response_text = await self.generate_response(
                prompt=prompt,
                system_instruction=enhanced_system,
                context=context,
                use_rag=use_rag
            )
            
            # Clean and parse JSON
            json_text = self._extract_json(response_text)
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response_text}")
            # Return a fallback response
            return {
                "error": "Failed to generate structured response",
                "raw_response": response_text,
                "user_profile": {"current_level": "unknown"},
                "roadmap": {"phases": []},
                "milestones": [],
                "next_steps": "Please try rephrasing your request."
            }
        except Exception as e:
            logger.error(f"Error generating structured response: {e}")
            raise
    
    def _format_rag_context(self, rag_results: List[Dict[str, Any]]) -> str:
        """Format RAG search results into context string."""
        if not rag_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(rag_results, 1):
            context_parts.append(
                f"Document {i}: {result['title']}\n"
                f"Source: {result['source']}\n"
                f"Content: {result['content']}\n"
                f"Topics: {', '.join(result.get('metadata', {}).get('topics', []))}\n"
            )
        
        return "\n".join(context_parts)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from response text."""
        # Try to find JSON within the response
        text = text.strip()
        
        # Look for JSON block markers
        json_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1)
        
        # If no JSON markers found, assume entire text is JSON
        return text
    
    async def test_connection(self) -> bool:
        """Test the connection to Gemini API."""
        try:
            response = await self.generate_response(
                "Hello, please respond with a simple greeting.",
                use_rag=False
            )
            return bool(response and len(response) > 0)
        except Exception as e:
            logger.error(f"Gemini API connection test failed: {e}")
            return False