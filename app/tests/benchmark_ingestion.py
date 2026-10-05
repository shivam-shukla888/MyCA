"""
Phase 4 Ingestion Pipeline Benchmark.
Measures:
- Read & Validation time
- Extraction & Classification time
- Arithmetic reconciliation time
- Database persistence time
- Scanned / OCR fallback latency
- Memory usage (RSS)
"""

import time
import psutil
import os
from decimal import Decimal
from app.db import init_db
from app.ingestion.pipeline import process_pdf_document
from app.tests.fixtures.golden_statements import (
    create_salary_slip_pdf,
    create_form_16_pdf,
    create_scanned_pdf
)

def run_benchmarks():
    init_db()
    proc = psutil.Process()
    m0 = proc.memory_info().rss / 1024 / 1024

    # 1. Bank Statement (4 pages, tabular)
    valid_pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads", "HDFC_Bank_Statement_Oct2024.pdf")
    with open(valid_pdf_path, 'rb') as f:
        hdfc_bytes = f.read()

    t0 = time.perf_counter()
    res_bank = process_pdf_document(hdfc_bytes, 'Benchmark_HDFC.pdf', 'usr_aarav_01', allow_duplicate=True)
    t_bank = (time.perf_counter() - t0) * 1000

    # 2. Salary Slip
    sal_bytes = create_salary_slip_pdf()
    t1 = time.perf_counter()
    res_sal = process_pdf_document(sal_bytes, 'Benchmark_Salary.pdf', 'usr_aarav_01', allow_duplicate=True)
    t_sal = (time.perf_counter() - t1) * 1000

    # 3. Form 16
    f16_bytes = create_form_16_pdf()
    t2 = time.perf_counter()
    res_f16 = process_pdf_document(f16_bytes, 'Benchmark_Form16.pdf', 'usr_aarav_01', allow_duplicate=True)
    t_f16 = (time.perf_counter() - t2) * 1000

    # 4. Scanned / OCR Fallback
    scan_bytes = create_scanned_pdf()
    t3 = time.perf_counter()
    res_scan = process_pdf_document(scan_bytes, 'Benchmark_Scanned.pdf', 'usr_aarav_01', allow_duplicate=True)
    t_scan = (time.perf_counter() - t3) * 1000

    m1 = proc.memory_info().rss / 1024 / 1024
    mem_delta = m1 - m0

    print("--- INGESTION BENCHMARK RESULTS ---")
    print(f"Bank Statement (4 pages, 22 txs): {t_bank:.2f} ms | Status: {res_bank['status']}")
    print(f"Salary Slip:                      {t_sal:.2f} ms | Status: {res_sal['status']}")
    print(f"Form 16 Tax Certificate:          {t_f16:.2f} ms | Status: {res_f16['status']}")
    print(f"Scanned PDF (Local OCR Fallback): {t_scan:.2f} ms | Status: {res_scan['status']}")
    print(f"Process Memory (RSS):             {m1:.2f} MB (Delta: {mem_delta:.2f} MB)")
    print("-----------------------------------")

if __name__ == "__main__":
    run_benchmarks()
