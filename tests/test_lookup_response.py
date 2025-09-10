"""Tests for the LookupResponse model."""

from api.models.result import LookupResponse, PotentialCode, PotentialDivision


class TestLookupResponse:
    """Test class for LookupResponse model."""

    def test_lookup_response_with_match(self):
        """Test LookupResponse with a successful match."""
        response = LookupResponse(
            found=True,
            code="56302",
            code_division="56",
            potential_codes_count=0,
            potential_divisions=[],
            potential_codes=[],
        )

        assert response.found is True
        assert response.code == "56302"
        assert response.code_division == "56"
        assert response.potential_codes_count == 0
        assert response.potential_divisions == []
        assert response.potential_codes == []

    def test_lookup_response_no_match(self):
        """Test LookupResponse with no match."""
        response = LookupResponse(
            found=False,
            code=None,
            code_division=None,
            potential_codes_count=0,
            potential_divisions=[],
            potential_codes=[],
        )

        assert response.found is False
        assert response.code is None
        assert response.code_division is None
        assert response.potential_codes_count == 0
        assert response.potential_divisions == []
        assert response.potential_codes == []

    def test_lookup_response_with_potential_matches(self):
        """Test LookupResponse with potential matches."""
        potential_divisions = [
            PotentialDivision(code="56", title="Food and beverage service activities")
        ]
        potential_codes = [
            PotentialCode(code="56302", description="Public houses and bars")
        ]

        response = LookupResponse(
            found=False,
            code=None,
            code_division=None,
            potential_codes_count=1,
            potential_divisions=potential_divisions,
            potential_codes=potential_codes,
        )

        assert response.found is False
        assert response.code is None
        assert response.code_division is None
        assert response.potential_codes_count == 1
        assert len(response.potential_divisions) == 1
        assert len(response.potential_codes) == 1
        assert response.potential_divisions[0].code == "56"
        assert response.potential_codes[0].code == "56302"

    def test_lookup_response_serialization(self):
        """Test LookupResponse serialisation to dict."""
        response = LookupResponse(
            found=True,
            code="43210",
            code_division="43",
            potential_codes_count=0,
            potential_divisions=[],
            potential_codes=[],
        )

        data = response.model_dump()
        expected = {
            "found": True,
            "code": "43210",
            "code_division": "43",
            "potential_codes_count": 0,
            "potential_divisions": [],
            "potential_codes": [],
        }

        assert data == expected

    def test_lookup_response_deserialization(self):
        """Test LookupResponse deserialisation from dict."""
        data = {
            "found": False,
            "code": None,
            "code_division": None,
            "potential_codes_count": 0,
            "potential_divisions": [],
            "potential_codes": [],
        }

        response = LookupResponse.model_validate(data)

        assert response.found is False
        assert response.code is None
        assert response.code_division is None
        assert response.potential_codes_count == 0

    def test_lookup_response_default_values(self):
        """Test LookupResponse with default None values for code and code_division."""
        response = LookupResponse(
            found=True,
            potential_codes_count=0,
            potential_divisions=[],
            potential_codes=[],
        )

        assert response.found is True
        assert response.code is None
        assert response.code_division is None
        assert response.potential_codes_count == 0

    def test_lookup_response_with_division_only(self):
        """Test LookupResponse with only code_division populated."""
        response = LookupResponse(
            found=False,
            code=None,
            code_division="56",
            potential_codes_count=0,
            potential_divisions=[],
            potential_codes=[],
        )

        assert response.found is False
        assert response.code is None
        assert response.code_division == "56"

    def test_lookup_response_with_code_only(self):
        """Test LookupResponse with only code populated."""
        response = LookupResponse(
            found=True,
            code="56302",
            code_division=None,
            potential_codes_count=0,
            potential_divisions=[],
            potential_codes=[],
        )

        assert response.found is True
        assert response.code == "56302"
        assert response.code_division is None
