"""
Mock Claude API client used for local development and testing without real API calls.
"""

from __future__ import annotations

from typing import Dict, Any


class MockClaudeAPIClient:
    """Light-weight Claude API stub that returns deterministic JSON payloads."""

    def __init__(self):
        self.api_key = "mock-api-key"
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4000
        self.timeout = 60
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0

    async def generate_response(self, prompt: str, system_prompt: str | None = None, **_: Any) -> str:
        """Return canned responses based on keywords."""
        self.total_requests += 1
        self.total_tokens += 100

        lowered = prompt.lower()
        if "frontend" in lowered or "前端" in prompt:
            return self._get_frontend_response()
        if "backend" in lowered or "后端" in prompt:
            return self._get_backend_response()
        if "测试" in prompt:
            return "API连接测试成功！模拟响应正常工作。"
        return "这是一个模拟的API响应，系统正在正常工作。"

    async def generate_response_with_retry(self, prompt: str, **kwargs: Any) -> str:
        """Keep the same signature as the real client."""
        return await self.generate_response(prompt, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Return counters similar to the real client."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "error_rate": 0.0,
            "avg_tokens_per_request": self.total_tokens / max(self.total_requests, 1),
        }

    def reset_stats(self):
        """Reset collected counters."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0

    def _get_frontend_response(self) -> str:
        return """
{
  "components": {
    "App.vue": "<template>\\n  <div id=\\"app\\">\\n    <h1>测试应用</h1>\\n  </div>\\n</template>\\n<script>\\nexport default { name: 'App' }\\n</script>"
  },
  "styles": {
    "main.css": "body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }"
  },
  "config": {
    "vite.config.js": "import { defineConfig } from 'vite'\\nimport vue from '@vitejs/plugin-vue'\\n\\nexport default defineConfig({ plugins: [vue()] })"
  },
  "package_json": {
    "package.json": "{\\"name\\": \\"test-app\\", \\"version\\": \\"1.0.0\\", \\"dependencies\\": {\\"vue\\": \\"^3.0.0\\"}}"
  }
}
""".strip()

    def _get_backend_response(self) -> str:
        return """
{
  "models": {
    "user.py": "from sqlalchemy import Column, Integer, String\\nfrom database import Base\\n\\nclass User(Base):\\n    __tablename__ = 'users'\\n    id = Column(Integer, primary_key=True)\\n    name = Column(String(50))\\n    email = Column(String(100))"
  },
  "views": {
    "user_views.py": "from fastapi import APIRouter\\nfrom models.user import User\\n\\nrouter = APIRouter()\\n\\n@router.get('/users')\\nasync def get_users():\\n    return {'users': []}"
  },
  "services": {
    "user_service.py": "class UserService:\\n    async def get_all_users(self):\\n        return []"
  },
  "utils": {
    "database.py": "from sqlalchemy import create_engine\\nfrom sqlalchemy.ext.declarative import declarative_base\\n\\nBase = declarative_base()"
  },
  "config": {
    "main.py": "from fastapi import FastAPI\\nfrom views.user_views import router\\n\\napp = FastAPI()\\napp.include_router(router)"
  },
  "requirements": {
    "requirements.txt": "fastapi==0.104.1\\nuvicorn==0.24.0\\nsqlalchemy==2.0.23"
  }
}
""".strip()
