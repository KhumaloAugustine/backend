# Advanced: Customizing Harmony for South African Languages

This guide covers advanced customization options for building production-grade South African language support.

## 1. Custom Language Detection & Routing

Create `harmony_api/services/language_detector.py`:

```python
from langdetect import detect
from typing import Dict, List

SA_LANGUAGES = {
    'zu': 'Zulu',
    'xh': 'Xhosa', 
    'st': 'Sotho',
    'af': 'Afrikaans',
    'en': 'English'
}

def detect_language(text: str) -> str:
    """Detect language code of input text"""
    try:
        lang = detect(text)
        return lang
    except:
        return 'en'  # Default to English

def get_language_name(code: str) -> str:
    """Get human-readable language name"""
    return SA_LANGUAGES.get(code, 'Unknown')

def is_south_african_language(code: str) -> bool:
    """Check if language is SA-supported"""
    return code in SA_LANGUAGES
```

## 2. Language-Specific Similarity Thresholds

```python
# harmony_api/services/language_matching.py

LANGUAGE_PAIR_THRESHOLDS = {
    ('en', 'zu'): 0.60,  # English-Zulu: 60% threshold
    ('en', 'xh'): 0.62,  # English-Xhosa: 62% threshold  
    ('en', 'af'): 0.55,  # English-Afrikaans: 55% (more similar)
    ('zu', 'xh'): 0.70,  # Zulu-Xhosa: 70% (both Bantu languages)
    ('st', 'zu'): 0.68,  # Sotho-Zulu: 68% (related Bantu)
}

def get_threshold_for_language_pair(lang1: str, lang2: str) -> float:
    """Get optimal similarity threshold for language pair"""
    key = tuple(sorted([lang1, lang2]))
    return LANGUAGE_PAIR_THRESHOLDS.get(key, 0.60)  # Default 60%
```

## 3. Fine-tuning LaBSE on SA Mental Health Data

```python
# scripts/finetune_labse_sa.py

import torch
from sentence_transformers import SentenceTransformer, models, losses
from sentence_transformers.evaluation import TripletEvaluator

def finetune_labse_sa_mental_health():
    """Fine-tune LaBSE on SA mental health questionnaires"""
    
    # Load pre-trained LaBSE
    model = SentenceTransformer('sentence-transformers/LaBSE')
    
    # Your aligned mental health data
    train_data = [
        # (english_text, zulu_text, 1.0)  # positive pair
        ("Feeling nervous", "Ukuzwa ngokukhala", 1.0),
        ("Worrying too much", "Ukunethezeka kakhulu", 1.0),
        # (english_text, random_text, 0.0)  # negative pair
        ("Feeling nervous", "Uxolo ngaphakathi", 0.0),
    ]
    
    # Fine-tune
    train_loss = losses.TripletLoss(model)
    model.fit(
        train_objectives=[(train_loss, 1.0)],
        epochs=3,
        warmup_steps=100,
        output_path="./models/labse-sa-mental-health-v1"
    )
    
    return model

# Usage:
# model = finetune_labse_sa_mental_health()
# embeddings = model.encode(texts)
```

## 4. Custom Similarity Metrics

```python
# harmony_api/services/multilingual_similarity.py

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def cross_lingual_similarity(
    embeddings1: np.ndarray,
    embeddings2: np.ndarray,
    language_pair: tuple = None,
    method: str = 'cosine'
) -> np.ndarray:
    """
    Calculate cross-lingual similarity with optional language-pair weighting
    
    Parameters:
    -----------
    embeddings1: Embeddings from first language
    embeddings2: Embeddings from second language
    language_pair: Tuple of (lang1_code, lang2_code)
    method: 'cosine', 'euclidean', or 'weighted'
    
    Returns:
    --------
    Similarity matrix of shape (n_sentences1, n_sentences2)
    """
    
    if method == 'cosine':
        return cosine_similarity(embeddings1, embeddings2)
    
    elif method == 'weighted':
        # Apply language-pair specific weighting
        base_sim = cosine_similarity(embeddings1, embeddings2)
        
        if language_pair:
            weight = get_cross_lingual_weight(language_pair)
            return base_sim * weight
        
        return base_sim
    
    elif method == 'euclidean':
        from scipy.spatial.distance import cdist
        distances = cdist(embeddings1, embeddings2, metric='euclidean')
        return 1 / (1 + distances)
    
    return cosine_similarity(embeddings1, embeddings2)

def get_cross_lingual_weight(lang_pair: tuple) -> float:
    """Get cross-lingual weight for language pair"""
    weights = {
        ('en', 'af'): 1.15,  # English-Afrikaans: closely related
        ('zu', 'xh'): 1.10,  # Zulu-Xhosa: both Bantu
        ('st', 'zu'): 1.08,  # Sotho-Zulu: related Bantu
    }
    key = tuple(sorted(lang_pair))
    return weights.get(key, 1.0)
```

## 5. Domain-Specific Terminology Dictionaries

```python
# harmony_api/services/sa_health_terminology.py

SA_MENTAL_HEALTH_TERMS = {
    # Mental health terms across SA languages
    'depression': {
        'en': ['depression', 'sadness', 'low mood'],
        'zu': ['ukufa umuntu', 'inhlupentle', 'isikhalo'],
        'xh': ['indlala yomoya', 'inxunguphalo', 'ukuswela ithemba'],
        'af': ['depressie', 'droefheid', 'lae gemoed'],
        'st': ['poelano', 'bohloko', 'lehlonepino']
    },
    'anxiety': {
        'en': ['anxiety', 'nervousness', 'worry'],
        'zu': ['ukuzethu', 'isikhalo samakanda', 'inethezeka'],
        'xh': ['intsizwa', 'isikhalo, 'ingxaki'],
        'af': ['angs', 'senuweeagtigheid', 'bekommernis'],
        'st': ['poifo', 'tshaba', 'lelapa']
    },
    # Add more terms...
}

def get_sa_terminology_synonyms(term: str, language: str) -> List[str]:
    """Get synonyms for health term in specific SA language"""
    for concept, translations in SA_MENTAL_HEALTH_TERMS.items():
        if language in translations and term in translations[language]:
            return translations[language]
    return [term]

def enrich_embeddings_with_terminology(
    texts: List[str],
    language: str,
    model
) -> np.ndarray:
    """Enrich embeddings using SA health terminology"""
    enriched_texts = []
    
    for text in texts:
        enriched = text
        for concept, translations in SA_MENTAL_HEALTH_TERMS.items():
            if language in translations:
                for term in translations[language]:
                    if term.lower() in text.lower():
                        # Add concept keywords
                        enriched += f" {concept}"
        
        enriched_texts.append(enriched)
    
    return model.encode(enriched_texts)
```

## 6. Multilingual Clustering

```python
# harmony_api/services/multilingual_clustering.py

from sklearn.cluster import AgglomerativeClustering
import numpy as np

def multilingual_hierarchical_cluster(
    embeddings: np.ndarray,
    texts: List[str],
    languages: List[str],
    n_clusters: int = None
) -> Dict:
    """
    Hierarchical clustering for multilingual text
    
    Preserves language information in clusters
    """
    
    clusterer = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage='ward'
    )
    
    labels = clusterer.fit_predict(embeddings)
    
    clusters = {}
    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        
        clusters[label].append({
            'text': texts[idx],
            'language': languages[idx],
            'embedding_idx': idx
        })
    
    return clusters

def cluster_by_language_and_semantics(
    instruments: List[Instrument],
    vectorisation_function
) -> Dict:
    """Cluster while keeping language information"""
    
    all_texts = []
    all_languages = []
    text_to_instrument = {}
    
    for inst in instruments:
        lang = detect_language(inst.questions[0].question_text)
        for q in inst.questions:
            all_texts.append(q.question_text)
            all_languages.append(lang)
            text_to_instrument[len(all_texts)-1] = inst.file_name
    
    embeddings = vectorisation_function(all_texts)
    clusters = multilingual_hierarchical_cluster(
        embeddings,
        all_texts,
        all_languages
    )
    
    return clusters
```

## 7. API Integration

Add to `harmony_api/routers/text_router.py`:

```python
@router.post("/match/multilingual/")
def match_instruments_multilingual(
    request: MatchInstrumentsBody
):
    """
    Enhanced endpoint with language-aware matching
    """
    
    # Detect languages
    languages = {}
    for inst in request.body.instruments:
        if inst.questions:
            text = inst.questions[0].question_text
            languages[inst.file_id] = detect_language(text)
    
    # Use LaBSE for embedding
    vectorisation_function = get_labse_embeddings
    
    # Get language-pair thresholds
    thresholds = {}
    for i, inst1 in enumerate(request.body.instruments):
        for j, inst2 in enumerate(request.body.instruments[i+1:]):
            lang_pair = (languages[inst1.file_id], languages[inst2.file_id])
            thresholds[f"{inst1.file_id}_{inst2.file_id}"] = \
                get_threshold_for_language_pair(*lang_pair)
    
    # Perform matching with custom thresholds
    result = match_instruments_with_function(
        instruments=request.body.instruments,
        vectorisation_function=vectorisation_function
    )
    
    # Add language information
    result.languages = languages
    result.similarity_thresholds = thresholds
    
    return result
```

## 8. Evaluation & Metrics

```python
# scripts/evaluate_sa_matching.py

from sklearn.metrics import precision_recall_fscore_support
import numpy as np

def evaluate_multilingual_matching(
    gold_standard_pairs: List[tuple],
    predicted_pairs: List[tuple],
    languages: List[str]
) -> Dict:
    """
    Evaluate multilingual matching performance
    
    gold_standard_pairs: List of (text1, text2, is_match) tuples
    predicted_pairs: List of (text1, text2, similarity) tuples
    """
    
    # Group by language pair
    results_by_lang = {}
    
    for lang in set(languages):
        lang_gold = [p for p in gold_standard_pairs if p[2] == lang]
        
        y_true = [p[3] for p in lang_gold]
        y_pred = [1 if p[2] > 0.5 else 0 for p in predicted_pairs]
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average='binary'
        )
        
        results_by_lang[lang] = {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    return results_by_lang
```

## 9. Deployment Configuration

```yaml
# config/labse_production.yaml

model:
  name: sentence-transformers/LaBSE
  cache_dir: /models/labse
  device: cuda  # or cpu
  fp16: true  # Use half-precision for speed
  batch_size: 64
  max_length: 512

languages:
  primary:
    - zu  # Zulu
    - xh  # Xhosa
    - af  # Afrikaans
  secondary:
    - st  # Sotho
    - en  # English

matching:
  algorithm: hierarchical
  similarity_metric: cosine
  default_threshold: 0.60
  language_pair_thresholds:
    zu-xh: 0.65
    en-af: 0.55
    en-zu: 0.60

performance:
  enable_caching: true
  cache_size_gb: 5
  max_inference_batch: 128
  timeout_seconds: 30
```

## 10. Monitoring & Logging

```python
# harmony_api/services/labse_monitor.py

import logging
from datetime import datetime
from typing import Dict

class LaBSEMonitor:
    def __init__(self):
        self.metrics = {
            'total_embeddings': 0,
            'total_matches': 0,
            'language_distribution': {},
            'average_similarity': []
        }
    
    def log_embedding_batch(self, texts: List[str], languages: List[str]):
        """Log embedding batch statistics"""
        self.metrics['total_embeddings'] += len(texts)
        
        for lang in languages:
            self.metrics['language_distribution'][lang] = \
                self.metrics['language_distribution'].get(lang, 0) + 1
    
    def log_match(self, lang1: str, lang2: str, similarity: float):
        """Log match statistics"""
        self.metrics['total_matches'] += 1
        self.metrics['average_similarity'].append(similarity)
    
    def get_report(self) -> Dict:
        """Get monitoring report"""
        avg_sim = np.mean(self.metrics['average_similarity']) if \
            self.metrics['average_similarity'] else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_embeddings': self.metrics['total_embeddings'],
            'total_matches': self.metrics['total_matches'],
            'average_similarity': float(avg_sim),
            'language_distribution': self.metrics['language_distribution']
        }

# Usage
monitor = LaBSEMonitor()
# ... log as you process
print(monitor.get_report())
```

---

## Implementation Checklist

- [ ] Implement language detection (`language_detector.py`)
- [ ] Set up language-specific thresholds
- [ ] Create terminology dictionaries
- [ ] Fine-tune LaBSE on SA data
- [ ] Add multilingual clustering
- [ ] Integrate into API endpoints
- [ ] Set up monitoring and logging
- [ ] Create evaluation metrics
- [ ] Test with real SA questionnaires
- [ ] Deploy with production config

## Performance Targets

- **Multilingual Matching Accuracy**: >85% for SA language pairs
- **Inference Speed**: <100ms per 100 texts on GPU
- **Cross-lingual F1 Score**: >0.80 for related language pairs
- **Memory Usage**: <2GB for model + cache

---

For detailed implementation help, see the main documentation files.
