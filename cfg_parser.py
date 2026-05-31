# CFG (Baglamsiz Dilbilgisi) Parser
# Nobel cumle yapisini dogrulamak icin kullanilir
# NLTK kutuphanesi gerekli: pip install nltk

from nltk import CFG, ChartParser

# Nobel cumlesi icin gramer kurallari
grammar = CFG.fromstring("""
    S -> NP VP
    NP -> DET N | N N | N
    VP -> V NP | VP PP
    PP -> P NP | P N
    DET -> 'the'
    N -> 'Prize' | 'Physics' | 'Chemistry' | 'Einstein' | 'Curie'
    V -> 'won'
    P -> 'in'
""")

parser = ChartParser(grammar)


def cfg_parse(cumle_tokenlari):
    """Cumle tokenlarini CFG ile parse et, agac dondur"""
    agaclar = list(parser.parse(cumle_tokenlari))
    return agaclar


if __name__ == "__main__":
    cumle = ['Einstein', 'won', 'the', 'Prize']
    print("Parse agaci:")
    for tree in cfg_parse(cumle):
        tree.pretty_print()
