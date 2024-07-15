import json
import requests


def main():
    case_ids = []

    # could hard-code these instead of making a request - highly unlikely to change
    states = requests.get("https://www.namus.gov/api/CaseSets/NamUs/States").json()

    with open("output.json", "w") as outfile:
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
            print("Found {count} cases in {state}".format(count=len(ids), state=state["name"]))
            case_ids += ids
            break

        print("Found {} total cases".format(len(case_ids)))

        for i in range(len(case_ids)):
            case_id = case_ids[i]
            print("Getting case id {id} ({index}/{total})".format(id=case_id, index=i, total=len(case_ids)))
            res = requests.get("https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Cases/{id}".format(id=case_id)).json()
            outfile.write(json.dumps(res) + "\n")


if __name__ == '__main__':
    main()
