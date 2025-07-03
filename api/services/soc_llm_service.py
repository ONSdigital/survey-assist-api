"""SOC LLM service for the Survey Assist API.

This module provides SOC (Standard Occupational Classification) classification
functionality using LLM and vector store integration.
"""

from typing import Any

from industrial_classification_utils.llm.llm import ClassificationLLM
from langchain.chains.llm import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts.prompt import PromptTemplate
from survey_assist_utils.logging import get_logger

from api.models.soc_classify import SocClassificationResponse

logger = get_logger(__name__)

# Constants
DEFAULT_CHARS_LIMIT = 14000
DEFAULT_CANDIDATES_LIMIT = 5
DEFAULT_CODE_DIGITS = 4


class SOCLLMService:  # pylint: disable=too-few-public-methods
    """Service for SOC classification using LLM and vector store.

    This class provides SOC classification functionality using a combination
    of vector store search and LLM processing.
    """

    def __init__(self, llm: ClassificationLLM):
        """Initialise the SOC LLM service.

        Args:
            llm: The ClassificationLLM instance to use for SOC classification.
        """
        self.llm = llm
        self._setup_soc_prompt()

    def _setup_soc_prompt(self) -> None:
        """Set up the SOC classification prompt template."""
        # Create a SOC-specific prompt template similar to the SIC one
        self.soc_prompt_template = PromptTemplate.from_template(
            """Given the respondent's job title, job description, and industry description,
            your task is to determine the most likely UK SOC (Standard Occupational Classification)
            codes for this job.

            The following will be provided to make your decision:
            Respondent Data
            Relevant subset of UK SOC codes (you must only use this list to classify)
            Output Format (the output format MUST be valid JSON)

            Only use the subset of UK SOC codes provided to determine if you can match the most
            likely SOC codes, provide a confidence score between 0 and 1 where 0.1 is least
            likely and 0.9 is most likely.

            You must return a subset list of possible SOC codes (UK SOC codes provided)
            that might match with a confidence score for each.

            You must provide a follow up question that would help identify the exact coding based
            on the list you respond with.

            ===Respondent Data===
            - Job Title: {job_title}
            - Job Description: {job_description}
            - Industry Description: {industry_descr}

            ===Relevant subset of UK SOC codes===
            {soc_index}

            ===Output Format===
            {format_instructions}

            ===Output===
            """
        )

    def _prompt_candidate_list(
        self,
        short_list: list[dict[str, Any]],
        chars_limit: int = DEFAULT_CHARS_LIMIT,
        candidates_limit: int = DEFAULT_CANDIDATES_LIMIT,
    ) -> str:
        """Create candidate list for the prompt based on the given parameters.

        Args:
            short_list: List of search results from vector store.
            chars_limit: Maximum number of characters for the prompt.
            candidates_limit: Maximum number of candidates to include.

        Returns:
            Formatted string of SOC candidates for the prompt.
        """
        if not short_list:
            return ""

        # Format candidates for the prompt
        soc_candidates = []
        for result in short_list[:candidates_limit]:
            code = result.get("code", "")
            title = result.get("title", "")
            distance = result.get("distance", 0.0)

            # Convert distance to similarity score (1 - distance)
            similarity = max(0.0, 1.0 - distance)

            candidate = (
                f"Code: {code}, Title: {title}, " f"Relevance Score: {similarity:.2f}"
            )
            soc_candidates.append(candidate)

        # Limit by character count if specified
        if chars_limit:
            total_chars = sum(len(candidate) for candidate in soc_candidates)
            if total_chars > chars_limit:
                # Simple truncation - in production you might want more sophisticated logic
                soc_candidates = soc_candidates[:3]  # Reduce to 3 candidates
                logger.warning(
                    "Shortening list of SOC candidates to fit character limit"
                )

        return "\n".join(soc_candidates)

    def sa_rag_soc_code(  # noqa: PLR0913 pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments,unused-argument
        self,
        industry_descr: str,
        job_title: str,
        job_description: str,
        short_list: list[dict[str, Any]],
        code_digits: int = DEFAULT_CODE_DIGITS,  # pylint: disable=unused-argument
        candidates_limit: int = DEFAULT_CANDIDATES_LIMIT,
    ) -> tuple[SocClassificationResponse, list[dict[str, Any]], dict[str, Any]]:
        """Generate SOC classification using RAG approach.

        Args:
            industry_descr: The industry description.
            job_title: The job title.
            job_description: The job description.
            short_list: List of search results from vector store.
            code_digits: Number of digits in SOC codes (default 4).
            candidates_limit: Maximum number of candidates to consider.

        Returns:
            Tuple containing:
            - SocClassificationResponse: The classification response
            - List of search results
            - Call dictionary used for the prompt
        """

        # Prepare call dictionary
        def prep_call_dict(
            industry_descr: str, job_title: str, job_description: str, soc_codes: str
        ) -> dict[str, Any]:
            """Helper function to prepare the call dictionary."""
            is_job_title_present = job_title is None or job_title.strip() in {"", " "}
            job_title = "Unknown" if is_job_title_present else job_title

            is_job_description_present = (
                job_description is None or job_description.strip() in {"", " "}
            )
            job_description = (
                "Unknown" if is_job_description_present else job_description
            )

            return {
                "industry_descr": industry_descr,
                "job_title": job_title,
                "job_description": job_description,
                "soc_index": soc_codes,
            }

        if not short_list:
            logger.warning("Empty short list provided for SOC classification")
            validated_answer = SocClassificationResponse(
                classified=False,
                followup=(
                    "Unable to find relevant SOC codes. "
                    "Please provide more specific job information."
                ),
                soc_code=None,
                soc_description=None,
                soc_candidates=[],
                reasoning="No relevant SOC codes found in vector store search.",
                prompt_used=None,
            )
            return validated_answer, [], {}

        # Format SOC codes for prompt
        soc_codes = self._prompt_candidate_list(
            short_list, candidates_limit=candidates_limit
        )

        call_dict = prep_call_dict(
            industry_descr=industry_descr,
            job_title=job_title,
            job_description=job_description,
            soc_codes=soc_codes,
        )

        # Create parser for the response
        parser = PydanticOutputParser(
            pydantic_object=SocClassificationResponse
        )  # type: ignore # Suspect langchain ver bug

        # Add format instructions to the call dictionary
        call_dict["format_instructions"] = parser.get_format_instructions()

        if self.llm.verbose:
            final_prompt = self.soc_prompt_template.format(**call_dict)
            logger.debug(
                "SOC classification prompt",
                prompt=final_prompt,
            )

        chain = LLMChain(llm=self.llm.llm, prompt=self.soc_prompt_template)

        try:
            response = chain.invoke(call_dict, return_only_outputs=True)
        except Exception as err:  # pylint: disable=broad-except
            logger.error("Error from LLMChain in SOC classification", error=str(err))
            logger.warning("Error from LLMChain, exit early", error=str(err))
            validated_answer = SocClassificationResponse(
                classified=False,
                followup="Follow-up question not available due to error.",
                soc_code=None,
                soc_description=None,
                soc_candidates=[],
                reasoning="Error from LLMChain, exit early",
                prompt_used=str(call_dict),
            )
            return validated_answer, short_list, call_dict

        if self.llm.verbose:
            logger.debug(
                "SOC LLM response",
                response=str(response),
            )

        # Parse the output to the desired format
        try:
            validated_answer = parser.parse(response["text"])
        except Exception as parse_error:  # pylint: disable=broad-except
            logger.error("Failed to parse SOC LLM response", error=str(parse_error))
            logger.warning("Failed to parse response", response=response["text"])

            reasoning = (
                f'ERROR parse_error=<{parse_error}>, response=<{response["text"]}>'
            )
            validated_answer = SocClassificationResponse(
                classified=False,
                followup="Follow-up question not available due to parsing error.",
                soc_code=None,
                soc_description=None,
                soc_candidates=[],
                reasoning=reasoning,
                prompt_used=str(call_dict),
            )

        return validated_answer, short_list, call_dict
