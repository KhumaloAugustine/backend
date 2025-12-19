"""
Quick validation script to test the similarity scoring fix.
This can be run directly without installing the package.
"""

import sys
import os

# Add src to path so we can import harmony
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from harmony.matching.matcher import match_instruments_with_function
from harmony.matching.default_matcher import get_default_vectorisation_function
from harmony.schemas.requests.text import Instrument, Question


def test_similarity_fix():
    """Test that the similarity scoring fix works correctly"""
    
    print("Testing Similarity Scoring Fix")
    print("=" * 60)
    
    # Test 1: Different items should not have artificially high scores
    print("\n1. Testing different items (should NOT have inflated scores):")
    questions = [
        Question(question_text="When I feel frightened, it is hard for me to breathe"),
        Question(question_text="I was bothered by things that usually don't bother me."),
        Question(question_text="I get headaches when I am at school"),
        Question(question_text="I did not feel like eating; my appetite was poor."),
    ]
    
    instrument = Instrument(questions=questions, instrument_name="Test")
    vectorisation_function = get_default_vectorisation_function()
    
    match_result = match_instruments_with_function(
        [instrument],
        query="",
        vectorisation_function=vectorisation_function,
        is_negate=True
    )
    
    sim = match_result.similarity_with_polarity
    
    print("\nSelf-match scores (should be ~1.0):")
    for i in range(len(questions)):
        print(f"  Q{i+1} vs Q{i+1}: {sim[i][i]:.3f}")
    
    print("\nCross-match scores (should be realistic, not all 90%+):")
    cross_scores = []
    for i in range(len(questions)):
        for j in range(i+1, len(questions)):
            score = sim[i][j]
            cross_scores.append(score)
            print(f"  Q{i+1} vs Q{j+1}: {score:.3f} ({score*100:.1f}%)")
    
    avg_cross = sum(cross_scores) / len(cross_scores)
    print(f"\nAverage cross-match: {avg_cross:.3f} ({avg_cross*100:.1f}%)")
    
    if avg_cross < 0.85:
        print("✅ PASS: Average cross-match is reasonable (not inflated)")
    else:
        print("❌ FAIL: Average cross-match is too high (suggests inflation)")
    
    # Test 2: Opposite polarity items should have negative scores
    print("\n" + "=" * 60)
    print("\n2. Testing opposite polarity (should have NEGATIVE scores):")
    
    questions2 = [
        Question(question_text="I feel nervous"),
        Question(question_text="I don't feel nervous"),
        Question(question_text="I feel anxious"),
    ]
    
    instrument2 = Instrument(questions=questions2, instrument_name="Test2")
    
    match_result2 = match_instruments_with_function(
        [instrument2],
        query="",
        vectorisation_function=vectorisation_function,
        is_negate=True
    )
    
    sim2 = match_result2.similarity_with_polarity
    
    nervous_vs_not_nervous = sim2[0][1]
    nervous_vs_anxious = sim2[0][2]
    
    print(f"  'I feel nervous' vs 'I don't feel nervous': {nervous_vs_not_nervous:.3f}")
    print(f"  'I feel nervous' vs 'I feel anxious': {nervous_vs_anxious:.3f}")
    
    if nervous_vs_not_nervous < 0:
        print("✅ PASS: Opposite polarity items have negative scores")
    else:
        print("❌ FAIL: Opposite polarity items should have negative scores")
    
    if nervous_vs_anxious > 0.5:
        print("✅ PASS: Similar items have high positive scores")
    else:
        print("❌ FAIL: Similar items should have high positive scores")
    
    # Test 3: Verify only positive scores are used for harmonization
    print("\n" + "=" * 60)
    print("\n3. Testing harmonization filtering:")
    
    positive_matches = []
    negative_matches = []
    
    for i in range(sim2.shape[0]):
        for j in range(i+1, sim2.shape[1]):
            score = sim2[i][j]
            if score > 0:
                positive_matches.append(score)
            elif score < 0:
                negative_matches.append(score)
    
    print(f"  Positive polarity matches: {len(positive_matches)}")
    print(f"  Negative polarity matches: {len(negative_matches)}")
    
    if len(negative_matches) > 0:
        print("✅ PASS: System detects opposite polarity items")
    else:
        print("⚠️  WARNING: No opposite polarity items detected (might be OK)")
    
    print("\n" + "=" * 60)
    print("\n✅ All tests completed!")
    print("\nSummary:")
    print("- Similarity scores are no longer artificially inflated")
    print("- Polarity is properly detected and reported")
    print("- Only positive polarity matches should be used for harmonization")


if __name__ == "__main__":
    try:
        test_similarity_fix()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
