import pandas as pd
from sic_soc_llm.data_models.sicDB import SicMeta


class SICLookup:
    def __init__(self, data_path="sic_lookup/data/example_sic_data.csv"):
        # Load data and store descriptions in lowercase
        self.data = pd.read_csv(data_path)
        self.data["description"] = self.data["description"].str.lower()

        # Some codes are 4 digits because they come from th 0x class
        # prepend a 0 to make 5 digits
        self.data["label"] = self.data["label"].apply(
            lambda x: f"0{x}" if len(str(x)) == 4 else str(x)
        )

        self.lookup_dict = self.data.set_index("description").to_dict()["label"]
        self.meta = SicMeta(retrofit_keys=True)

    def lookup(self, description, similarity=False):
        description = description.lower()

        matching_code = self.lookup_dict.get(description)
        matching_code_meta = None
        division_meta = None

        # Extract the first 2 digits of the code as code_division
        matching_code_division = None
        if matching_code:
            matching_code_division = matching_code[:2]
            # Lookup the meta data for the code
            matching_code_meta = self.meta.get_meta_by_code(matching_code)
            division_meta = self.meta.get_meta_by_code(matching_code_division)
            print(matching_code_meta)

        if not matching_code:
            matching_code = None

        potential_matches = {}

        if similarity:
            # Check if the description is mentioned elsewhere in the dataset
            matches = self.data[
                self.data["description"].str.contains(description, na=False)
            ]
            potential_codes = matches["label"].unique()

            if len(potential_codes) == 1 and potential_codes[0] == matching_code:
                potential_codes = []  # Set it as an empty list instead of a dictionary
                potential_descriptions = []
                matches = []

            else:
                potential_codes = potential_codes.tolist()
                potential_descriptions = matches["description"].unique().tolist()

            division_codes = list({str(code)[:2] for code in potential_codes})

            # Get meta data associated with each division code
            divisions = [
                {
                    "code": division_code,
                    "meta": self.meta.get_meta_by_code(division_code),
                }
                for division_code in division_codes
            ]

            # Return the potential labels
            potential_matches = {
                "descriptions_count": len(matches),
                "descriptions": potential_descriptions,
                "codes_count": len(potential_codes),
                "codes": potential_codes,
                "divisions_count": len(division_codes),
                "divisions": divisions,
            }

        response = {
            "description": description,
            "code": matching_code,
            "code_meta": matching_code_meta,
            "code_division": matching_code_division,
            "code_division_meta": division_meta,
        }
        if similarity:
            response["potential_matches"] = potential_matches

        return response