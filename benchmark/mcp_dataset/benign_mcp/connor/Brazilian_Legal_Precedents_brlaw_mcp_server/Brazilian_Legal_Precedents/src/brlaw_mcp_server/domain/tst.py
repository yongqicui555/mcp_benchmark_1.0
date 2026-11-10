import contextlib
import logging
from typing import TYPE_CHECKING, Self, override

from patchright.async_api import TimeoutError
from pydantic import field_validator

from brlaw_mcp_server.domain.base import BaseLegalPrecedent

if TYPE_CHECKING:
    from patchright.async_api import Page

_LOGGER = logging.getLogger(__name__)


class TstLegalPrecedent(BaseLegalPrecedent):
    """Model for a legal precedent from the Tribunal Superior do Trabalho (TST)."""

    @field_validator("summary")
    @classmethod
    def _remove_style_elements_from_summary(cls, v: str) -> str:
        """Remove style elements from the summary.

        On the TST website, the summary is split into multiple elements. In some cases,
        there's a <style> element among the <p> elements. Its data is not relevant at all to
        the summary, so we need to filter it out."""

        if not v.startswith("<!--"):
            return v

        for char_idx, char in enumerate(v):
            if char == ">" and v[char_idx - 2 : char_idx + 1] == "-->":
                return v[char_idx + 1 :].strip()

        raise RuntimeError(
            "Could not find the end of the style element inside the summary"
        )

    @override
    @classmethod
    async def research(
        cls, browser: "Page", *, summary_search_prompt: str, desired_page: int = 1
    ) -> "list[Self]":
        _LOGGER.info(
            "Starting research for legal precedents authored by the TST with the summary search prompt %s",
            repr(summary_search_prompt),
        )

        await browser.goto("https://jurisprudencia.tst.jus.br/")

        with contextlib.suppress(TimeoutError):
            await (
                browser.locator("span[class^='jss']")
                .filter(has_text="Fechar")
                .click(timeout=1000)
            )

        locator_summary_input = browser.locator("#campoTxtEmenta")
        await locator_summary_input.fill(summary_search_prompt)
        await locator_summary_input.press("Enter")

        await browser.locator("circle").wait_for(state="hidden", timeout=1000 * 30)

        precedents = [
            cls(summary=text)
            for locator in await browser.locator("div[id^=celulaLeiaMaisAcordao]").all()
            if (text := await locator.text_content()) is not None
        ]

        _LOGGER.info(
            "Found %d legal precedents",
            len(precedents),
        )

        return precedents
