import datetime
import json
import time

import requests

# currently unused except for manual reformatting of previous output
# may be useful in situations where we only want to query records we don't already have a copy of
def load_stored_cases():
    with open("output/namus-20240811.json", "r") as f:
        cases = json.load(f)
    return cases


def save_cases(cases):
    # this is a very naive way to save cases - we should probably use a database
    date = datetime.datetime.now().strftime("%Y%m%d")

    # sort by case ID first
    cases.sort(key=lambda x: x["id"])

    with open(f"output/namus-{date}.json2", "w") as f:
        # handling this manually to keep a one-case-per-line format for easy diffing while still maintaining a valid
        # JSON object (versus jsonlines which would add another dependency for using the data)

        # open the JSON array
        f.write("[\n")

        for case in cases:
            # add a tab before each line to make it pretty
            f.write("\t")
            json.dump(case, f)
            # skip the final comma on the last entry to maintain a valid JSON object
            if case == cases[-1]:
                f.write("\n")
            else:
                f.write(",\n")
        # close the JSON array
        f.write("]\n")


def get_states():
    # could hard-code these instead of making a request - highly unlikely to change
    # don't bother catching exceptions here - if this fails we have bigger issues
    states = [state["name"] for state in requests.get("https://www.namus.gov/api/CaseSets/NamUs/States").json()]
    return states


def get_cases_by_state(state):
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
                        "values": [state],
                    }
                ],
            }
        ),
    ).json()

    case_ids = [case["namus2Number"] for case in res["results"]]
    return case_ids


def get_case_by_id(case_id):
    case = requests.get(f"https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Cases/{case_id}").json()
    return case


def main():
    failures = 0
    cases = []
    case_ids = []

    states = get_states()

    for state in states:
        ids = get_cases_by_state(state)
        print(f"Found {len(ids)} cases in {state}")
        case_ids.extend(ids)

    print(f"Found {len(case_ids)} total ")

    for i in range(len(case_ids)):
        while True:
            case_id = case_ids[i]
            print(f"Getting case ID {case_id} ({i+1}/{len(case_ids)} - {100*(i+1)/len(case_ids):.2f}%)")
            try:
                case = get_case_by_id(case_id)
                cases.append(case)
                failures = 0
                break
            except Exception as e:
                print(f"Failed to get case ID {case_id}: {e}")

                # very dumb exponential backoff
                failures += 1
                if failures == 13: # 2^12 = 4096 seconds = ~68 minutes
                    print("Too many failures, exiting")
                    return
                delay_s = pow(2, failures)
                print(f"Failures: {failures}, sleeping for {delay_s} seconds")
                time.sleep(delay_s)

    save_cases(cases)


if __name__ == '__main__':
    main()
