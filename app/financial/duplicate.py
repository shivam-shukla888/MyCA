"""
Transaction Fingerprinting & Overlapping Statement Deduplication.
"""

import hashlib
from typing import List, Dict, Any, Tuple
from decimal import Decimal
from .models import NormalizedTransaction, DuplicateStatus
from .money import to_decimal

def compute_transaction_fingerprint(
    date_iso: str,
    amount: Decimal,
    direction: str,
    cleaned_merchant: str,
    account_id: str,
    reference: str = ""
) -> str:
    """
    Computes a deterministic SHA-256 fingerprint for a transaction.
    Matches identical transactions across overlapping statement periods.
    """
    ref_part = f"|{reference.strip().upper()}" if reference else ""
    normalized_str = (
        f"{date_iso.strip()}|"
        f"{amount:.2f}|"
        f"{direction.strip().upper()}|"
        f"{cleaned_merchant.strip().upper()}|"
        f"{account_id.strip()}"
        f"{ref_part}"
    )
    return hashlib.sha256(normalized_str.encode('utf-8')).hexdigest()

def detect_overlapping_transactions(
    incoming_txs: List[Dict[str, Any]],
    existing_fingerprints: Dict[str, str]  # fingerprint -> existing_tx_id
) -> List[Dict[str, Any]]:
    """
    Evaluates incoming transactions against existing fingerprints.
    Categorizes duplicates using multi-variable evidence without silent deletion:
    - UNIQUE: Distinct transaction or repeated legitimate transaction with different ref/balance.
    - POSSIBLE_DUPLICATE: Ambiguous duplicate sharing date/amount/merchant without distinct ref.
    - DUPLICATE_CONFIRMED: Exact fingerprint match across overlapping statement periods.
    """
    processed = []
    seen_in_batch = {}

    for tx in incoming_txs:
        date_iso = str(tx.get("date_iso") or tx.get("date") or "")
        amount = to_decimal(tx.get("amount", Decimal('0.00')))
        direction = str(tx.get("direction") or tx.get("type") or "DEBIT")
        merchant = str(tx.get("cleaned_merchant") or tx.get("description") or "")
        account_id = str(tx.get("account_id") or "")
        ref = str(tx.get("ref_no") or tx.get("reference") or "")

        base_fp = compute_transaction_fingerprint(date_iso, amount, direction, merchant, account_id)
        strict_fp = compute_transaction_fingerprint(date_iso, amount, direction, merchant, account_id, ref) if ref else base_fp

        fp = tx.get("fingerprint") or strict_fp
        tx["fingerprint"] = fp

        if strict_fp in existing_fingerprints:
            tx["duplicate_status"] = DuplicateStatus.DUPLICATE_CONFIRMED.value
            tx["duplicate_of_id"] = existing_fingerprints[strict_fp]
        elif base_fp in existing_fingerprints:
            if ref:
                # Different ref or explicit ref on existing ambiguous match
                tx["duplicate_status"] = DuplicateStatus.POSSIBLE_DUPLICATE.value
                tx["duplicate_of_id"] = existing_fingerprints[base_fp]
            else:
                tx["duplicate_status"] = DuplicateStatus.DUPLICATE_CONFIRMED.value
                tx["duplicate_of_id"] = existing_fingerprints[base_fp]
        elif base_fp in seen_in_batch:
            prev_tx = seen_in_batch[base_fp]
            prev_ref = str(prev_tx.get("ref_no") or prev_tx.get("reference") or "")
            prev_bal = prev_tx.get("balance")
            curr_bal = tx.get("balance")

            if (ref and prev_ref and ref != prev_ref) or (curr_bal is not None and prev_bal is not None and curr_bal != prev_bal):
                tx["duplicate_status"] = DuplicateStatus.UNIQUE.value
            else:
                tx["duplicate_status"] = DuplicateStatus.POSSIBLE_DUPLICATE.value
                tx["duplicate_of_id"] = prev_tx.get("id")
        else:
            tx["duplicate_status"] = DuplicateStatus.UNIQUE.value
            seen_in_batch[base_fp] = tx

        processed.append(tx)

    return processed
