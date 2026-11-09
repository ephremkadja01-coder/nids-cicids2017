from app.agent.prompts import get_soc_prompt


def test_soc_prompt_requests_a_detailed_french_analysis():
    prompt = " ".join(
        get_soc_prompt("Que signifie ce résultat ?", 0.82, "ATTACK").split()
    )

    assert "5 à 8 phrases" in prompt
    assert "trois parties" in prompt
    assert "mesures de remédiation" in prompt
    assert "n'invente aucun indicateur" in prompt
