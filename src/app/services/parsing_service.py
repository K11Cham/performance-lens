# parsing_service.py - File parsing and subject extraction logic

import csv
import io
import re
from typing import List, Dict, Tuple, Any


class ParsingService:
    """Service for parsing uploaded files and extracting subject/score data."""
    
    @staticmethod
    def find_score(cells: List[str]) -> float:
        """Return the first numeric value between 0–100 found in a list of cell strings."""
        for cell in cells:
            try:
                val = float(str(cell).strip())
                if 0 <= val <= 100:
                    return val
            except (ValueError, TypeError):
                continue
        return None

    @staticmethod
    def is_metadata(cell: str) -> bool:
        """Check if cell contains metadata that should be ignored."""
        metadata_patterns = re.compile(
            r'(?i)^(gpa|cgpa|times\s|number\s+of|overall|termly|cumulative|remark|'
            r'result|grade|position|shift|class\b|year\b|student|subject|mark|'
            r'pass|fail|credit|absent|late|detention|suspension|signature)',
        )
        return bool(metadata_patterns.match(cell))

    @staticmethod
    def extract_from_text_lines(raw_text: str) -> List[Dict[str, Any]]:
        """
        Enhanced regex-based extraction for better subject distinction.
        Handles various report card formats while properly distinguishing between
        similar subjects like "Mathematics" vs "Further Mathematics".
        """
        results = []
        seen = set()

        # Pattern 1: numbered row with detailed subject names
        # "1  FURTHER MATHEMATICS  83  A" or "1  MATHEMATICS  78  B"
        numbered = re.compile(
            r'^\d{1,2}[\s.]+([A-Z][A-Z\s&/()\.\-]{3,}?)\s{2,}(\d{1,3})\s+[A-F]',
            re.MULTILINE
        )
        for m in numbered.finditer(raw_text):
            subject = m.group(1).strip()
            score = float(m.group(2))
            if 0 <= score <= 100 and subject not in seen:
                seen.add(subject)
                results.append({'subject': subject.title(), 'score': score})

        # Pattern 2: Enhanced subject detection with better matching
        # Handles "Further Mathematics", "Business Studies", "Technical Drawing", etc.
        if not results:
            enhanced = re.compile(
                r'^([A-Z][A-Z\s&/()\.\-]{3,}?)\s{2,}(\d{1,3})(?:\s+[A-F]|\s|$)',
                re.MULTILINE
            )
            for m in enhanced.finditer(raw_text):
                subject = m.group(1).strip()
                score = float(m.group(2))
                if 0 <= score <= 100 and subject not in seen:
                    seen.add(subject)
                    results.append({'subject': subject.title(), 'score': score})

        # Pattern 3: Mixed case subjects (fallback)
        # "Mathematics  78" or "History  85"
        if not results:
            mixed = re.compile(
                r'^([A-Za-z][A-Za-z\s&/()\.\-]{3,}?)\s{2,}(\d{1,3})(?:\s|$)',
                re.MULTILINE
            )
            for m in mixed.finditer(raw_text):
                subject = m.group(1).strip()
                score = float(m.group(2))
                if 0 <= score <= 100 and subject not in seen:
                    seen.add(subject)
                    results.append({'subject': subject.title(), 'score': score})

        return results

    @staticmethod
    def extract_raw(all_rows: List[List[Any]], raw_text: str = '') -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """
        Extract subject/score pairs without needing known subjects.
        Primary: scan table rows for (text cell, nearby numeric cell) pairs.
        Fallback: regex line scanning for PDFs where table detection fails.
        """
        results = []
        seen = set()

        for row in all_rows:
            str_cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
            if len(str_cells) < 2:
                continue
            for i, cell in enumerate(str_cells):
                # Skip purely numeric cells and known metadata labels
                if re.fullmatch(r'[\d.]+', cell) or ParsingService.is_metadata(cell):
                    continue
                score = ParsingService.find_score(str_cells[i + 1:i + 4])
                if score is not None and cell not in seen:
                    seen.add(cell)
                    results.append({'subject': cell.title(), 'score': score})
                    break

        # If table extraction found nothing, fall back to text-line parsing
        if not results and raw_text:
            results = ParsingService.extract_from_text_lines(raw_text)

        period = ParsingService.build_period_from_text(raw_text)
        return period, results

    @staticmethod
    def build_period_from_text(raw_text: str) -> Dict[str, str]:
        """Parse school year and term label separately; build display string."""
        if not raw_text:
            return {'school_year': '', 'term_label': '', 'term_display': ''}

        # Extract school year
        sy_match = re.search(
            r'\b(20\d{2})\s*[-/]\s*(20\d{2})\b',
            raw_text,
        )
        if sy_match:
            school_year = f'{sy_match.group(1)}-{sy_match.group(2)}'
        else:
            school_year = ''

        # Extract term label
        term_patterns = [
            r'\b(First|Second|Third|Fourth)\s+Term\b',
            r'\b(Term\s*\d+)\b',
            r'\b(Fall|Spring|Summer|Winter)\s+20\d{2}\b',
            r'\b(Midterm|Midterms|Final|Finals)\b',
        ]
        term_label = ''
        for pattern in term_patterns:
            m = re.search(pattern, raw_text, re.IGNORECASE)
            if m:
                term_label = m.group(0).strip()
                break

        # Build display string
        if term_label and school_year:
            term_display = f'{term_label} · {school_year}'
        elif term_label:
            term_display = term_label
        elif school_year:
            term_display = f'Year {school_year}'
        else:
            term_display = 'Term'

        return {
            'school_year': school_year,
            'term_label': term_label,
            'term_display': term_display,
        }

    @staticmethod
    def format_subject_display(name: str) -> str:
        """Canonical display form for a subject: trim, collapse spaces, title case."""
        s = re.sub(r'\s+', ' ', (name or '').strip())
        if not s:
            return ''
        return s.title()

    @staticmethod
    def resolve_subject_name(raw_name: str) -> str:
        """Format subject name without relying on subjects table lookup."""
        return ParsingService.format_subject_display(raw_name)
