from graph.vector_retriever import (
    search_business_concepts,
    search_metrics
)


questions = [

    "Who are our biggest buyers?",

    "Which performers are most popular?",

    "Break down purchase value by geography",

    "Which listeners generate the most income?"
]


for question in questions:

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"QUESTION: {question}"
    )


    concepts = (
        search_business_concepts(
            question
        )
    )


    print(
        "\nCONCEPT MATCHES"
    )

    for concept in concepts:

        print(
            concept["name"],
            "score=",
            round(
                concept[
                    "similarity_score"
                ],
                4
            )
        )


    metrics = (
        search_metrics(
            question
        )
    )


    print(
        "\nMETRIC MATCHES"
    )

    for metric in metrics:

        print(
            metric["name"],
            "score=",
            round(
                metric[
                    "similarity_score"
                ],
                4
            )
        )