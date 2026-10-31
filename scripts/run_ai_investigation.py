import json

from app.ai_investigator import investigate


if __name__ == "__main__":
    result = investigate()

    print("\n========== INCIDENT REPORT ==========\n")

    print(result["report"].model_dump_json(indent=2))

    print("\n========== INVESTIGATION TRACE ==========\n")

    print(
        json.dumps(
            result["tool_trace"],
            indent=4,
        )
    )