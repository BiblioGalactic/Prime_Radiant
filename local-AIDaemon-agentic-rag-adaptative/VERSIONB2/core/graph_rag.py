#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================
    GRAPH RAG - RAG con Grafos de Conocimiento
========================================
Sistema de RAG mejorado usando grafos de conocimiento.

Arquitectura:
1. Extracción de entidades y relaciones de documentos
2. Construcción de grafo de conocimiento
3. Navegación del grafo para contexto expandido
4. Fusión de recuperación vectorial + grafo
========================================
"""

import os
import sys
import re
import json
import sqlite3
import hashlib
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

# === Setup paths ===
BASE_DIR = os.path.expanduser("~/wikirag")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GraphRAG")


class EntityType(Enum):
    """Tipos de entidad"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    EVENT = "event"
    TECHNOLOGY = "technology"
    DATE = "date"
    PRODUCT = "product"
    UNKNOWN = "unknown"


class RelationType(Enum):
    """Tipos de relación"""
    IS_A = "is_a"               # Es un tipo de
    PART_OF = "part_of"         # Es parte de
    HAS_PART = "has_part"       # Tiene como parte
    RELATED_TO = "related_to"   # Relacionado con
    CREATED_BY = "created_by"   # Creado por
    LOCATED_IN = "located_in"   # Ubicado en
    WORKS_FOR = "works_for"     # Trabaja para
    BELONGS_TO = "belongs_to"   # Pertenece a
    FOUNDED = "founded"         # Fundó
    OCCURRED_IN = "occurred_in" # Ocurrió en
    USES = "uses"               # Usa
    SIMILAR_TO = "similar_to"   # Similar a


@dataclass
class Entity:
    """Entidad del grafo"""
    id: str
    name: str
    type: EntityType
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    source_docs: List[str] = field(default_factory=list)  # IDs de docs donde aparece
    mention_count: int = 1


@dataclass
class Relation:
    """Relación entre entidades"""
    source_id: str
    target_id: str
    type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    source_docs: List[str] = field(default_factory=list)


@dataclass
class GraphSearchResult:
    """Resultado de búsqueda en grafo"""
    entities: List[Entity]
    relations: List[Relation]
    subgraph: Dict[str, List[str]]  # adjacency list
    paths: List[List[str]]  # Caminos encontrados
    relevance_score: float


class KnowledgeGraph:
    """
    Grafo de conocimiento en memoria con persistencia SQLite.
    """

    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: Ruta a SQLite para persistencia
        """
        self.db_path = db_path or os.path.join(BASE_DIR, "data", "knowledge_graph.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Estructuras en memoria
        self._entities: Dict[str, Entity] = {}
        self._relations: List[Relation] = []
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)  # source -> targets
        self._reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)  # target -> sources

        # Índices
        self._name_index: Dict[str, str] = {}  # name.lower() -> entity_id
        self._type_index: Dict[EntityType, Set[str]] = defaultdict(set)

        # Inicializar DB
        self._init_db()
        self._load_from_db()

    def _init_db(self):
        """Inicializar estructura de base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    aliases TEXT DEFAULT '[]',
                    properties TEXT DEFAULT '{}',
                    source_docs TEXT DEFAULT '[]',
                    mention_count INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties TEXT DEFAULT '{}',
                    source_docs TEXT DEFAULT '[]',
                    FOREIGN KEY (source_id) REFERENCES entities(id),
                    FOREIGN KEY (target_id) REFERENCES entities(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id)")
            conn.commit()

    def _load_from_db(self):
        """Cargar grafo desde DB"""
        with sqlite3.connect(self.db_path) as conn:
            # Cargar entidades
            cursor = conn.execute("SELECT * FROM entities")
            for row in cursor.fetchall():
                entity = Entity(
                    id=row[0],
                    name=row[1],
                    type=EntityType(row[2]),
                    aliases=json.loads(row[3]),
                    properties=json.loads(row[4]),
                    source_docs=json.loads(row[5]),
                    mention_count=row[6]
                )
                self._entities[entity.id] = entity
                self._name_index[entity.name.lower()] = entity.id
                self._type_index[entity.type].add(entity.id)

            # Cargar relaciones
            cursor = conn.execute("SELECT * FROM relations")
            for row in cursor.fetchall():
                relation = Relation(
                    source_id=row[1],
                    target_id=row[2],
                    type=RelationType(row[3]),
                    weight=row[4],
                    properties=json.loads(row[5]),
                    source_docs=json.loads(row[6])
                )
                self._relations.append(relation)
                self._adjacency[relation.source_id].add(relation.target_id)
                self._reverse_adjacency[relation.target_id].add(relation.source_id)

        logger.info(f"Grafo cargado: {len(self._entities)} entidades, {len(self._relations)} relaciones")

    def add_entity(self, entity: Entity, persist: bool = True) -> str:
        """Añadir entidad al grafo"""
        self._entities[entity.id] = entity
        self._name_index[entity.name.lower()] = entity.id
        self._type_index[entity.type].add(entity.id)

        if persist:
            self._persist_entity(entity)

        return entity.id

    def add_relation(self, relation: Relation, persist: bool = True):
        """Añadir relación al grafo"""
        self._relations.append(relation)
        self._adjacency[relation.source_id].add(relation.target_id)
        self._reverse_adjacency[relation.target_id].add(relation.source_id)

        if persist:
            self._persist_relation(relation)

    def _persist_entity(self, entity: Entity):
        """Guardar entidad en DB"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO entities
                (id, name, type, aliases, properties, source_docs, mention_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.id,
                entity.name,
                entity.type.value,
                json.dumps(entity.aliases),
                json.dumps(entity.properties),
                json.dumps(entity.source_docs),
                entity.mention_count
            ))
            conn.commit()

    def _persist_relation(self, relation: Relation):
        """Guardar relación en DB"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO relations
                (source_id, target_id, type, weight, properties, source_docs)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                relation.source_id,
                relation.target_id,
                relation.type.value,
                relation.weight,
                json.dumps(relation.properties),
                json.dumps(relation.source_docs)
            ))
            conn.commit()

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Obtener entidad por ID"""
        return self._entities.get(entity_id)

    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        """Buscar entidad por nombre"""
        entity_id = self._name_index.get(name.lower())
        if entity_id:
            return self._entities.get(entity_id)
        return None

    def get_neighbors(self, entity_id: str, max_depth: int = 1) -> Set[str]:
        """Obtener vecinos de una entidad hasta cierta profundidad"""
        visited = set()
        current = {entity_id}

        for _ in range(max_depth):
            next_level = set()
            for eid in current:
                if eid in visited:
                    continue
                visited.add(eid)
                next_level.update(self._adjacency.get(eid, set()))
                next_level.update(self._reverse_adjacency.get(eid, set()))
            current = next_level - visited

        return visited - {entity_id}

    def get_relations_for(self, entity_id: str) -> List[Relation]:
        """Obtener relaciones de una entidad"""
        return [
            r for r in self._relations
            if r.source_id == entity_id or r.target_id == entity_id
        ]

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 4
    ) -> Optional[List[str]]:
        """Encontrar camino entre dos entidades (BFS)"""
        if source_id == target_id:
            return [source_id]

        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for neighbor in self._adjacency.get(current, set()):
                if neighbor == target_id:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

            for neighbor in self._reverse_adjacency.get(current, set()):
                if neighbor == target_id:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del grafo"""
        type_counts = {t.value: len(ids) for t, ids in self._type_index.items()}
        return {
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
            "entity_types": type_counts
        }


class EntityExtractor:
    """
    Extractor de entidades y relaciones de texto.
    Usa patrones + heurísticas (puede mejorarse con NER models).
    """

    # Patrones para detectar tipos de entidad
    PERSON_PATTERNS = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',  # Nombres propios
        r'\b(Dr\.|Prof\.|Sr\.|Sra\.|Mr\.|Mrs\.)\s+([A-Z][a-z]+)',
    ]

    ORGANIZATION_PATTERNS = [
        r'\b([A-Z][A-Za-z]*(?:\s+(?:Inc|Corp|Ltd|LLC|S\.A\.|S\.L\.|Company|Universidad|Institute|Foundation))?)\b',
        r'\b((?:Universidad|Instituto|Empresa|Compañía|Organización)\s+(?:de\s+)?[A-Z][a-z]+)\b',
    ]

    LOCATION_PATTERNS = [
        r'\b((?:en|de|desde)\s+)?([A-Z][a-z]+(?:,\s+[A-Z][a-z]+)?)\b',
    ]

    TECHNOLOGY_PATTERNS = [
        r'\b([A-Z][a-z]*(?:Script|Kit|Flow|Base|Hub|ware|soft))\b',
        r'\b(Python|JavaScript|Java|C\+\+|Ruby|Go|Rust|Swift|Kotlin)\b',
    ]

    def __init__(self, use_llm: bool = False):
        """
        Args:
            use_llm: Si usar LLM para extracción avanzada
        """
        self.use_llm = use_llm

    def extract_from_text(
        self,
        text: str,
        doc_id: str = None
    ) -> Tuple[List[Entity], List[Relation]]:
        """
        Extraer entidades y relaciones de texto.

        Args:
            text: Texto a procesar
            doc_id: ID del documento fuente

        Returns:
            Tupla (entidades, relaciones)
        """
        entities = []
        relations = []
        seen_names = set()

        # Extraer entidades por tipo
        for pattern in self.TECHNOLOGY_PATTERNS:
            for match in re.finditer(pattern, text):
                name = match.group(1) if match.lastindex else match.group()
                if name.lower() not in seen_names and len(name) > 2:
                    seen_names.add(name.lower())
                    entities.append(self._create_entity(name, EntityType.TECHNOLOGY, doc_id))

        for pattern in self.PERSON_PATTERNS:
            for match in re.finditer(pattern, text):
                name = match.group(1) if match.lastindex else match.group()
                if name.lower() not in seen_names and len(name) > 3:
                    # Filtrar falsos positivos comunes
                    if not self._is_common_word(name):
                        seen_names.add(name.lower())
                        entities.append(self._create_entity(name, EntityType.PERSON, doc_id))

        for pattern in self.ORGANIZATION_PATTERNS:
            for match in re.finditer(pattern, text):
                name = match.group(1) if match.lastindex else match.group()
                if name.lower() not in seen_names and len(name) > 3:
                    seen_names.add(name.lower())
                    entities.append(self._create_entity(name, EntityType.ORGANIZATION, doc_id))

        # Extraer conceptos de títulos/headers
        concepts = self._extract_concepts(text)
        for concept in concepts:
            if concept.lower() not in seen_names:
                seen_names.add(concept.lower())
                entities.append(self._create_entity(concept, EntityType.CONCEPT, doc_id))

        # Extraer relaciones básicas
        relations = self._extract_relations(text, entities, doc_id)

        return entities, relations

    def _create_entity(self, name: str, entity_type: EntityType, doc_id: str = None) -> Entity:
        """Crear entidad"""
        entity_id = hashlib.md5(name.lower().encode()).hexdigest()[:12]
        return Entity(
            id=entity_id,
            name=name,
            type=entity_type,
            source_docs=[doc_id] if doc_id else []
        )

    def _extract_concepts(self, text: str) -> List[str]:
        """Extraer conceptos principales"""
        concepts = []

        # Buscar patrones de definición
        patterns = [
            r'(?:es|son|significa|define)\s+(?:un[oa]?\s+)?([a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+)',
            r'([A-Za-záéíóúñ]+)\s+(?:es|son)\s+(?:un[oa]?\s+)?',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                concept = match.group(1).strip()
                if 3 < len(concept) < 50:
                    concepts.append(concept.title())

        return concepts[:10]  # Limitar

    def _extract_relations(
        self,
        text: str,
        entities: List[Entity],
        doc_id: str = None
    ) -> List[Relation]:
        """Extraer relaciones entre entidades"""
        relations = []

        if len(entities) < 2:
            return relations

        # Crear índice de entidades por nombre
        entity_map = {e.name.lower(): e for e in entities}

        # Patrones de relación
        relation_patterns = [
            (r'(\w+)\s+(?:es|fue|era)\s+(?:un[oa]?\s+)?(\w+)', RelationType.IS_A),
            (r'(\w+)\s+(?:parte de|pertenece a)\s+(\w+)', RelationType.PART_OF),
            (r'(\w+)\s+(?:creado?|desarrollado?)\s+por\s+(\w+)', RelationType.CREATED_BY),
            (r'(\w+)\s+(?:usa|utiliza)\s+(\w+)', RelationType.USES),
            (r'(\w+)\s+(?:ubicado?|localizado?)\s+en\s+(\w+)', RelationType.LOCATED_IN),
            (r'(\w+)\s+(?:trabaja|trabajó)\s+(?:para|en)\s+(\w+)', RelationType.WORKS_FOR),
            (r'(\w+)\s+(?:fundó|creó|estableció)\s+(\w+)', RelationType.FOUNDED),
        ]

        for pattern, rel_type in relation_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source_name = match.group(1).lower()
                target_name = match.group(2).lower()

                source_entity = entity_map.get(source_name)
                target_entity = entity_map.get(target_name)

                if source_entity and target_entity and source_entity.id != target_entity.id:
                    relations.append(Relation(
                        source_id=source_entity.id,
                        target_id=target_entity.id,
                        type=rel_type,
                        source_docs=[doc_id] if doc_id else []
                    ))

        # Co-ocurrencia: entidades en la misma oración
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            entities_in_sentence = [
                e for e in entities
                if e.name.lower() in sentence.lower()
            ]
            for i, e1 in enumerate(entities_in_sentence):
                for e2 in entities_in_sentence[i+1:]:
                    if e1.id != e2.id:
                        relations.append(Relation(
                            source_id=e1.id,
                            target_id=e2.id,
                            type=RelationType.RELATED_TO,
                            weight=0.5,
                            source_docs=[doc_id] if doc_id else []
                        ))

        return relations

    def _is_common_word(self, word: str) -> bool:
        """Verificar si es palabra común (falso positivo)"""
        common = {
            'the', 'this', 'that', 'these', 'those', 'what', 'which', 'when',
            'where', 'who', 'why', 'how', 'there', 'here', 'now', 'then',
            'el', 'la', 'los', 'las', 'esto', 'ese', 'esa', 'estos', 'esas',
            'que', 'cual', 'cuando', 'donde', 'quien', 'como', 'porque'
        }
        return word.lower() in common


class GraphRAG:
    """
    Sistema RAG mejorado con grafos de conocimiento.

    Combina:
    1. Búsqueda vectorial tradicional
    2. Navegación del grafo de conocimiento
    3. Expansión de contexto vía relaciones
    """

    def __init__(
        self,
        rag_manager=None,
        graph: KnowledgeGraph = None,
        extractor: EntityExtractor = None
    ):
        """
        Args:
            rag_manager: Instancia de RAGManager para búsqueda vectorial
            graph: Grafo de conocimiento
            extractor: Extractor de entidades
        """
        self.rag_manager = rag_manager
        self.graph = graph or KnowledgeGraph()
        self.extractor = extractor or EntityExtractor()

    def index_document(self, doc_id: str, text: str, metadata: Dict = None):
        """
        Indexar documento en el grafo.

        Args:
            doc_id: ID del documento
            text: Contenido del documento
            metadata: Metadatos adicionales
        """
        # Extraer entidades y relaciones
        entities, relations = self.extractor.extract_from_text(text, doc_id)

        # Añadir al grafo
        for entity in entities:
            existing = self.graph.find_entity_by_name(entity.name)
            if existing:
                # Actualizar entidad existente
                existing.mention_count += 1
                if doc_id and doc_id not in existing.source_docs:
                    existing.source_docs.append(doc_id)
                self.graph._persist_entity(existing)
            else:
                self.graph.add_entity(entity)

        for relation in relations:
            self.graph.add_relation(relation)

        logger.info(f"Indexado: {doc_id} -> {len(entities)} entidades, {len(relations)} relaciones")

    def search(
        self,
        query: str,
        k: int = 5,
        expand_with_graph: bool = True,
        max_graph_depth: int = 2
    ) -> Tuple[List[Dict], GraphSearchResult]:
        """
        Búsqueda híbrida: vectorial + grafo.

        Args:
            query: Query del usuario
            k: Número de resultados
            expand_with_graph: Si expandir usando grafo
            max_graph_depth: Profundidad máxima de navegación

        Returns:
            Tupla (documentos, resultado_grafo)
        """
        # 1. Búsqueda vectorial tradicional
        vector_docs = []
        if self.rag_manager:
            try:
                vector_docs = self.rag_manager.search("wikipedia", query, k=k)
            except Exception as e:
                logger.warning(f"Error en búsqueda vectorial: {e}")

        # 2. Extraer entidades de la query
        query_entities, _ = self.extractor.extract_from_text(query)

        # 3. Buscar entidades en el grafo
        graph_entities = []
        for qe in query_entities:
            found = self.graph.find_entity_by_name(qe.name)
            if found:
                graph_entities.append(found)

        # También buscar por palabras clave
        keywords = re.findall(r'\b[A-Z][a-z]+\b', query)
        for kw in keywords[:5]:
            found = self.graph.find_entity_by_name(kw)
            if found and found not in graph_entities:
                graph_entities.append(found)

        # 4. Expandir contexto via grafo
        expanded_entities = set()
        expanded_relations = []

        if expand_with_graph and graph_entities:
            for entity in graph_entities:
                # Obtener vecinos
                neighbors = self.graph.get_neighbors(entity.id, max_depth=max_graph_depth)
                expanded_entities.update(neighbors)

                # Obtener relaciones
                relations = self.graph.get_relations_for(entity.id)
                expanded_relations.extend(relations)

        # 5. Construir resultado del grafo
        all_entities = graph_entities + [
            self.graph.get_entity(eid)
            for eid in expanded_entities
            if self.graph.get_entity(eid)
        ]

        subgraph = defaultdict(list)
        for rel in expanded_relations:
            subgraph[rel.source_id].append(rel.target_id)

        graph_result = GraphSearchResult(
            entities=all_entities,
            relations=expanded_relations,
            subgraph=dict(subgraph),
            paths=[],
            relevance_score=len(graph_entities) / max(1, len(query_entities)) if query_entities else 0.5
        )

        # 6. Reordenar documentos usando información del grafo
        if vector_docs and graph_entities:
            vector_docs = self._rerank_with_graph(vector_docs, graph_entities)

        return vector_docs, graph_result

    def _rerank_with_graph(
        self,
        docs: List[Dict],
        graph_entities: List[Entity]
    ) -> List[Dict]:
        """Reordenar documentos usando información del grafo"""
        entity_names = {e.name.lower() for e in graph_entities}
        entity_docs = set()
        for e in graph_entities:
            entity_docs.update(e.source_docs)

        scored_docs = []
        for doc in docs:
            score = 0.0

            # Boost si documento contiene entidades encontradas
            doc_text = doc.get('content', doc.get('text', '')).lower()
            for name in entity_names:
                if name in doc_text:
                    score += 0.2

            # Boost si documento está en source_docs de entidades
            doc_id = doc.get('id', doc.get('doc_id', ''))
            if doc_id in entity_docs:
                score += 0.3

            doc['_graph_score'] = score
            scored_docs.append((doc, score))

        # Ordenar por score combinado (original + grafo)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs]

    def get_context_for_query(
        self,
        query: str,
        k: int = 3,
        include_graph_context: bool = True
    ) -> str:
        """
        Obtener contexto enriquecido para una query.

        Args:
            query: Query del usuario
            k: Número de documentos
            include_graph_context: Si incluir contexto del grafo

        Returns:
            Contexto como string
        """
        docs, graph_result = self.search(query, k=k)

        context_parts = []

        # Contexto de documentos
        for doc in docs[:k]:
            content = doc.get('content', doc.get('text', ''))
            context_parts.append(content[:500])

        # Contexto del grafo
        if include_graph_context and graph_result.entities:
            graph_context = "\n[Entidades relacionadas]:\n"
            for entity in graph_result.entities[:5]:
                graph_context += f"- {entity.name} ({entity.type.value})\n"

            # Añadir relaciones clave
            if graph_result.relations:
                graph_context += "\n[Relaciones]:\n"
                for rel in graph_result.relations[:5]:
                    source = self.graph.get_entity(rel.source_id)
                    target = self.graph.get_entity(rel.target_id)
                    if source and target:
                        graph_context += f"- {source.name} -> {rel.type.value} -> {target.name}\n"

            context_parts.append(graph_context)

        return "\n\n".join(context_parts)

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        graph_stats = self.graph.get_stats()
        return {
            "graph": graph_stats,
            "has_rag_manager": self.rag_manager is not None
        }


# === SINGLETON ===
_graph_rag_instance: Optional[GraphRAG] = None


def get_graph_rag(rag_manager=None) -> GraphRAG:
    """Obtener instancia singleton"""
    global _graph_rag_instance
    if _graph_rag_instance is None:
        _graph_rag_instance = GraphRAG(rag_manager=rag_manager)
    return _graph_rag_instance


# === CLI para pruebas ===
if __name__ == "__main__":
    print("=== Test Graph RAG ===\n")

    graph_rag = GraphRAG()

    # Indexar documentos de prueba
    test_docs = [
        ("doc1", "Python es un lenguaje de programación creado por Guido van Rossum en 1991. Python usa indentación para definir bloques de código."),
        ("doc2", "JavaScript fue creado por Brendan Eich en Netscape. JavaScript es el lenguaje de la web."),
        ("doc3", "Guido van Rossum trabajó en Google y luego en Dropbox. Van Rossum es conocido como el creador de Python."),
        ("doc4", "Machine Learning usa Python extensivamente. TensorFlow y PyTorch son frameworks populares de ML."),
    ]

    for doc_id, text in test_docs:
        graph_rag.index_document(doc_id, text)

    # Mostrar estadísticas
    stats = graph_rag.get_stats()
    print(f"📊 Estadísticas:")
    print(f"   Entidades: {stats['graph']['total_entities']}")
    print(f"   Relaciones: {stats['graph']['total_relations']}")
    print()

    # Test búsqueda
    test_queries = [
        "¿Quién creó Python?",
        "¿Qué es JavaScript?",
        "Machine Learning frameworks",
    ]

    for query in test_queries:
        print(f"🔍 Query: {query}")
        docs, graph_result = graph_rag.search(query, k=2)
        print(f"   Entidades encontradas: {len(graph_result.entities)}")
        for e in graph_result.entities[:3]:
            print(f"      - {e.name} ({e.type.value})")
        print(f"   Relaciones: {len(graph_result.relations)}")
        print()

    # Test contexto
    print("📝 Contexto enriquecido para 'Python':")
    context = graph_rag.get_context_for_query("Python", k=2)
    print(context[:500])
