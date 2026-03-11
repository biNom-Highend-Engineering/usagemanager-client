from datetime import datetime
from typing import Optional

import httpx


class UsageManagerClient:
    """Async HTTP client for the centralized Usage Manager service."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        app_name: str,
        timeout: float = 10.0,
    ):
        self._app_name = app_name
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def record_usage(
        self,
        company: str,
        user_email: str,
        profile_name: str,
        cost: float,
        department: Optional[str] = None,
        jobtitle: Optional[str] = None,
    ) -> dict:
        """
        Record a usage entry. Returns:
        {
            "status": "ok",
            "monthly_total": float,
            "usage_limit": float | None,
            "limit_exceeded": bool | None
        }
        """
        payload = {
            "app_name": self._app_name,
            "company": company,
            "user_email": user_email,
            "profile_name": profile_name,
            "cost": cost,
            "department": department,
            "jobtitle": jobtitle,
        }
        resp = await self._client.post("/usage/record", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_company_monthly_usage(
        self,
        company: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> dict:
        """
        Get company monthly usage with per-app breakdown. Returns:
        {
            "company": str,
            "year": int,
            "month": int,
            "total_cost": float,
            "per_app": [{"app_name": str, "total_cost": float}]
        }
        """
        params = {}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        resp = await self._client.get(
            f"/usage/company/{company}/monthly", params=params
        )
        resp.raise_for_status()
        return resp.json()

    async def get_user_monthly_usage(
        self,
        company: str,
        user_email: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> dict:
        """
        Get user monthly usage with per-app breakdown. Returns:
        {
            "company": str,
            "user_email": str,
            "year": int,
            "month": int,
            "total_cost": float,
            "per_app": [{"app_name": str, "total_cost": float}]
        }
        """
        params = {}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        resp = await self._client.get(
            f"/usage/company/{company}/user/{user_email}/monthly", params=params
        )
        resp.raise_for_status()
        return resp.json()

    async def check_limit_exceeded(self, company: str) -> bool:
        """Returns True if the company exceeded its monthly limit."""
        resp = await self._client.get(f"/usage/company/{company}/limit")
        resp.raise_for_status()
        return resp.json()["exceeded"]

    async def get_limit_status(self, company: str) -> dict:
        """
        Get detailed limit status. Returns:
        {
            "company": str,
            "current_usage": float,
            "usage_limit": float | None,
            "percentage": float | None,
            "exceeded": bool
        }
        """
        resp = await self._client.get(f"/usage/company/{company}/limit/status")
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.aclose()
