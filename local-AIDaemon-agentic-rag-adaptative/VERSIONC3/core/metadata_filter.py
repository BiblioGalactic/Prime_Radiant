#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    METADATA FILTER - Filtrado por Metadatos
========================================
Sistema de filtrado de documentos RAG basado en metadatos.
Permite:
- Filtrar por fecha, autor, categoría, idioma, etc.
- Aplicar reglas complejas con AND/OR/NOT
- Extraer metadatos automáticamente de queries
========================================
"""

import os
import sys
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MetadataFilter")


class FilterOperator(Enum):
    """Operadores de filtro"""
    EQUALS = "eq"           # Igual a
    NOT_EQUALS = "neq"      # No igual a
    CONTAINS = "contains"   # Contiene (strings)
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "gt"     # Mayor que
    LESS_THAN = "lt"        # Menor que
    GREATER_EQ = "gte"      # Mayor o igual
    LESS_EQ = "lte"         # Menor o igual
    IN = "in"               # En lista
    NOT_IN = "not_in"       # No en lista
    REGEX = "regex"         # Expresión regular
    EXISTS = "exists"       # Campo existe
    NOT_EXISTS = "not_exists"
    BETWEEN = "between"     # Entre dos valores


class LogicalOperator(Enum):
    """Operadores lógicos"""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class FilterCondition:
    """Condición de filtro individual"""
    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False


@dataclass
class FilterGroup:
    """Grupo de condiciones con operador lógico"""
    conditions: List[Union[FilterCondition, 'FilterGroup']]
    logical_op: LogicalOperator = LogicalOperator.AND


@dataclass
class FilterResult:
    """Resultado de aplicar filtros"""
    original_count: int
    filtered_count: int
    documents: List[Dict]
    filters_applied: List[str]
    execution_time_ms: float


class MetadataFilter:
    """
    Sistema de filtrado de documentos por metadatos.

    Soporta:
    - Filtros simples y compuestos
    - Extracción automática de filtros de queries
    - Metadatos comunes: date, author, category, language, source, etc.
    """

    # Patrones para extraer filtros de queries naturales
    DATE_PATTERNS = [
        (r'(?:de|del|desde|en)\s+(\d{4})', 'year_gte'),
        (r'(?:hasta|antes de)\s+(\d{4})', 'year_lte'),
        (r'(?:entre)\s+(\d{4})\s+y\s+(\d{4})', 'year_between'),
        (r'(?:hoy|today)', 'date_today'),
        (r'(?:ayer|yesterday)', 'date_yesterday'),
        (r'(?:esta semana|this week)', 'date_this_week'),
        (r'(?:este mes|this month)', 'date_this_month'),
        (r'(?:este año|this year)', 'date_this_year'),
        (r'(?:últimos?\s+(\d+)\s+(?:días?|days?))', 'date_last_n_days'),
        (r'(?:últimos?\s+(\d+)\s+(?:meses?|months?))', 'date_last_n_months'),
    ]

    LANGUAGE_PATTERNS = [
        (r'\b(?:en español|spanish)\b', 'es'),
        (r'\b(?:en inglés|in english|english)\b', 'en'),
        (r'\b(?:en francés|french)\b', 'fr'),
        (r'\b(?:en alemán|german)\b', 'de'),
        (r'\b(?:en portugués|portuguese)\b', 'pt'),
    ]

    CATEGORY_PATTERNS = [
        (r'\b(?:ciencia|science)\b', 'science'),
        (r'\b(?:tecnología|technology|tech)\b', 'technology'),
        (r'\b(?:historia|history)\b', 'history'),
        (r'\b(?:medicina|medicine|medical)\b', 'medicine'),
        (r'\b(?:arte|art)\b', 'art'),
        (r'\b(?:deportes?|sports?)\b', 'sports'),
        (r'\b(?:música|music)\b', 'music'),
        (r'\b(?:política|politics)\b', 'politics'),
        (r'\b(?:economía|economy|economics)\b', 'economics'),
    ]

    SOURCE_PATTERNS = [
        (r'\b(?:wikipedia)\b', 'wikipedia'),
        (r'\b(?:arxiv)\b', 'arxiv'),
        (r'\b(?:pubmed)\b', 'pubmed'),
        (r'\b(?:github)\b', 'github'),
    ]

    def __init__(self):
        """Inicializar filtro de metadatos"""
        self._custom_extractors: List[Callable] = []

    def register_extractor(self, extractor: Callable[[str], Optional[FilterCondition]]):
        """Registrar extractor personalizado de filtros"""
        self._custom_extractors.append(extractor)

    def apply_filter(
        self,
        documents: List[Dict],
        filter_group: FilterGroup
    ) -> FilterResult:
        """
        Aplicar grupo de filtros a documentos.

        Args:
            documents: Lista de documentos con metadatos
            filter_group: Grupo de filtros a aplicar

        Returns:
            FilterResult con documentos filtrados
        """
        import time
        start = time.time()

        original_count = len(documents)
        filtered = []
        filters_applied = []

        for doc in documents:
            if self._evaluate_group(doc, filter_group):
                filtered.append(doc)

        # Generar descripción de filtros
        filters_applied = self._describe_filter_group(filter_group)

        return FilterResult(
            original_count=original_count,
            filtered_count=len(filtered),
            documents=filtered,
            filters_applied=filters_applied,
            execution_time_ms=(time.time() - start) * 1000
        )

    def apply_conditions(
        self,
        documents: List[Dict],
        conditions: List[FilterCondition],
        logical_op: LogicalOperator = LogicalOperator.AND
    ) -> FilterResult:
        """
        Aplicar lista de condiciones.

        Args:
            documents: Documentos a filtrar
            conditions: Lista de condiciones
            logical_op: Operador lógico entre condiciones

        Returns:
            FilterResult
        """
        group = FilterGroup(
            conditions=conditions,
            logical_op=logical_op
        )
        return self.apply_filter(documents, group)

    def extract_filters_from_query(self, query: str) -> List[FilterCondition]:
        """
        Extraer filtros automáticamente de una query natural.

        Args:
            query: Query en lenguaje natural

        Returns:
            Lista de condiciones extraídas
        """
        conditions = []
        query_lower = query.lower()

        # Extraer filtros de fecha
        date_filter = self._extract_date_filter(query_lower)
        if date_filter:
            conditions.append(date_filter)

        # Extraer filtros de idioma
        for pattern, lang in self.LANGUAGE_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                conditions.append(FilterCondition(
                    field="language",
                    operator=FilterOperator.EQUALS,
                    value=lang
                ))
                break

        # Extraer filtros de categoría
        for pattern, category in self.CATEGORY_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                conditions.append(FilterCondition(
                    field="category",
                    operator=FilterOperator.EQUALS,
                    value=category
                ))
                break

        # Extraer filtros de fuente
        for pattern, source in self.SOURCE_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                conditions.append(FilterCondition(
                    field="source",
                    operator=FilterOperator.EQUALS,
                    value=source
                ))
                break

        # Aplicar extractores personalizados
        for extractor in self._custom_extractors:
            try:
                result = extractor(query)
                if result:
                    conditions.append(result)
            except Exception as e:
                logger.warning(f"Custom extractor failed: {e}")

        return conditions

    def _extract_date_filter(self, query: str) -> Optional[FilterCondition]:
        """Extraer filtro de fecha de query"""
        now = datetime.now()

        for pattern, filter_type in self.DATE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if not match:
                continue

            if filter_type == 'year_gte':
                year = int(match.group(1))
                return FilterCondition(
                    field="year",
                    operator=FilterOperator.GREATER_EQ,
                    value=year
                )

            elif filter_type == 'year_lte':
                year = int(match.group(1))
                return FilterCondition(
                    field="year",
                    operator=FilterOperator.LESS_EQ,
                    value=year
                )

            elif filter_type == 'year_between':
                year1 = int(match.group(1))
                year2 = int(match.group(2))
                return FilterCondition(
                    field="year",
                    operator=FilterOperator.BETWEEN,
                    value=(min(year1, year2), max(year1, year2))
                )

            elif filter_type == 'date_today':
                return FilterCondition(
                    field="date",
                    operator=FilterOperator.EQUALS,
                    value=now.strftime("%Y-%m-%d")
                )

            elif filter_type == 'date_yesterday':
                yesterday = now - timedelta(days=1)
                return FilterCondition(
                    field="date",
                    operator=FilterOperator.EQUALS,
                    value=yesterday.strftime("%Y-%m-%d")
                )

            elif filter_type == 'date_this_week':
                week_start = now - timedelta(days=now.weekday())
                return FilterCondition(
                    field="date",
                    operator=FilterOperator.GREATER_EQ,
                    value=week_start.strftime("%Y-%m-%d")
                )

            elif filter_type == 'date_this_month':
                month_start = now.replace(day=1)
                return FilterCondition(
                    field="date",
                    operator=FilterOperator.GREATER_EQ,
                    value=month_start.strftime("%Y-%m-%d")
                )

            elif filter_type == 'date_this_year':
                year_start = now.replace(month=1, day=1)
                return FilterCondition(
                    field="date",
                    operator=FilterOperator.GREATER_EQ,
                    value=year_start.strftime("%Y-%m-%d")
                )

            elif filter_type == 'date_last_n_days':
                n_days = int(match.group(1))
                cutoff = now - timedelta(days=n_days)
                return FilterCondition(
                    field="date",
                    operator=FilterOperator.GREATER_EQ,
                    value=cutoff.strftime("%Y-%m-%d")
                )

            elif filter_type == 'date_last_n_months':
                n_months = int(match.group(1))
                cutoff = now - timedelta(days=n_months * 30)
                return FilterCondition(
                    field="date",
                    operator=FilterOperator.GREATER_EQ,
                    value=cutoff.strftime("%Y-%m-%d")
                )

        return None

    def _evaluate_group(self, doc: Dict, group: FilterGroup) -> bool:
        """Evaluar un grupo de filtros contra un documento"""
        results = []

        for condition in group.conditions:
            if isinstance(condition, FilterGroup):
                result = self._evaluate_group(doc, condition)
            else:
                result = self._evaluate_condition(doc, condition)
            results.append(result)

        if group.logical_op == LogicalOperator.AND:
            return all(results) if results else True
        elif group.logical_op == LogicalOperator.OR:
            return any(results) if results else False
        elif group.logical_op == LogicalOperator.NOT:
            return not any(results) if results else True

        return True

    def _evaluate_condition(self, doc: Dict, condition: FilterCondition) -> bool:
        """Evaluar una condición individual"""
        # Obtener valor del documento (soporta nested fields con '.')
        doc_value = self._get_nested_value(doc, condition.field)

        # Manejar caso de campo no existente
        if condition.operator == FilterOperator.EXISTS:
            return doc_value is not None
        elif condition.operator == FilterOperator.NOT_EXISTS:
            return doc_value is None

        if doc_value is None:
            return False

        # Preparar valores para comparación
        if not condition.case_sensitive and isinstance(doc_value, str):
            doc_value = doc_value.lower()
        if not condition.case_sensitive and isinstance(condition.value, str):
            cmp_value = condition.value.lower()
        else:
            cmp_value = condition.value

        # Evaluar operador
        op = condition.operator

        if op == FilterOperator.EQUALS:
            return doc_value == cmp_value

        elif op == FilterOperator.NOT_EQUALS:
            return doc_value != cmp_value

        elif op == FilterOperator.CONTAINS:
            return cmp_value in str(doc_value)

        elif op == FilterOperator.NOT_CONTAINS:
            return cmp_value not in str(doc_value)

        elif op == FilterOperator.GREATER_THAN:
            return doc_value > cmp_value

        elif op == FilterOperator.LESS_THAN:
            return doc_value < cmp_value

        elif op == FilterOperator.GREATER_EQ:
            return doc_value >= cmp_value

        elif op == FilterOperator.LESS_EQ:
            return doc_value <= cmp_value

        elif op == FilterOperator.IN:
            if isinstance(cmp_value, (list, tuple)):
                return doc_value in cmp_value
            return False

        elif op == FilterOperator.NOT_IN:
            if isinstance(cmp_value, (list, tuple)):
                return doc_value not in cmp_value
            return True

        elif op == FilterOperator.REGEX:
            try:
                return bool(re.search(str(cmp_value), str(doc_value)))
            except:
                return False

        elif op == FilterOperator.BETWEEN:
            if isinstance(cmp_value, (list, tuple)) and len(cmp_value) >= 2:
                return cmp_value[0] <= doc_value <= cmp_value[1]
            return False

        return False

    def _get_nested_value(self, doc: Dict, field: str) -> Any:
        """Obtener valor de campo anidado (e.g., 'metadata.author')"""
        keys = field.split('.')
        value = doc

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _describe_filter_group(self, group: FilterGroup) -> List[str]:
        """Generar descripción de filtros aplicados"""
        descriptions = []

        for condition in group.conditions:
            if isinstance(condition, FilterGroup):
                sub_descs = self._describe_filter_group(condition)
                descriptions.append(f"({' {group.logical_op.value} '.join(sub_descs)})")
            else:
                desc = f"{condition.field} {condition.operator.value} {condition.value}"
                descriptions.append(desc)

        return descriptions


# === Factory ===
_filter_instance: Optional[MetadataFilter] = None


def get_metadata_filter() -> MetadataFilter:
    """Obtener instancia singleton"""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = MetadataFilter()
    return _filter_instance


# === Funciones de conveniencia ===
def filter_by_date(
    documents: List[Dict],
    start_date: str = None,
    end_date: str = None,
    date_field: str = "date"
) -> List[Dict]:
    """Filtrar documentos por rango de fecha"""
    conditions = []

    if start_date:
        conditions.append(FilterCondition(
            field=date_field,
            operator=FilterOperator.GREATER_EQ,
            value=start_date
        ))

    if end_date:
        conditions.append(FilterCondition(
            field=date_field,
            operator=FilterOperator.LESS_EQ,
            value=end_date
        ))

    if not conditions:
        return documents

    mf = get_metadata_filter()
    result = mf.apply_conditions(documents, conditions, LogicalOperator.AND)
    return result.documents


def filter_by_category(
    documents: List[Dict],
    categories: List[str],
    category_field: str = "category"
) -> List[Dict]:
    """Filtrar documentos por categoría"""
    condition = FilterCondition(
        field=category_field,
        operator=FilterOperator.IN,
        value=categories
    )

    mf = get_metadata_filter()
    result = mf.apply_conditions(documents, [condition])
    return result.documents


def filter_by_language(
    documents: List[Dict],
    language: str,
    language_field: str = "language"
) -> List[Dict]:
    """Filtrar documentos por idioma"""
    condition = FilterCondition(
        field=language_field,
        operator=FilterOperator.EQUALS,
        value=language
    )

    mf = get_metadata_filter()
    result = mf.apply_conditions(documents, [condition])
    return result.documents


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Metadata Filter ===\n")

    # Documentos de prueba
    docs = [
        {"title": "Python Basics", "language": "en", "category": "technology", "year": 2023, "date": "2023-06-15"},
        {"title": "Historia de España", "language": "es", "category": "history", "year": 2022, "date": "2022-03-20"},
        {"title": "Machine Learning", "language": "en", "category": "technology", "year": 2024, "date": "2024-01-10"},
        {"title": "Arte Renacentista", "language": "es", "category": "art", "year": 2021, "date": "2021-11-05"},
        {"title": "Medicina Moderna", "language": "es", "category": "medicine", "year": 2024, "date": "2024-02-28"},
    ]

    mf = get_metadata_filter()

    # Test 1: Filtrar por idioma
    print("Test 1: Documentos en español")
    result = filter_by_language(docs, "es")
    for doc in result:
        print(f"   - {doc['title']}")
    print()

    # Test 2: Filtrar por año
    print("Test 2: Documentos desde 2023")
    result = filter_by_date(docs, start_date="2023-01-01", date_field="date")
    for doc in result:
        print(f"   - {doc['title']} ({doc['date']})")
    print()

    # Test 3: Filtrar por categoría
    print("Test 3: Documentos de technology o medicine")
    result = filter_by_category(docs, ["technology", "medicine"])
    for doc in result:
        print(f"   - {doc['title']} [{doc['category']}]")
    print()

    # Test 4: Extraer filtros de query natural
    print("Test 4: Extraer filtros de query")
    test_queries = [
        "artículos de tecnología en español desde 2023",
        "historia entre 2020 y 2022",
        "documentos de los últimos 30 días sobre medicina",
    ]
    for query in test_queries:
        conditions = mf.extract_filters_from_query(query)
        print(f"   Query: {query}")
        for c in conditions:
            print(f"      - {c.field} {c.operator.value} {c.value}")
    print()

    # Test 5: Filtro compuesto
    print("Test 5: Filtro compuesto (technology AND year >= 2024)")
    conditions = [
        FilterCondition("category", FilterOperator.EQUALS, "technology"),
        FilterCondition("year", FilterOperator.GREATER_EQ, 2024)
    ]
    result = mf.apply_conditions(docs, conditions, LogicalOperator.AND)
    print(f"   Filtrados: {result.filtered_count}/{result.original_count}")
    for doc in result.documents:
        print(f"   - {doc['title']}")
