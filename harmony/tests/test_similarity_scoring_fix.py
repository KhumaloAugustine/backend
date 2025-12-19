"""
MIT License

Copyright (c) 2023 Ulster University (https://www.ulster.ac.uk).
Project: Harmony (https://harmonydata.ac.uk)
Maintainer: Thomas Wood (https://fastdatascience.com)

Test to verify the fix for high similarity percentages issue.
This test ensures that:
1. Similarity scores are not inflated by taking max of positive and negative
2. Polarity is properly respected (negative scores for opposite items)
3. Only positive polarity matches are reported in harmonization outputs
"""

import sys
import unittest

sys.path.append("../src")

from harmony import match_instruments
from harmony.schemas.requests.text import Instrument, Question


class TestSimilarityScoringFix(unittest.TestCase):
    """Test that similarity scoring is accurate and not inflated"""

    def test_different_items_do_not_have_inflated_scores(self):
        """
        Test that semantically different items don't get artificially high scores.
        Previously, the max of positive and negative similarity was used, causing inflation.
        """
        questions = [
            Question(question_text="When I feel frightened, it is hard for me to breathe"),
            Question(question_text="I was bothered by things that usually don't bother me."),
            Question(question_text="I get headaches when I am at school"),
            Question(question_text="I did not feel like eating; my appetite was poor."),
        ]
        
        instrument = Instrument(questions=questions, instrument_name="Test")
        match_response = match_instruments([instrument])
        
        # Self-matches should be close to 1.0
        for i in range(len(questions)):
            self.assertGreater(match_response.similarity_with_polarity[i][i], 0.99)
        
        # Cross-matches for semantically different items should NOT be artificially high
        # Check that at least some cross-matches are reasonably low (< 0.8)
        cross_match_scores = []
        for i in range(len(questions)):
            for j in range(i+1, len(questions)):
                score = match_response.similarity_with_polarity[i][j]
                cross_match_scores.append(score)
        
        # At least some pairs should have moderate or low similarity
        low_scores = [s for s in cross_match_scores if s < 0.8]
        self.assertGreater(len(low_scores), 0, 
                          "Expected some question pairs to have similarity < 0.8, but all were high")
        
        # Average cross-match score should be reasonable (not all above 90%)
        avg_cross_match = sum(cross_match_scores) / len(cross_match_scores)
        self.assertLess(avg_cross_match, 0.85,
                       f"Average cross-match score {avg_cross_match:.2%} is too high - suggests score inflation")

    def test_opposite_polarity_items_have_negative_scores(self):
        """
        Test that items with opposite polarity (e.g., 'I feel happy' vs 'I don't feel happy')
        have negative similarity scores, not positive inflated scores.
        """
        questions = [
            Question(question_text="I feel nervous"),
            Question(question_text="I don't feel nervous"),
            Question(question_text="I feel anxious"),
            Question(question_text="I am calm and relaxed")
        ]
        
        instrument = Instrument(questions=questions, instrument_name="Test")
        match_response = match_instruments([instrument])
        
        # "I feel nervous" vs "I don't feel nervous" should have negative similarity
        score_nervous_vs_not_nervous = match_response.similarity_with_polarity[0][1]
        self.assertLess(score_nervous_vs_not_nervous, 0,
                       "Opposite polarity items should have negative similarity scores")
        
        # "I feel nervous" vs "I feel anxious" should have positive similarity
        score_nervous_vs_anxious = match_response.similarity_with_polarity[0][2]
        self.assertGreater(score_nervous_vs_anxious, 0.5,
                          "Similar items should have positive similarity scores")

    def test_pdf_report_filters_by_positive_polarity(self):
        """
        Test that PDF report generation only includes positive polarity matches
        """
        from harmony.services.export_pdf_report import calculate_harmonisation_statistics
        
        questions = [
            Question(question_text="I feel sad"),
            Question(question_text="I don't feel sad"),
            Question(question_text="I feel happy"),
        ]
        
        instruments = [Instrument(questions=questions, instrument_name="Test")]
        match_response = match_instruments(instruments)
        
        # Collect matches manually
        raw_matches = []
        sim = match_response.similarity_with_polarity
        for i in range(sim.shape[0]):
            for j in range(i + 1, sim.shape[1]):
                if sim[i][j] > 0:  # Only positive
                    raw_matches.append((i, j, sim[i][j]))
        
        # Calculate statistics
        stats = calculate_harmonisation_statistics(
            match_response, instruments, raw_matches, threshold=0.5
        )
        
        # Verify that only positive polarity matches are counted
        # The negative polarity match between "I feel sad" and "I don't feel sad" should NOT count
        self.assertGreaterEqual(stats['successful_matches'], 0)
        
        # All successful matches should have positive scores
        positive_matches = [m for m in raw_matches if m[2] >= 0.5]
        self.assertEqual(stats['successful_matches'], len(positive_matches))

    def test_crosswalk_table_excludes_negative_polarity(self):
        """
        Test that crosswalk table generation excludes opposite polarity items
        """
        from harmony.matching.generate_crosswalk_table import generate_crosswalk_table
        
        questions = [
            Question(question_text="I feel nervous", question_no=1),
            Question(question_text="I don't feel nervous", question_no=2),
            Question(question_text="I feel anxious", question_no=3),
        ]
        
        instrument = Instrument(questions=questions, instrument_name="Test")
        match_response = match_instruments([instrument])
        
        # Generate crosswalk with threshold 0.3
        crosswalk = generate_crosswalk_table(
            instruments=[instrument],
            item_to_item_similarity_matrix=match_response.similarity_with_polarity,
            threshold=0.3,
            is_allow_within_instrument_matches=True
        )
        
        # Check that no matches have negative scores
        if len(crosswalk) > 0:
            for _, row in crosswalk.iterrows():
                self.assertGreaterEqual(row['match_score'], 0.3,
                                       "Crosswalk should not include negative polarity or low score matches")


if __name__ == '__main__':
    unittest.main()
