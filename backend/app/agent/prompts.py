def get_soc_prompt(user_query: str, probability: float, verdict: str) -> str:
    return f"""
    Tu es un expert SOC (Security Operations Center) en cybersécurité.
    L'utilisateur te demande : "{user_query}"

    Voici les données du flux réseau analysé par notre modèle XGBoost :
    - Probabilité d'attaque : {probability*100:.4f}%
    - Verdict : {verdict}

    Rédige une réponse courte, professionnelle et en français.
    Si c'est BENIGN, rassure l'utilisateur brièvement.
    Si c'est une attaque, explique le risque et donne une recommandation de remédiation.
    """