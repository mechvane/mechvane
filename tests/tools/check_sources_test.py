#!/usr/bin/env python3
"""Offline unit tests for check_sources.py components.

Tests markdown parsing, link extraction, quotation fuzzy matching,
number normalization (German comma vs dot), and HTML-to-text conversion
without requiring network access.

Usage:
  python3 tests/tools/check_sources_test.py
"""

import sys
from pathlib import Path

# Add repo root to sys.path so tools can be imported
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.check_sources import (
    clean_latex,
    extract_markdown_links,
    find_urls_in_text,
    find_quotes_in_text,
    find_numbers_in_text,
    parse_markdown_entries,
    check_quote_in_text,
    check_number_in_text,
    html_to_text,
    normalize_text_for_matching
)


def test_markdown_link_extraction():
    # Regular markdown link
    text1 = "[Bossard PDF](https://assets.example.com/doc.pdf)"
    links1, _ = extract_markdown_links(text1)
    assert links1 == [("Bossard PDF", "https://assets.example.com/doc.pdf")], f"Failed: {links1}"

    # Nested parentheses inside URL (e.g., ECSS revision or smw download)
    text2 = "[ECSS Handbook](https://ecss.nl/doc-Rev.1(6February2023).pdf)"
    links2, _ = extract_markdown_links(text2)
    assert links2 == [("ECSS Handbook", "https://ecss.nl/doc-Rev.1(6February2023).pdf")], f"Failed: {links2}"

    # Multiple links and bare URLs
    text3 = """
    * Link 1: [Aramfix](https://www.aramfix.com/ds.pdf)
    * Bare: https://www.example.org/bare-link.html
    * Incomplete: https://www.broken.com/...
    """
    urls = find_urls_in_text(text3)
    assert "https://www.aramfix.com/ds.pdf" in urls
    assert "https://www.example.org/bare-link.html" in urls
    assert not any("..." in u for u in urls), f"Incomplete url not filtered: {urls}"


def test_quote_extraction():
    sample = '''
    ### 1. Quelle: Test
    * **Wörtliches Zitat:**
      > *„Sollen Schrauben in geschnittene Innengewinde eingeschraubt werden und wird volle Tragfähigkeit erwartet...“*
    * **Englisch:**
      > *"The lockwasher serves as a spring while the bolt is being tightened."*
    * `Thread d: M2,5 | dk max.: 4,50 | k max.: 2,50 | s nominal: 2`
    '''
    quotes = find_quotes_in_text(sample)
    assert any("geschnittene Innengewinde" in q for q in quotes), f"German quote missing: {quotes}"
    assert any("lockwasher serves as a spring" in q for q in quotes), f"English quote missing: {quotes}"
    assert any("Thread d: M2,5" in q for q in quotes), f"Table code quote missing: {quotes}"


def test_number_extraction():
    sample = r"""
    * Mindesteinschraubtiefe: $2{,}0 \cdot d$
    * Festigkeit: $R_m = 150\,\text{N/mm}^2$
    * Versatz: M6 ($P=1{,}0$): $21{,}3\,\text{mm}$
    * Toleranz: $\pm 0{,}3\text{ mm}$
    """
    numbers = find_numbers_in_text(sample)
    num_vals = [n["number"] for n in numbers]
    assert "2,0" in num_vals, f"2,0 missing: {num_vals}"
    assert "150" in num_vals, f"150 missing: {num_vals}"
    assert "1,0" in num_vals, f"1,0 missing: {num_vals}"
    assert "21,3" in num_vals, f"21,3 missing: {num_vals}"
    assert "0,3" in num_vals, f"0,3 missing: {num_vals}"


def test_number_normalization_and_matching():
    doc_text = """
    Technische Daten: M6 Schraube mit Steigung 1.0 mm, Laenge 21.3 mm,
    Vorspannung 150 N/mm2. Fuer M8 gilt 27,9 mm. Kantenabstand ist 1215 mm.
    """
    # German comma in query matching English dot in document
    assert check_number_in_text("21,3", doc_text) is True
    # German comma in query matching German comma in document
    assert check_number_in_text("27,9", doc_text) is True
    assert check_number_in_text("27.9", doc_text) is True
    # Integer check
    assert check_number_in_text("150", doc_text) is True
    # Value not present in doc
    assert check_number_in_text("23,2", doc_text) is False
    # Substring avoidance (e.g., '21' should not match inside '1215')
    assert check_number_in_text("12", doc_text) is False
    assert check_number_in_text("1215", doc_text) is True


def test_quote_verification():
    doc_text = """
    Auslegungshinweise: Sollen Schrauben in geschnittene Innengewinde eingeschraubt werden
    und wird volle Tragfaehigkeit erwartet, sind minimale Eindrehtiefen festzulegen.
    Bei Eindrehtiefen ueber 1,5 d koennen extreme Toleranzlagen zum Klemmen fuehren.
    """

    # 1. Exact / near-exact match
    q1 = "Sollen Schrauben in geschnittene Innengewinde eingeschraubt werden und wird volle Tragfähigkeit erwartet"
    status1, ratio1 = check_quote_in_text(q1, doc_text)
    assert status1 == "ja", f"Expected 'ja', got '{status1}' with ratio {ratio1}"
    assert ratio1 >= 0.85

    # 2. Quotation with typographic variations (curly quotes, dashes)
    q2 = "„Sollen Schrauben in geschnittene Innengewinde eingeschraubt werden und wird volle Tragfaehigkeit erwartet...“"
    status2, ratio2 = check_quote_in_text(q2, doc_text)
    assert status2 == "ja", f"Expected 'ja', got '{status2}' with ratio {ratio2}"

    # 3. Ellipsis splitting
    q3 = "Sollen Schrauben in geschnittene Innengewinde eingeschraubt werden [...] extreme Toleranzlagen zum Klemmen fuehren."
    status3, ratio3 = check_quote_in_text(q3, doc_text)
    assert status3 == "ja", f"Expected 'ja', got '{status3}' with ratio {ratio3}"

    # 4. Partial match
    q4 = "Sollen Schrauben in geschnittene Innengewinde eingeschraubt werden [...] aber dieser zweite Teil ist voellig frei erfunden."
    status4, ratio4 = check_quote_in_text(q4, doc_text)
    assert status4 == "teilweise", f"Expected 'teilweise', got '{status4}' with ratio {ratio4}"

    # 5. Non-matching quote
    q5 = "Diese Norm legt ausschliesslich Abmessungen fuer Zylinderstifte fest."
    status5, ratio5 = check_quote_in_text(q5, doc_text)
    assert status5 == "nein", f"Expected 'nein', got '{status5}' with ratio {ratio5}"


def test_html_to_text():
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Ignored</title>
        <style>.hidden { display: none; }</style>
        <script>console.log("secret code");</script>
      </head>
      <body>
        <h1>Produktdatenblatt</h1>
        <p>Mindesteinschraubtiefe betr&auml;gt <b>2,5 &times; d</b>.</p>
        <table>
          <tr><th>Gewinde</th><th>Ma&szlig;</th></tr>
          <tr><td>M6</td><td>21,3 mm</td></tr>
        </table>
      </body>
    </html>
    """
    text = html_to_text(sample_html)
    assert "secret code" not in text
    assert "Produktdatenblatt" in text
    assert "beträgt 2,5 × d" in text or "2,5" in text
    assert "M6" in text
    assert "21,3 mm" in text


def test_url_with_balanced_parentheses():
    text = "[Passung](https://de.wikipedia.org/wiki/Passung_(Technik))"
    links, _ = extract_markdown_links(text)
    assert links == [("Passung", "https://de.wikipedia.org/wiki/Passung_(Technik)")], f"Failed: {links}"


def test_german_decimal_comma():
    text = "2,5 mm and 0,05 mm"
    numbers = find_numbers_in_text(text)
    num_vals = [n["number"] for n in numbers]
    assert "2,5" in num_vals, f"2,5 missing: {num_vals}"
    assert "0,05" in num_vals, f"0,05 missing: {num_vals}"


def test_number_range():
    text = "12 … 15 mm"
    numbers = find_numbers_in_text(text)
    num_vals = [n["number"] for n in numbers]
    assert "12" in num_vals, f"12 missing: {num_vals}"
    assert "15" in num_vals, f"15 missing: {num_vals}"


def main():
    print("Running check_sources unit tests...")
    test_markdown_link_extraction()
    print("  ✓ Markdown link extraction")
    test_quote_extraction()
    print("  ✓ Quote extraction")
    test_number_extraction()
    print("  ✓ Number extraction")
    test_number_normalization_and_matching()
    print("  ✓ Number normalization & matching")
    test_quote_verification()
    print("  ✓ Quote fuzzy verification")
    test_html_to_text()
    print("  ✓ HTML to text conversion")
    test_url_with_balanced_parentheses()
    print("  ✓ URL with balanced parentheses")
    test_german_decimal_comma()
    print("  ✓ German decimal comma")
    test_number_range()
    print("  ✓ Number range")
    print("All unit tests passed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
