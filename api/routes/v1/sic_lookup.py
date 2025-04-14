from fastapi import APIRouter, HTTPException

from api.services.sic_lookup_client import SICLookupClient

router = APIRouter(tags=["SIC Lookup"])

# Initialize the SIC Lookup Client
lookup_client = SICLookupClient(
    data_path="../sic-classification-library/src/industrial_classification/data/sic_knowledge_base_utf8.csv"
)


@router.get("/sic-lookup")
async def sic_lookup(description: str, similarity: bool = False):
    """Lookup the SIC code for a given description.

    Args:
        description (str): The description to look up.
        similarity (bool, optional): Whether to use similarity search. Defaults to False.

    Returns:
        dict: The SIC lookup result.

    Example:
        ```json
        {
            "code": "43210",
            "description": "Electrical installation",
            "potential_matches": {
                "descriptions": [
                    "Electrical installation",
                    "Electrical contractor",
                    "Electrician"
                ]
            }
        }
        ```

    Raises:
        HTTPException: If the description parameter is missing or invalid.
    """
    if not description:
        raise HTTPException(status_code=400, detail="Description parameter is required")
    result = lookup_client.get_result(description, similarity)
    return result


@router.get("/test")
async def test():
    """Test endpoint to verify the API is working.

    Returns:
        dict: A message indicating the test endpoint is working.
    """
    return {"message": "Test endpoint is working"}
