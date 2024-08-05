import datetime
import json
import time

import requests


def load_stored_cases():
    with open("cases.json", "r") as f:
        cases = json.load(f)
    return cases


def save_cases(cases):
    # this is a very naive way to save cases - we should probably use a database
    date = datetime.datetime.now().strftime("%Y%m%d")
    with open(f"output/cases-{date}.json", "w") as f:
        json.dump(cases, f)


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

    print(f"Found {len(case_ids)} total cases")

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
