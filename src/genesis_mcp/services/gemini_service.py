"""
GeminiCLI service for Genesis MCP server
Provides integration with Google's Gemini API
"""

import json
import logging
import os
import asyncio
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class GeminiCLIService:
    """Service for interacting with Gemini API"""
    
    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Initialize GeminiCLI service
        
        Args:
            model: Gemini model to use (default: gemini-2.5-flash)
        """
        self.model = model
        
        # .envファイルから環境変数を読み込み
        self._load_env_file()
        
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        
        # Verify API availability
        self._verify_api_setup()
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        from pathlib import Path
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            logger.debug(f"Loaded .env file: {env_file}")
        else:
            logger.debug(f".env file not found: {env_file}")
    
    def _verify_api_setup(self) -> None:
        """Verify that Gemini API is properly configured"""
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            # Don't raise error - allow fallback mode
            return
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # 利用可能なモデルをチェック（最新順）
            available_models = [
                "gemini-2.5-flash",          # 優先: Gemini 2.5 Flash
                "gemini-2.0-flash",          # フォールバック: Gemini 2.0
                "gemini-flash-latest",       # フォールバック: 最新Flash
                "gemini-1.5-flash",          # 従来版フォールバック
                "gemini-1.5-pro"             # 最終フォールバック
            ]
            
            for model_name in available_models:
                try:
                    self.client = genai.GenerativeModel(model_name)
                    self.model = model_name
                    logger.info(f"✅ Gemini API configured successfully with model: {model_name}")
                    break
                except Exception as model_error:
                    logger.debug(f"Model {model_name} not available: {model_error}")
                    continue
            
            if not self.client:
                raise Exception("No compatible Gemini model found")
                
        except ImportError:
            logger.error("google-generativeai package not installed")
            logger.info("Install with: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Gemini API configuration error: {e}")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Gemini API
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        if not self.client:
            logger.warning("🔄 Gemini API client not available, using fallback")
            return self._fallback_response(prompt)
        
        # デバッグ情報
        logger.info(f"🤖 Gemini API リクエスト送信中...")
        logger.debug(f"プロンプト長: {len(prompt)} 文字")
        
        try:
            # Configure generation parameters
            generation_config = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            
            # Generate response
            response = await asyncio.to_thread(
                self.client.generate_content,
                prompt,
                generation_config=generation_config if generation_config else None
            )
            
            result = response.text.strip()
            
            # 成功ログ
            logger.info(f"✅ Gemini API 応答受信 (長さ: {len(result)} 文字)")
            logger.debug(f"Gemini response: {result[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini API エラー: {e}")
            logger.warning("🔄 フォールバックレスポンスを使用")
            return self._fallback_response(prompt)
    
    async def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate structured JSON response using Gemini API
        
        Args:
            prompt: Input text prompt (should specify JSON format requirement)
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        if not self.client:
            return {"text": self._fallback_response(prompt), "source": "fallback"}
        
        try:
            # Add JSON format instruction to prompt
            json_prompt = f"{prompt}\n\nPlease respond with valid JSON format only."
            
            # Generate response
            response = await asyncio.to_thread(
                self.client.generate_content,
                json_prompt
            )
            
            response_text = response.text.strip()
            
            # Parse JSON
            try:
                response_json = json.loads(response_text)
                logger.debug(f"Gemini JSON response keys: {list(response_json.keys())}")
                return response_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response_text}")
                # Fallback: return as text in JSON structure
                return {"text": response_text, "error": "Failed to parse as JSON"}
                
        except Exception as e:
            logger.error(f"Error in generate_json: {e}")
            return {"text": self._fallback_response(prompt), "error": str(e)}
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat-style interaction with Gemini
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        try:
            # Convert messages to single prompt
            prompt_parts = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'system':
                    prompt_parts.append(f"System: {content}")
                elif role == 'user':
                    prompt_parts.append(f"User: {content}")
                elif role == 'assistant':
                    prompt_parts.append(f"Assistant: {content}")
            
            full_prompt = "\n".join(prompt_parts)
            return await self.generate_text(full_prompt, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return self._fallback_response("Chat interaction")
    
    def sync_generate_text(self, prompt: str, **kwargs) -> str:
        """
        Synchronous version of generate_text
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        if not self.client:
            return self._fallback_response(prompt)
        
        try:
            # Configure generation parameters
            generation_config = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            
            # Generate response
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config if generation_config else None
            )
            
            result = response.text
            logger.debug(f"Gemini response: {result[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error in sync_generate_text: {e}")
            return self._fallback_response(prompt)
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Gemini models
        
        Returns:
            List of available model names
        """
        if not self.client:
            return [self.model]  # Return default model if API not available
        
        try:
            # Return commonly available Gemini models
            return [
                "gemini-pro",
                "gemini-pro-vision", 
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ]
            
        except Exception as e:
            logger.error(f"Error in get_available_models: {e}")
            return [self.model]  # Return default model as fallback
    
    def _fallback_response(self, prompt: str) -> str:
        """
        Provide fallback response when Gemini API is not available
        
        Args:
            prompt: Original prompt
            
        Returns:
            Fallback response
        """
        return f"""# Fallback Genesis Code (GeminiAPI not available)
import genesis as gs
import time
import math

# Genesis初期化
# gs.init(backend=gs.cpu)  # 自動初期化されます

# シーン作成
scene = gs.Scene(show_viewer=False)

# 基本オブジェクト作成
sphere = scene.add_entity(gs.morphs.Sphere(radius=0.5))

# シーンビルド
scene.build()

# 位置設定
sphere.set_pos((0, 0, 2))

print("🎯 フォールバックシミュレーション開始")

# シミュレーション実行
for i in range(100):
    scene.step()
    if i % 20 == 0:
        print(f"Step: {{i}}")
        time.sleep(0.01)

print("✅ シミュレーション完了")
"""