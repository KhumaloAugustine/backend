#!/usr/bin/env python3
"""
Regenerate catalogue data from metadata_sources directory.
This script processes all mh_study_*.json files and generates:
- all_instruments_preprocessed.json
- all_questions_ever_seen.json
- instrument_idx_to_question_idxs.json
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_instruments_from_metadata_sources(metadata_path: str = "metadata_sources") -> tuple:
    """
    Load all instruments from metadata_sources and generate catalogue files.
    
    Returns:
        Tuple of (all_instruments, all_questions, instrument_idx_to_question_idxs)
    """
    
    metadata_dir = Path(metadata_path)
    
    if not metadata_dir.exists():
        logger.error(f"Metadata directory not found: {metadata_dir}")
        return [], [], {}
    
    all_instruments = []
    all_questions = []
    instrument_idx_to_question_idxs = []
    
    # Load all mh_study_*.json files in order
    study_files = sorted(metadata_dir.glob("mh_study_*.json"))
    logger.info(f"Found {len(study_files)} metadata files")
    
    for study_file in study_files:
        try:
            with open(study_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Extract instrument details
            instrument_details = metadata.get("instrument_details", {})
            instrument_name = instrument_details.get("instrument_name", "")
            
            # Only process if instrument_name exists
            if not instrument_name:
                logger.debug(f"Skipping {study_file.stem} - no instrument_name")
                continue
            
            logger.info(f"Processing {study_file.stem}: {instrument_name}")
            
            # Build instrument object for catalogue
            instrument_obj = {
                "id": study_file.stem,
                "instrument_name": instrument_name,
                "full_name": instrument_details.get("full_name", instrument_name),
                "measurement_target": instrument_details.get("measurement_target", ""),
                "num_items": instrument_details.get("num_items", 0),
                "response_scale": instrument_details.get("response_scale", ""),
                "score_range": instrument_details.get("score_range", ""),
                "interpretation": instrument_details.get("interpretation", ""),
                "producers": metadata.get("doc_desc", {}).get("producers", []),
                "keywords": [kw.get("keyword", "") for kw in metadata.get("study_desc", {}).get("study_info", {}).get("keywords", [])],
                "doc_desc": metadata.get("doc_desc", {}),
                "study_desc": metadata.get("study_desc", {}),
                "instrument_details": instrument_details,
            }
            
            # Record the index where this instrument starts in the questions list
            start_question_idx = len(all_questions)
            instrument_idx_to_question_idxs.append({
                "instrument_id": study_file.stem,
                "instrument_name": instrument_name,
                "question_indices": []
            })
            
            # Extract and add questions
            questions = metadata.get("questions", [])
            for q_idx, question in enumerate(questions):
                question_obj = {
                    "id": f"{study_file.stem}_q{q_idx}",
                    "instrument_id": study_file.stem,
                    "instrument_name": instrument_name,
                    "question_no": question.get("question_no", q_idx + 1),
                    "question_text": question.get("question_text", ""),
                    "response_options": question.get("response_options", []),
                    "subscale": question.get("subscale", ""),
                    "domain": question.get("domain", ""),
                }
                
                all_questions.append(question_obj)
                current_question_idx = len(all_questions) - 1
                
                # Track question indices for this instrument
                instrument_idx_to_question_idxs[-1]["question_indices"].append(current_question_idx)
            
            all_instruments.append(instrument_obj)
            
        except Exception as e:
            logger.error(f"Error processing {study_file}: {str(e)}")
            continue
    
    logger.info(f"Loaded {len(all_instruments)} instruments")
    logger.info(f"Loaded {len(all_questions)} total questions")
    
    return all_instruments, all_questions, instrument_idx_to_question_idxs


def save_catalogue_files(all_instruments: List[Dict], 
                        all_questions: List[Dict],
                        instrument_idx_to_question_idxs: List[Dict],
                        output_dir: str = ".") -> None:
    """
    Save generated catalogue files to disk.
    """
    
    output_path = Path(output_dir)
    
    # Save all_instruments_preprocessed.json
    instruments_file = output_path / "all_instruments_preprocessed.json"
    with open(instruments_file, 'w', encoding='utf-8') as f:
        for instrument in all_instruments:
            f.write(json.dumps(instrument, ensure_ascii=False) + '\n')
    logger.info(f"Saved {len(all_instruments)} instruments to {instruments_file}")
    
    # Save all_questions_ever_seen.json
    questions_file = output_path / "all_questions_ever_seen.json"
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(all_questions)} questions to {questions_file}")
    
    # Save instrument_idx_to_question_idxs.json
    idx_file = output_path / "instrument_idx_to_question_idxs.json"
    with open(idx_file, 'w', encoding='utf-8') as f:
        json.dump(instrument_idx_to_question_idxs, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved index mapping to {idx_file}")


def main():
    """Main function to regenerate catalogue data."""
    
    logger.info("Starting catalogue data regeneration...")
    logger.info("=" * 60)
    
    # Load instruments from metadata_sources
    all_instruments, all_questions, instrument_idx_to_question_idxs = \
        load_instruments_from_metadata_sources()
    
    if not all_instruments:
        logger.error("No instruments loaded! Check metadata_sources directory.")
        return False
    
    logger.info("=" * 60)
    
    # Save to current directory (where API runs)
    save_catalogue_files(all_instruments, all_questions, instrument_idx_to_question_idxs)
    
    logger.info("=" * 60)
    logger.info("✓ Catalogue data regeneration complete!")
    logger.info(f"  - {len(all_instruments)} instruments")
    logger.info(f"  - {len(all_questions)} questions")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Restart the API server")
    logger.info("  2. Clear browser cache if using web UI")
    logger.info("  3. Test with discovery endpoints")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
