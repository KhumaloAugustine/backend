# Quick Test Script
# Tests if the similarity scoring fix is working correctly

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing Similarity Scoring Fix" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

# Create test script
$testScript = @"
import sys
sys.path.insert(0, 'harmony/src')

try:
    from harmony.matching.matcher import match_instruments_with_function
    from harmony.matching.default_matcher import get_default_vectorisation_function
    from harmony.schemas.requests.text import Instrument, Question
    
    print('✅ Imports successful')
    
    # Test with the questions from the issue
    questions = [
        Question(question_text='When I feel frightened, it is hard for me to breathe'),
        Question(question_text='I was bothered by things that usually don''t bother me.'),
        Question(question_text='I get headaches when I am at school'),
        Question(question_text='I did not feel like eating; my appetite was poor.'),
    ]
    
    instrument = Instrument(questions=questions, instrument_name='Test')
    vectorisation_function = get_default_vectorisation_function()
    
    print('\nMatching questions...')
    match_result = match_instruments_with_function(
        [instrument],
        query='',
        vectorisation_function=vectorisation_function,
        is_negate=True
    )
    
    sim = match_result.similarity_with_polarity
    
    print('\nSelf-match scores (should be ~1.0):')
    for i in range(len(questions)):
        print(f'  Q{i+1} vs Q{i+1}: {sim[i][i]:.3f}')
    
    print('\nCross-match scores:')
    cross_scores = []
    for i in range(len(questions)):
        for j in range(i+1, len(questions)):
            score = sim[i][j]
            cross_scores.append(score)
            print(f'  Q{i+1} vs Q{j+1}: {score:.3f} ({score*100:.1f}%)')
    
    avg_cross = sum(cross_scores) / len(cross_scores)
    print(f'\nAverage cross-match: {avg_cross:.3f} ({avg_cross*100:.1f}%)')
    
    if avg_cross < 0.85:
        print('\n✅ PASS: Scores are realistic (not inflated)')
    else:
        print('\n❌ FAIL: Scores still appear inflated')
        
except ImportError as e:
    print(f'\n❌ Import Error: {e}')
    print('\nMake sure to run: cd harmony; python -m pip install -e .')
    sys.exit(1)
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@

# Run the test
Write-Host "Running test..." -ForegroundColor Yellow
$testScript | python

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Complete" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Read-Host "Press Enter to exit"
