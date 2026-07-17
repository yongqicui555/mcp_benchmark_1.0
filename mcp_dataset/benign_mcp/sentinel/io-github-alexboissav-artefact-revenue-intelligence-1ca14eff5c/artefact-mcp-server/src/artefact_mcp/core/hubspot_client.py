"""
HubSpot API Client

Fetches deal and company data from HubSpot API.
Uses httpx for async-compatible HTTP requests.
"""

import os
from datetime import datetime
from typing import Optional

import httpx


class HubSpotClient:
    """HubSpot API client for revenue intelligence data."""

    BASE_URL = "https://api.hubapi.com"
    MAX_PAGES = 50  # Safety limit: max 50 pages of 100 = 5,000 records

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("HUBSPOT_API_KEY")
        if not self._api_key:
            raise ValueError(
                "HubSpot API key required. Set HUBSPOT_API_KEY environment variable "
                "or pass api_key to constructor."
            )
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    @property
    def api_key(self) -> str:
        """Masked API key for safe display."""
        if self._api_key and len(self._api_key) > 8:
            return self._api_key[:4] + "..." + self._api_key[-4:]
        return "***"

    def __repr__(self) -> str:
        return f"HubSpotClient(api_key='{self.api_key}')"

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # --- Client Data (for RFM) ---

    def fetch_client_data(
        self,
        stage_filter: Optional[str] = "closedwon",
        limit: int = 100,
    ) -> list[dict]:
        """Fetch deals and aggregate by company for RFM analysis."""
        deals = self._fetch_deals(stage_filter, limit)

        company_ids = set()
        for deal in deals:
            assocs = (
                deal.get("associations", {}).get("companies", {}).get("results", [])
            )
            for assoc in assocs:
                company_ids.add(assoc.get("id"))

        companies = self._batch_fetch_companies(list(company_ids))
        return self._aggregate_by_company(deals, companies)

    # --- Open Deals (for Pipeline) ---

    def fetch_open_deals(self, pipeline_id: Optional[str] = None) -> list[dict]:
        """Fetch all open deals, optionally filtered by pipeline.

        Uses HubSpot's Search API to exclude closed stages reliably.
        First fetches pipeline definitions to identify closed stage IDs,
        then filters them out server-side.
        """
        # Step 1: Get all closed stage IDs across pipelines
        closed_stage_ids = self._get_closed_stage_ids(pipeline_id)

        # Step 2: Search for deals, excluding closed stages
        deals = []
        after = "0"
        pages = 0

        while pages < self.MAX_PAGES:
            pages += 1
            url = f"{self.BASE_URL}/crm/v3/objects/deals/search"

            filters = []
            if closed_stage_ids:
                filters.append({
                    "propertyName": "dealstage",
                    "operator": "NOT_IN",
                    "values": list(closed_stage_ids),
                })
            if pipeline_id:
                filters.append({
                    "propertyName": "pipeline",
                    "operator": "EQ",
                    "value": pipeline_id,
                })

            payload: dict = {
                "filterGroups": [{"filters": filters}] if filters else [],
                "properties": [
                    "dealname", "amount", "closedate", "dealstage",
                    "pipeline", "createdate", "hs_lastmodifieddate",
                ],
                "limit": 100,
                "after": after,
            }

            response = self._request("POST", url, json=payload)
            data = response.json()

            for deal in data.get("results", []):
                props = deal.get("properties", {})
                deals.append({
                    "id": deal.get("id"),
                    "name": props.get("dealname"),
                    "amount": self._safe_float(props.get("amount")),
                    "stage": props.get("dealstage", ""),
                    "pipeline": props.get("pipeline"),
                    "create_date": self._parse_date(props.get("createdate")),
                    "close_date": self._parse_date(props.get("closedate")),
                    "last_modified": self._parse_date(props.get("hs_lastmodifieddate")),
                })

            paging = data.get("paging", {})
            if paging.get("next"):
                after = paging["next"].get("after")
            else:
                break

        return deals

    def _get_closed_stage_ids(self, pipeline_id: Optional[str] = None) -> set[str]:
        """Fetch pipeline definitions and return IDs of all closed stages."""
        closed_ids: set[str] = set()
        url = f"{self.BASE_URL}/crm/v3/pipelines/deals"
        response = self._request("GET", url)
        data = response.json()

        for pipeline in data.get("results", []):
            if pipeline_id and pipeline.get("id") != pipeline_id:
                continue
            for stage in pipeline.get("stages", []):
                stage_id_val = stage.get("id", "")
                # HubSpot marks closed stages with metadata
                metadata = stage.get("metadata", {})
                if metadata.get("isClosed") == "true":
                    closed_ids.add(stage_id_val)
                # Fallback: catch common closed stage IDs
                if stage_id_val.lower() in ("closedwon", "closedlost"):
                    closed_ids.add(stage_id_val)
                # Fallback: catch stages with "closed won"/"closed lost" in label
                label = stage.get("label", "").lower()
                if "closed won" in label or "closed lost" in label:
                    closed_ids.add(stage_id_val)

        return closed_ids

    # --- Pipeline Stages (auto-detect) ---

    def fetch_pipeline_stages(self, pipeline_id: str = "default") -> list[dict]:
        """Fetch pipeline stage definitions in order from HubSpot.

        Returns list of dicts with 'id', 'label', and 'display_order'.
        """
        url = f"{self.BASE_URL}/crm/v3/pipelines/deals/{pipeline_id}"
        response = self._request("GET", url)
        data = response.json()

        stages = []
        for stage in data.get("stages", []):
            stages.append({
                "id": stage.get("id", ""),
                "label": stage.get("label", stage.get("id", "")),
                "display_order": stage.get("displayOrder", 0),
            })

        stages.sort(key=lambda s: s["display_order"])
        return stages

    # --- Deal Stage History (for Velocity) ---

    def fetch_deal_stage_history(self, deal_id: str) -> list[dict]:
        """Fetch stage change history for a specific deal."""
        url = f"{self.BASE_URL}/crm/v3/objects/deals/{deal_id}"
        params = {"propertiesWithHistory": "dealstage"}

        response = self._request("GET", url, params=params)
        data = response.json()

        history = []
        stage_versions = (
            data.get("propertiesWithHistory", {})
            .get("dealstage", [])
        )

        for i, version in enumerate(stage_versions):
            entered = self._parse_date(version.get("timestamp"))
            exited = None
            duration_days = None

            if i > 0:
                exited = self._parse_date(stage_versions[i - 1].get("timestamp"))
                if entered and exited:
                    duration_days = (exited - entered).days

            history.append({
                "stage": version.get("value"),
                "entered_at": entered.isoformat() if entered else None,
                "exited_at": exited.isoformat() if exited else None,
                "duration_days": duration_days,
            })

        return history

    # --- Company Lookup (for ICP) ---

    def fetch_company(self, company_id: str) -> dict:
        """Fetch a single company by ID."""
        url = f"{self.BASE_URL}/crm/v3/objects/companies/{company_id}"
        params = {
            "properties": "name,domain,industry,numberofemployees,annualrevenue,state,country,hs_analytics_source,lifecyclestage",
        }

        response = self._request("GET", url, params=params)
        data = response.json()

        props = data.get("properties", {})
        return {
            "id": data.get("id"),
            "name": props.get("name", "Unknown"),
            "domain": props.get("domain"),
            "industry": props.get("industry"),
            "employee_count": self._safe_int(props.get("numberofemployees")),
            "annual_revenue": self._safe_float(props.get("annualrevenue")),
            "geography": props.get("state") or props.get("country"),
        }

    def search_companies(self, query: str, limit: int = 10) -> list[dict]:
        """Search companies by name or domain."""
        url = f"{self.BASE_URL}/crm/v3/objects/companies/search"
        limit = min(limit, 100)  # Cap at HubSpot max
        payload = {
            "query": query,
            "limit": limit,
            "properties": [
                "name", "domain", "industry", "numberofemployees",
                "annualrevenue", "state", "country",
            ],
        }

        response = self._request("POST", url, json=payload)

        results = []
        for company in response.json().get("results", []):
            props = company.get("properties", {})
            results.append({
                "id": company.get("id"),
                "name": props.get("name", "Unknown"),
                "domain": props.get("domain"),
                "industry": props.get("industry"),
                "employee_count": self._safe_int(props.get("numberofemployees")),
                "annual_revenue": self._safe_float(props.get("annualrevenue")),
                "geography": props.get("state") or props.get("country"),
            })

        return results

    # --- Internal Helpers ---

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with error handling."""
        try:
            response = self._client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 401:
                raise ValueError(
                    "HubSpot API key is invalid or expired.\n\n"
                    "To fix this:\n"
                    "1. Go to HubSpot → Settings → Integrations → Private Apps\n"
                    "2. Create a new private app (or regenerate the token on your existing one)\n"
                    "3. Required scopes: crm.objects.deals.read, crm.objects.companies.read\n"
                    "4. Copy the access token and set it as HUBSPOT_API_KEY"
                ) from e
            elif status == 403:
                raise ValueError(
                    "HubSpot API key is missing required permissions.\n\n"
                    "To fix this:\n"
                    "1. Go to HubSpot → Settings → Integrations → Private Apps\n"
                    "2. Edit your private app's scopes\n"
                    "3. Enable: crm.objects.deals.read, crm.objects.companies.read\n"
                    "4. If using pipeline features, also enable: crm.objects.deals.write\n"
                    "5. Save and re-authorize the app"
                ) from e
            elif status == 429:
                raise ValueError(
                    "HubSpot API rate limit exceeded. Wait a few seconds and try again.\n"
                    "HubSpot allows 100 requests per 10 seconds for private apps."
                ) from e
            else:
                raise ValueError(f"HubSpot API error ({status}): {e.response.text[:200]}") from e
        except httpx.ConnectError as e:
            raise ValueError(
                "Cannot connect to HubSpot API. Check your internet connection.\n"
                "If you're behind a proxy or firewall, ensure api.hubapi.com is accessible."
            ) from e

    def _fetch_deals(self, stage_filter: Optional[str], limit: int) -> list[dict]:
        deals = []
        after = None
        pages = 0

        while pages < self.MAX_PAGES:
            pages += 1
            url = f"{self.BASE_URL}/crm/v3/objects/deals"
            params: dict = {
                "limit": limit,
                "properties": "dealname,amount,closedate,dealstage,pipeline",
                "associations": "companies",
            }
            if after:
                params["after"] = after

            response = self._request("GET", url, params=params)
            data = response.json()

            for deal in data.get("results", []):
                props = deal.get("properties", {})
                if stage_filter and props.get("dealstage", "").lower() != stage_filter:
                    continue
                deals.append({
                    "id": deal.get("id"),
                    "name": props.get("dealname"),
                    "amount": self._safe_float(props.get("amount")),
                    "close_date": self._parse_date(props.get("closedate")),
                    "stage": props.get("dealstage"),
                    "associations": deal.get("associations", {}),
                })

            paging = data.get("paging", {})
            if paging.get("next"):
                after = paging["next"].get("after")
            else:
                break

        return deals

    def _batch_fetch_companies(self, company_ids: list[str]) -> dict:
        if not company_ids:
            return {}

        companies = {}
        for i in range(0, len(company_ids), 100):
            batch = company_ids[i : i + 100]
            url = f"{self.BASE_URL}/crm/v3/objects/companies/batch/read"
            payload = {
                "inputs": [{"id": cid} for cid in batch],
                "properties": [
                    "name", "domain", "industry", "numberofemployees",
                    "annualrevenue", "state", "country",
                ],
            }

            response = self._request("POST", url, json=payload)

            for company in response.json().get("results", []):
                props = company.get("properties", {})
                companies[company.get("id")] = {
                    "id": company.get("id"),
                    "name": props.get("name", "Unknown"),
                    "domain": props.get("domain"),
                    "industry": props.get("industry"),
                    "employee_count": self._parse_employee_band(
                        props.get("numberofemployees")
                    ),
                    "company_revenue": self._parse_revenue_band(
                        props.get("annualrevenue")
                    ),
                    "state_region": props.get("state") or props.get("country"),
                }

        return companies

    def _aggregate_by_company(self, deals: list[dict], companies: dict) -> list[dict]:
        company_data: dict = {}

        for deal in deals:
            assocs = (
                deal.get("associations", {}).get("companies", {}).get("results", [])
            )
            if not assocs:
                continue

            company_id = assocs[0].get("id")
            if not company_id:
                continue

            if company_id not in company_data:
                company_info = companies.get(company_id, {})
                company_data[company_id] = {
                    "client_id": company_id,
                    "client_name": company_info.get("name", "Unknown"),
                    "total_revenue": 0,
                    "transaction_count": 0,
                    "last_purchase_date": None,
                    "industry": company_info.get("industry"),
                    "employee_count": company_info.get("employee_count"),
                    "company_revenue": company_info.get("company_revenue"),
                    "state_region": company_info.get("state_region"),
                }

            company_data[company_id]["total_revenue"] += deal.get("amount", 0)
            company_data[company_id]["transaction_count"] += 1

            close_date = deal.get("close_date")
            if close_date:
                current_last = company_data[company_id]["last_purchase_date"]
                if not current_last or close_date > current_last:
                    company_data[company_id]["last_purchase_date"] = close_date

        return list(company_data.values())

    def _safe_float(self, value) -> float:
        if not value:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, value) -> Optional[int]:
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _parse_employee_band(self, value) -> Optional[str]:
        if not value:
            return None
        try:
            count = int(value)
            if count <= 10:
                return "1-10"
            elif count <= 50:
                return "11-50"
            elif count <= 200:
                return "51-200"
            elif count <= 500:
                return "201-500"
            elif count <= 1000:
                return "501-1000"
            else:
                return "1000+"
        except (ValueError, TypeError):
            return str(value)

    def _parse_revenue_band(self, value) -> Optional[str]:
        if not value:
            return None
        try:
            revenue = float(value)
            if revenue < 1_000_000:
                return "<$1M"
            elif revenue < 5_000_000:
                return "$1M-$5M"
            elif revenue < 20_000_000:
                return "$5M-$20M"
            elif revenue < 70_000_000:
                return "$20M-$70M"
            else:
                return "$70M+"
        except (ValueError, TypeError):
            return str(value)
