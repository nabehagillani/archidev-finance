"""
Optional ML upgrade to keyword-based categorization, using scikit-learn
(TF-IDF + Multinomial Naive Bayes) trained on each company's own
corrected transaction history.

Deliberately gated behind a minimum-data threshold: with too few
labeled examples a text classifier overfits and produces confident-
looking garbage, which is worse than the honest, inspectable keyword
rules. Below the threshold, categorization_service.suggest_category()
falls back to keyword matching automatically — this module is additive,
never a replacement that could regress accuracy on a new company with
no history yet.

Models are cached in memory per company and retrained on demand
(call invalidate() after enough new corrections accumulate) rather than
on every single request, since training is not free.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionCategory

MIN_EXAMPLES_PER_CATEGORY = 5
MIN_CATEGORIES = 2

_model_cache: dict[str, tuple] = {}  # company_id -> (vectorizer, classifier, category_id_by_label)


def _training_data(db: Session, company_id: str):
    rows = (
        db.query(Transaction.description, Transaction.category_id)
        .filter(Transaction.company_id == company_id, Transaction.category_id.isnot(None))
        .all()
    )
    return [(desc, cat_id) for desc, cat_id in rows if desc and cat_id]


def train(db: Session, company_id: str) -> bool:
    """Returns True if a model was successfully trained, False if there
    isn't yet enough labeled history (caller should keep using keyword
    rules in that case)."""
    data = _training_data(db, company_id)
    if not data:
        return False

    by_category: dict[str, list[str]] = {}
    for desc, cat_id in data:
        by_category.setdefault(cat_id, []).append(desc)

    eligible = {cat_id: descs for cat_id, descs in by_category.items() if len(descs) >= MIN_EXAMPLES_PER_CATEGORY}
    if len(eligible) < MIN_CATEGORIES:
        return False

    descriptions, labels = [], []
    for cat_id, descs in eligible.items():
        descriptions.extend(descs)
        labels.extend([cat_id] * len(descs))

    vectorizer = TfidfVectorizer(min_df=1, stop_words="english")
    X = vectorizer.fit_transform(descriptions)
    clf = MultinomialNB()
    clf.fit(X, labels)

    _model_cache[company_id] = (vectorizer, clf)
    return True


def invalidate(company_id: str):
    _model_cache.pop(company_id, None)


def predict(db: Session, company_id: str, description: str, min_confidence: float = 0.6) -> TransactionCategory | None:
    """Returns a predicted category only above min_confidence, so a
    genuinely ambiguous description falls through to keyword rules
    (or no suggestion) rather than guessing."""
    if company_id not in _model_cache:
        if not train(db, company_id):
            return None

    vectorizer, clf = _model_cache[company_id]
    try:
        X = vectorizer.transform([description])
        proba = clf.predict_proba(X)[0]
        best_idx = proba.argmax()
        confidence = proba[best_idx]
        if confidence < min_confidence:
            return None
        predicted_category_id = clf.classes_[best_idx]
    except Exception:
        return None

    return db.query(TransactionCategory).filter(TransactionCategory.id == predicted_category_id).first()
