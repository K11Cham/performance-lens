# results_service.py - Results business logic

from typing import List, Dict, Any, Optional
from ..models.database import Database
from ..services.parsing_service import ParsingService


class ResultsService:
    """Service for handling results operations."""
    
    @staticmethod
    def normalize_results_rows(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize subject names, clamp scores to 0–100, drop empty subjects.
        Case-insensitive duplicates collapse; last row wins.
        """
        merged = {}
        for r in results:
            canon = ParsingService.resolve_subject_name(r.get('subject', ''))
            if not canon:
                continue
            try:
                score = float(r['score'])
            except (TypeError, ValueError):
                continue
            score = max(0.0, min(100.0, score))
            merged[canon.casefold()] = {'subject': canon, 'score': score}
        return list(merged.values())
    
    @staticmethod
    def save_results(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save confirmed results to the database.
        Also upserts any new subjects into the subjects table.
        """
        results = payload.get('results', [])
        if not results:
            return {'status': 'error', 'message': 'No results provided.'}

        sy = (payload.get('school_year') or '').strip()
        tl = (payload.get('term_label') or '').strip()
        term_name = (payload.get('term_name') or '').strip()
        overwrite = bool(payload.get('overwrite'))

        if not tl:
            if not term_name:
                return {
                    'status': 'error',
                    'message': 'term_label or term_name is required.',
                }
            tl = term_name
        if not term_name:
            term_name = ResultsService._compose_term_display(sy, tl)

        conn = Database.get_db()
        try:
            results = ResultsService.normalize_results_rows(results)
            if not results:
                conn.close()
                return {'status': 'error', 'message': 'No valid subject/score rows to save.'}

            exists = conn.execute(
                'SELECT 1 FROM results WHERE school_year = ? AND term_label = ? LIMIT 1',
                (sy, tl),
            ).fetchone()
            if exists and not overwrite:
                conn.close()
                return {
                    'status': 'conflict',
                    'message': 'Results already exist for this school year and term. Send overwrite: true to replace them.',
                    'school_year': sy,
                    'term_label': tl,
                }

            if exists and overwrite:
                conn.execute(
                    'DELETE FROM results WHERE school_year = ? AND term_label = ?',
                    (sy, tl),
                )

            conn.executemany(
                'INSERT INTO results (term_name, school_year, term_label, subject, score) VALUES (?, ?, ?, ?, ?)',
                [(term_name, sy, tl, r['subject'], r['score']) for r in results],
            )
            conn.executemany(
                'INSERT OR IGNORE INTO subjects (name) VALUES (?)',
                [(r['subject'],) for r in results],
            )
            conn.commit()
            return {'status': 'success', 'message': 'Results saved successfully.'}
        except Exception as e:
            conn.rollback()
            return {'status': 'error', 'message': f'Database error: {str(e)}'}
        finally:
            conn.close()

    @staticmethod
    def _compose_term_display(school_year: str, term_label: str) -> str:
        """Compose term display string from school year and term label."""
        sy = (school_year or '').strip()
        tl = (term_label or '').strip()
        if tl and sy:
            return f'{tl} · {sy}'
        if tl:
            return tl
        if sy:
            return f'Year {sy}'
        return 'Term'
    
    @staticmethod
    def get_user_results(user_id: int) -> List[Dict[str, Any]]:
        """Get all results for a user."""
        conn = Database.get_db()
        try:
            rows = conn.execute(
                'SELECT id, term_name, school_year, term_label, subject, score FROM results WHERE user_id = ? ORDER BY id',
                (user_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    @staticmethod
    def get_subjects() -> List[str]:
        """Return all subject names currently stored in the DB."""
        conn = Database.get_db()
        try:
            rows = conn.execute('SELECT name FROM subjects ORDER BY name').fetchall()
            return [r['name'] for r in rows]
        finally:
            conn.close()
