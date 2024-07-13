import os, json, requests

CASE_ENDPOINT = "https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Cases/{case}"
DATA_OUTPUT = "./output/{type}/{type}.json"


def main():
    cases = []
    completed_cases = 0

    # could hard-code these instead of making a request - highly unlikely to change
    states = requests.get("https://www.namus.gov/api/CaseSets/NamUs/States").json()

    for state in states:
        res = requests.post(
            "https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "take": 10000,
                    "projections": ["namus2Number"],
                    "predicates": [
                        {
                            "field": "stateOfLastContact",
                            "operator": "IsIn",
                            "values": [state["name"]],
                        }
                    ],
                }
            ),
        ).json()

        ids = [case["namus2Number"] for case in res["results"]]
        print("Found {} cases in {}".format(len(ids), state["name"]))
        cases += ids

    print("Found {} total cases".format(len(cases)))


if __name__ == '__main__':
    main()
