"""
tests/conftest.py

Shared pytest fixtures used across unit, integration, and edge tests.
"""

import shutil
import tempfile
import pytest

from sa_resident_agent.crawlers.base_crawler import CrawledPage
from sa_resident_agent.knowledge.chunker import Chunker
from sa_resident_agent.knowledge.embedder import Embedder
from sa_resident_agent.knowledge.vector_store import VectorStore
from sa_resident_agent.agent.context import ContextManager


# ---------------------------------------------------------------------------
# Temporary ChromaDB directory
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def temp_chroma_dir():
    d = tempfile.mkdtemp(prefix="sa_test_chroma_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# Sample crawled pages
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_cps_page():
    return CrawledPage(
        url="https://www.cpsenergy.com/en/about-us/who-we-are/rates.html",
        provider="CPS_ENERGY",
        title="Rate Information | CPS Energy",
        text=(
            "CPS Energy offers residential electricity service to San Antonio customers. "
            "The average residential rate is approximately 8.8 cents per kilowatt-hour (kWh). "
            "New customers must provide a valid government-issued ID and proof of residence. "
            "Service can be started online, by phone, or in person at a CPS Energy office. "
            "A deposit may be required for customers without established credit history."
        ),
        scraped_at="2026-05-01T00:00:00+00:00",
    )


@pytest.fixture
def sample_saws_page():
    return CrawledPage(
        url="https://www.saws.org/service/start-stop-service/",
        provider="SAWS",
        title="Start Water Service | SAWS",
        text=(
            "To start SAWS water service, you will need to provide a valid photo ID, "
            "your service address, and a copy of your lease or proof of ownership. "
            "New residential accounts require a deposit of $50 to $150 depending on credit. "
            "Service activation typically takes 1-2 business days after your application is approved. "
            "You can apply online at saws.org or call customer service at 210-704-7297."
        ),
        scraped_at="2026-05-01T00:00:00+00:00",
    )


@pytest.fixture
def sample_city_page():
    return CrawledPage(
        url="https://www.sa.gov/Community/Housing-Neighborhoods",
        provider="CITY_SA",
        title="Residential Services | City of San Antonio",
        text=(
            "The City of San Antonio provides a range of services for new residents. "
            "You can register for solid waste collection, report issues via 311, "
            "and apply for building permits through the Development Services Department. "
            "New residents should contact 311 to set up garbage and recycling pickup. "
            "Permits are required for home improvements, additions, and new construction."
        ),
        scraped_at="2026-05-01T00:00:00+00:00",
    )


@pytest.fixture
def all_sample_pages(sample_cps_page, sample_saws_page, sample_city_page):
    return [sample_cps_page, sample_saws_page, sample_city_page]


# ---------------------------------------------------------------------------
# Core components
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def chunker():
    return Chunker()


@pytest.fixture(scope="session")
def embedder():
    return Embedder()


@pytest.fixture(scope="session")
def vector_store(temp_chroma_dir):
    return VectorStore(persist_path=temp_chroma_dir)


@pytest.fixture(scope="session")
def populated_store(temp_chroma_dir, embedder):
    """VectorStore pre-loaded with sample chunks from all three providers."""
    pages = [
        CrawledPage(
            url="https://www.cpsenergy.com/rates",
            provider="CPS_ENERGY",
            title="CPS Energy Rates",
            text=(
                "CPS Energy residential electricity rate is 8.8 cents per kWh. "
                "New customers need a government-issued ID and proof of residence. "
                "A deposit may be required. Service starts within 1-2 business days. "
                "Payment options include autopay, online, phone, and in-person."
            ),
            scraped_at="2026-05-01T00:00:00+00:00",
        ),
        CrawledPage(
            url="https://www.saws.org/service/start",
            provider="SAWS",
            title="Start SAWS Service",
            text=(
                "SAWS water service requires a photo ID, lease agreement, and deposit of $50-$150. "
                "Apply online at saws.org or call 210-704-7297. "
                "Service activation takes 1-2 business days. "
                "Monthly bills include water, sewer, and stormwater charges."
            ),
            scraped_at="2026-05-01T00:00:00+00:00",
        ),
        CrawledPage(
            url="https://www.sa.gov/Directory/Departments/DSD/Constructing/Residential/Permits",
            provider="CITY_SA",
            title="City of SA Residential Services",
            text=(
                "New San Antonio residents can set up garbage and recycling via 311. "
                "Building permits are required for home improvements. "
                "Contact the Development Services Department for permit applications. "
                "Report issues to 311 online or by calling 3-1-1."
            ),
            scraped_at="2026-05-01T00:00:00+00:00",
        ),
    ]
    chunker = Chunker()
    chunks = chunker.chunk_all(pages)
    embeddings = embedder.embed_chunks(chunks)
    store = VectorStore(persist_path=temp_chroma_dir)
    store.add_chunks(chunks, embeddings)
    return store


@pytest.fixture
def context_manager():
    return ContextManager()


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------

class MockLLM:
    """Deterministic mock — no network needed."""

    def chat(self, messages: list[dict], **kwargs) -> str:
        user_msg   = next((m["content"] for m in messages if m["role"] == "user"),   "").lower()
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "").lower()

        # Intent classification (low max_tokens signals this is a classification call)
        if kwargs.get("max_tokens", 512) <= 10:
            if any(w in user_msg for w in ["form", "field", "enter", "fill"]):
                return "FORM_HELP"
            if any(w in user_msg for w in ["status", "progress", "completed", "left"]):
                return "STATUS"
            return "QUESTION"

        if "checklist" in system_msg and "progress" in system_msg:
            return (
                "Your utility setup progress:\n"
                "- CPS Energy: Not started\n"
                "- SAWS: Not started\n"
                "- City of SA: Not started\n"
                "Start with CPS Energy to get electricity set up first."
            )

        if "form" in system_msg or "field" in system_msg:
            return (
                "For the service address field, enter the full street address "
                "of your new San Antonio residence. Example: 1 UTSA Circle, San Antonio, TX 78249."
            )

        return (
            "CPS Energy residential customers pay approximately 8.8 cents per kilowatt-hour. "
            "New customers need a valid ID and proof of residence to start service."
        )

    def is_reachable(self) -> bool:
        return True

    def close(self):
        pass


@pytest.fixture(scope="module")
def mock_llm():
    return MockLLM()
