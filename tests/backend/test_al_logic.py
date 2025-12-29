from backend.varga_charts import calculate_arudha_lagna

def test_al_logic():
    print("Testing Arudha Lagna Exceptions...\n")
    
    # Case 1: Standard (no exception)
    # Lagna: Aries(0), Lord (Mars) in Taurus(1) (2nd house)
    # dist = 1. Potential = 1 + 1 = 2 (Gemini). Correct.
    chart1 = {
        'ascendant': {'sign_num': 0, 'degree': 10},
        'mars': {'sign_num': 1, 'degree': 5}
    }
    al1 = calculate_arudha_lagna(chart1)
    print(f"Case 1 (Standard): Lagna Aries, Lord Taurus -> AL: {al1['ascendant']['sign']} (Expected: Gemini)")
    
    # Case 2: Exception 1 (Falls in 1st)
    # Lagna: Aries(0), Lord (Mars) in Aries(0) (1st house)
    # dist = 0. Potential = 0 + 0 = 0 (Aries). 
    # Exception: 10th from Aries = Capricorn(9).
    chart2 = {
        'ascendant': {'sign_num': 0, 'degree': 10},
        'mars': {'sign_num': 0, 'degree': 5}
    }
    al2 = calculate_arudha_lagna(chart2)
    print(f"Case 2 (Exception 1): Lagna Aries, Lord Aries -> AL: {al2['ascendant']['sign']} (Expected: Capricorn)")

    # Case 3: Exception 2 (Falls in 7th)
    # Lagna: Aries(0), Lord (Mars) in Cancer(3) (4th house)
    # dist = 3. Potential = 3 + 3 = 6 (Libra, 7th).
    # Exception: 4th from Libra = Capricorn(9).
    chart3 = {
        'ascendant': {'sign_num': 0, 'degree': 10},
        'mars': {'sign_num': 3, 'degree': 5}
    }
    al3 = calculate_arudha_lagna(chart3)
    print(f"Case 3 (Exception 2): Lagna Aries, Lord Cancer -> AL: {al3['ascendant']['sign']} (Expected: Capricorn)")

    # Case 4: Lord in 7th
    # Lagna: Aries(0), Lord (Mars) in Libra(6) (7th house)
    # dist = 6. Potential = 6 + 6 = 12 -> 0 (Aries, 1st).
    # Exception: 10th from Aries = Capricorn(9).
    chart4 = {
        'ascendant': {'sign_num': 0, 'degree': 10},
        'mars': {'sign_num': 6, 'degree': 5}
    }
    al4 = calculate_arudha_lagna(chart4)
    print(f"Case 4 (Lord in 7th): Lagna Aries, Lord Libra -> AL: {al4['ascendant']['sign']} (Expected: Capricorn)")

if __name__ == "__main__":
    test_al_logic()
