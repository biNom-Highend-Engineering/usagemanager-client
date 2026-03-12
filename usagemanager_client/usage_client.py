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

    async def record_usage_batch(
        self,
        company: str,
        users_data: dict,
    ) -> dict:
        """
        Record a batch of usage entries using the legacy nested users_data shape.
        Returns:
        {
            "status": "ok",
            "monthly_total": float,
            "usage_limit": float | None,
            "limit_exceeded": bool | None,
            "records_processed": int | None
        }
        """
        payload = {
            "app_name": self._app_name,
            "company": company,
            "users_data": users_data,
        }
        resp = await self._client.post("/usage/record/batch", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_company_monthly_usage(
        self,
        company: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> dict:
        """
        Get company monthly usage with per-app and per-profile breakdowns. Returns:
        {
            "company": str,
            "year": int,
            "month": int,
            "total_cost": float,
            "per_app": [{"app_name": str, "total_cost": float}],
            "per_profile": [{"profile_name": str, "total_cost": float}]
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
        Get user monthly usage with per-app and per-profile breakdowns. Returns:
        {
            "company": str,
            "user_email": str,
            "year": int,
            "month": int,
            "total_cost": float,
            "per_app": [{"app_name": str, "total_cost": float}],
            "per_profile": [{"profile_name": str, "total_cost": float}]
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

    async def get_detailed_monthly_usage(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        company: Optional[str] = None,
    ) -> dict:
        """
        Get a detailed monthly usage report across all companies or one company.
        Returns:
        {
            "year": int,
            "month": int,
            "total_cost": float,
            "companies": [
                {
                    "company": str,
                    "total_cost": float,
                    "per_app": [{"app_name": str, "total_cost": float}],
                    "per_department": [{"department": str, "total_cost": float}],
                    "per_profile": [{"profile_name": str, "total_cost": float}],
                    "users": [
                        {
                            "user_email": str,
                            "department": str | None,
                            "jobtitle": str | None,
                            "total_cost": float,
                            "per_app": [{"app_name": str, "total_cost": float}],
                            "per_profile": [{"profile_name": str, "total_cost": float}]
                        }
                    ]
                }
            ]
        }
        """
        params = {}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        if company is not None:
            params["company"] = company
        resp = await self._client.get("/usage/monthly/detailed", params=params)
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
