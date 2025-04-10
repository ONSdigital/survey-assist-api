from fastapi import APIRouter, HTTPException
from api.services.sic_lookup_client import SICLookupClient

router = APIRouter(tags=["Survey Assist"])

# Initialize the SIC Lookup Client
lookup_client = SICLookupClient(data_path="sic_lookup/data/sic_knowledge_base_utf8.csv")

@router.get("/sic-lookup")
async def sic_lookup(description: str, similarity: bool = False):
    """
    Lookup the SIC code for a given description.
    
    Args:
        description (str): The description to look up.
        similarity (bool, optional): Whether to use similarity search. Defaults to False.
    
    Returns:
        dict: The SIC lookup result.
    """
    if not description:
        raise HTTPException(status_code=400, detail="Description parameter is required")
    result = lookup_client.get_result(description, similarity)
    return result

@router.get("/test")
async def test():
    return {"message": "Test endpoint is working"}