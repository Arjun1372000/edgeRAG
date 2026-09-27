from src.retrieval.retriever import retrieve


TEST_QUERIES = {
    "HDF": (
        "The process temperature remains above 310 K. "
        "What should the operator do?"
    ),
    "TWF": (
        "Tool wear has exceeded 200 minutes and torque is "
        "gradually increasing. What action should be taken?"
    ),
    "OSF": (
        "Torque suddenly rises above 60 Nm and rotational "
        "speed drops sharply. What should be done?"
    ),
    "PWF": (
        "Machine power has dropped below 3500 W. "
        "What is the appropriate response?"
    ),
    "RNF": (
        "The machine has an unexplained failure with no clear "
        "indication of heat, power, tool wear, or overstrain. "
        "How should the issue be handled?"
    ),
}


def main():
    print("=" * 70)
    print("EdgeRAG Retrieval Test")
    print("=" * 70)

    for expected_fault, query in TEST_QUERIES.items():
        print("\n" + "-" * 70)
        print(f"Expected: {expected_fault}")
        print(f"Query:    {query}")
        print("-" * 70)

        try:
            results = retrieve(query)

            for rank, (document, score) in enumerate(results, start=1):
                print(f"\nRank {rank}")
                print(f"Score: {score:.4f}")
                print(
                    f"Source: "
                    f"{document.metadata.get('filename', 'unknown')}"
                )
                print(f"Content:\n{document.page_content}")

        except Exception as exc:
            print(f"Retrieval failed: {exc}")


if __name__ == "__main__":
    main()