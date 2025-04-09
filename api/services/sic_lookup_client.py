from sic_lookup.sic_lookup import SICLookup

class SICLookupClient:
    def __init__(self, data_path="src/sic_lookup/data/example_sic_data.csv"):
        self.lookup_service = SICLookup(data_path)

    def get_result(self, description, similarity=False):
        """
        Get the SIC lookup result for a given description.
        
        Args:
            description (str): The description to look up.
            similarity (bool): Whether to use similarity search.
        
        Returns:
            dict: The SIC lookup result.
        """
        return self.lookup_service.lookup(description, similarity)