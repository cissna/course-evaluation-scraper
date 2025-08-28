import json
import os
import re
from typing import List, Dict

class CourseGroupingService:
    def __init__(self, config_path='course_groupings.json'):
        self.config_path = config_path
        self.department_patterns = {}
        self.explicit_groupings = []
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.department_patterns = config.get('department_patterns', {})
            self.explicit_groupings = config.get('explicit_groupings', [])
        except Exception as e:
            raise ValueError(f"Failed to load config: {str(e)}")

    def _parse_course_code(self, code: str):
        # Match pattern "DEPT.NUM.NUM" e.g., "EN.601.485"
        m = re.match(r'^([A-Z]{2,}\.\d{3})\.(\d{3})$', code)
        if not m:
            return None, None
        dept, number = m.group(1), m.group(2)
        return dept, number

    def _get_department_equivalents(self, dept: str, number: str) -> List[str]:
        equivalents = []
        pattern_info = self.department_patterns.get(dept)
        if not pattern_info:
            return equivalents
        try:
            levels = pattern_info.get("equivalent_levels", [])
            # Find course number's level; assume last digit is hundreds (e.g. 485 -> 400)
            try:
                course_level = int(number)
            except Exception:
                return equivalents
            # Generate codes for all levels in equivalent_levels
            for lvl in levels:
                equiv_number = f"{lvl + int(number)%100:03d}"
                equivalents.append(f"{dept}.{equiv_number}")
        except Exception:
            pass
        return equivalents

    def _find_explicit_group(self, course_code: str):
        for group in self.explicit_groupings:
            if course_code in group.get("courses", []):
                return group
        return None

    def get_grouped_courses(self, course_code: str) -> List[str]:
        dept, number = self._parse_course_code(course_code)
        explicit_group = self._find_explicit_group(course_code)
        grouped_courses = set()

        if explicit_group:
            grouped_courses.update(explicit_group.get("courses", []))

        # Department-based equivalents
        if dept and number:
            equivs = self._get_department_equivalents(dept, number)
            grouped_courses.update(equivs)
            grouped_courses.add(f"{dept}.{number}")

        # If grouped_courses is empty, return [course_code]
        if not grouped_courses:
            return [course_code]
        return sorted(grouped_courses)

    def is_course_grouped(self, course_code: str) -> bool:
        dept, number = self._parse_course_code(course_code)
        if dept and number and self._get_department_equivalents(dept, number):
            return True
        if self._find_explicit_group(course_code):
            return True
        return False

    def get_group_info(self, course_code: str) -> Dict:
        dept, number = self._parse_course_code(course_code)
        info = {}
        explicit_group = self._find_explicit_group(course_code)
        if explicit_group:
            info["courses"] = sorted(explicit_group.get("courses", []))
            info["description"] = explicit_group.get("description", "")
            return info
        # Department-pattern group
        if dept and number:
            equivs = self._get_department_equivalents(dept, number)
            if equivs:
                # In this simple format, description is not supplied for department patterns
                info["courses"] = sorted(list(set(equivs + [f"{dept}.{number}"])))
                info["description"] = ""
                return info
        return {}
