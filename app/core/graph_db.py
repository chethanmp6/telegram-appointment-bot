"""Neo4j graph database connection and operations."""

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta
import json

from app.core.config import settings


logger = logging.getLogger(__name__)


class GraphDatabase:
    """Neo4j graph database manager."""
    
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self.uri = settings.neo4j_uri
        self.auth = (settings.neo4j_user, settings.neo4j_password)
    
    async def connect(self):
        """Initialize Neo4j connection."""
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=self.auth)
            # Test connection
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get Neo4j session context manager."""
        if not self.driver:
            await self.connect()
        
        async with self.driver.session() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Neo4j session error: {e}")
                raise
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        async with self.get_session() as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]
    
    async def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute a write query in a transaction."""
        async with self.get_session() as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]
    
    # Schema initialization
    async def create_schema(self):
        """Create Neo4j schema with indexes and constraints."""
        schema_queries = [
            # Constraints
            "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT staff_id IF NOT EXISTS FOR (s:Staff) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT service_id IF NOT EXISTS FOR (srv:Service) REQUIRE srv.id IS UNIQUE",
            "CREATE CONSTRAINT appointment_id IF NOT EXISTS FOR (a:Appointment) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT policy_name IF NOT EXISTS FOR (p:Policy) REQUIRE p.name IS UNIQUE",
            
            # Indexes
            "CREATE INDEX customer_telegram_id IF NOT EXISTS FOR (c:Customer) ON (c.telegram_user_id)",
            "CREATE INDEX service_category IF NOT EXISTS FOR (s:Service) ON (s.category)",
            "CREATE INDEX appointment_date IF NOT EXISTS FOR (a:Appointment) ON (a.start_time)",
            "CREATE INDEX staff_specialization IF NOT EXISTS FOR (s:Staff) ON (s.specializations)",
            "CREATE INDEX concept_category IF NOT EXISTS FOR (c:Concept) ON (c.category)",
        ]
        
        for query in schema_queries:
            try:
                await self.execute_write_query(query)
                logger.info(f"Executed schema query: {query}")
            except Exception as e:
                logger.warning(f"Schema query failed (may already exist): {query} - {e}")
    
    # Customer operations
    async def create_customer_node(self, customer_data: Dict[str, Any]) -> Dict:
        """Create a customer node in the graph."""
        query = """
        CREATE (c:Customer {
            id: $id,
            telegram_user_id: $telegram_user_id,
            name: $name,
            phone: $phone,
            email: $email,
            preferences: $preferences,
            created_at: $created_at,
            updated_at: $updated_at
        })
        RETURN c
        """
        result = await self.execute_write_query(query, customer_data)
        return result[0]["c"] if result else {}
    
    async def get_customer_preferences(self, customer_id: str) -> Dict:
        """Get customer preferences and booking patterns."""
        query = """
        MATCH (c:Customer {id: $customer_id})
        OPTIONAL MATCH (c)-[r:PREFERS]->(s:Service)
        OPTIONAL MATCH (c)-[b:BOOKED]->(a:Appointment)-[:FOR_SERVICE]->(srv:Service)
        RETURN c.preferences as preferences,
               collect(DISTINCT {service: s.name, strength: r.strength, count: r.count}) as preferred_services,
               collect(DISTINCT {service: srv.name, date: a.start_time, satisfaction: b.satisfaction}) as booking_history
        """
        result = await self.execute_query(query, {"customer_id": customer_id})
        return result[0] if result else {}
    
    async def update_customer_preferences(self, customer_id: str, service_id: str, satisfaction: float = 1.0):
        """Update customer preferences based on booking behavior."""
        query = """
        MATCH (c:Customer {id: $customer_id})
        MATCH (s:Service {id: $service_id})
        MERGE (c)-[r:PREFERS]->(s)
        SET r.strength = COALESCE(r.strength, 0) + $satisfaction,
            r.count = COALESCE(r.count, 0) + 1,
            r.updated_at = datetime()
        RETURN r
        """
        return await self.execute_write_query(query, {
            "customer_id": customer_id,
            "service_id": service_id,
            "satisfaction": satisfaction
        })
    
    # Service recommendations
    async def get_service_recommendations(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """Get personalized service recommendations based on graph analysis."""
        query = """
        MATCH (c:Customer {id: $customer_id})
        
        // Find similar customers
        OPTIONAL MATCH (c)-[:PREFERS]->(s:Service)<-[:PREFERS]-(similar:Customer)
        WHERE similar.id <> c.id
        
        // Get services preferred by similar customers
        OPTIONAL MATCH (similar)-[r:PREFERS]->(recommended:Service)
        WHERE NOT (c)-[:PREFERS]->(recommended)
        
        // Also find services that complement already preferred services
        OPTIONAL MATCH (c)-[:PREFERS]->(preferred:Service)-[:COMPLEMENTS]->(complement:Service)
        WHERE NOT (c)-[:PREFERS]->(complement)
        
        // Calculate recommendation scores
        WITH recommended, complement, 
             sum(r.strength) as similarity_score,
             count(similar) as similar_customers
        
        RETURN 
            COALESCE(recommended.name, complement.name) as service_name,
            COALESCE(recommended.description, complement.description) as description,
            COALESCE(recommended.price, complement.price) as price,
            COALESCE(recommended.duration, complement.duration) as duration,
            COALESCE(similarity_score, 0) + COALESCE(similar_customers, 0) as score
        ORDER BY score DESC
        LIMIT $limit
        """
        return await self.execute_query(query, {"customer_id": customer_id, "limit": limit})
    
    async def get_staff_recommendations(self, service_id: str, customer_id: str) -> List[Dict]:
        """Get staff recommendations based on specializations and customer history."""
        query = """
        MATCH (s:Service {id: $service_id})
        MATCH (staff:Staff)-[:SPECIALIZES_IN]->(s)
        OPTIONAL MATCH (c:Customer {id: $customer_id})-[worked:WORKED_WITH]->(staff)
        OPTIONAL MATCH (staff)-[specializes:SPECIALIZES_IN]->(s)
        
        RETURN staff.name as name,
               staff.id as staff_id,
               COALESCE(worked.satisfaction, 0) as previous_satisfaction,
               COALESCE(specializes.expertise_level, 1) as expertise_level,
               COALESCE(worked.satisfaction, 0) + COALESCE(specializes.expertise_level, 1) as total_score
        ORDER BY total_score DESC
        """
        return await self.execute_query(query, {"service_id": service_id, "customer_id": customer_id})
    
    # Service relationships
    async def create_service_relationships(self, service_data: List[Dict]):
        """Create service nodes and their relationships."""
        for service in service_data:
            # Create service node
            query = """
            MERGE (s:Service {id: $id})
            SET s.name = $name,
                s.description = $description,
                s.price = $price,
                s.duration = $duration,
                s.category = $category,
                s.updated_at = datetime()
            RETURN s
            """
            await self.execute_write_query(query, service)
            
            # Create category relationships
            if service.get("category"):
                category_query = """
                MATCH (s:Service {id: $service_id})
                MERGE (c:Category {name: $category})
                MERGE (s)-[:IN_CATEGORY]->(c)
                """
                await self.execute_write_query(category_query, {
                    "service_id": service["id"],
                    "category": service["category"]
                })
    
    async def create_service_complements(self, service_id: str, complement_ids: List[str]):
        """Create complement relationships between services."""
        for complement_id in complement_ids:
            query = """
            MATCH (s1:Service {id: $service_id})
            MATCH (s2:Service {id: $complement_id})
            MERGE (s1)-[:COMPLEMENTS]->(s2)
            MERGE (s2)-[:COMPLEMENTS]->(s1)
            """
            await self.execute_write_query(query, {
                "service_id": service_id,
                "complement_id": complement_id
            })
    
    # Appointment operations
    async def create_appointment_node(self, appointment_data: Dict) -> Dict:
        """Create appointment node and relationships."""
        query = """
        MATCH (c:Customer {id: $customer_id})
        MATCH (staff:Staff {id: $staff_id})
        MATCH (s:Service {id: $service_id})
        
        CREATE (a:Appointment {
            id: $id,
            start_time: datetime($start_time),
            end_time: datetime($end_time),
            status: $status,
            created_at: datetime()
        })
        
        CREATE (c)-[:BOOKED]->(a)
        CREATE (a)-[:ASSIGNED_TO]->(staff)
        CREATE (a)-[:FOR_SERVICE]->(s)
        
        RETURN a
        """
        result = await self.execute_write_query(query, appointment_data)
        return result[0]["a"] if result else {}
    
    async def update_appointment_feedback(self, appointment_id: str, customer_id: str, staff_id: str, satisfaction: float):
        """Update appointment feedback and relationships."""
        query = """
        MATCH (a:Appointment {id: $appointment_id})
        MATCH (c:Customer {id: $customer_id})
        MATCH (staff:Staff {id: $staff_id})
        
        // Update customer-staff relationship
        MERGE (c)-[r:WORKED_WITH]->(staff)
        SET r.satisfaction = (COALESCE(r.satisfaction, 0) + $satisfaction) / 2,
            r.count = COALESCE(r.count, 0) + 1,
            r.updated_at = datetime()
        
        // Update appointment
        SET a.satisfaction = $satisfaction,
            a.updated_at = datetime()
        
        RETURN r
        """
        return await self.execute_write_query(query, {
            "appointment_id": appointment_id,
            "customer_id": customer_id,
            "staff_id": staff_id,
            "satisfaction": satisfaction
        })
    
    # Knowledge graph operations
    async def create_knowledge_graph(self, knowledge_data: List[Dict]):
        """Create knowledge graph from business information."""
        for item in knowledge_data:
            # Create concept node
            query = """
            MERGE (c:Concept {name: $name})
            SET c.description = $description,
                c.category = $category,
                c.content = $content,
                c.updated_at = datetime()
            RETURN c
            """
            await self.execute_write_query(query, item)
            
            # Create relationships
            if item.get("related_concepts"):
                for related in item["related_concepts"]:
                    relation_query = """
                    MATCH (c1:Concept {name: $concept1})
                    MATCH (c2:Concept {name: $concept2})
                    MERGE (c1)-[:RELATES_TO {strength: $strength}]->(c2)
                    """
                    await self.execute_write_query(relation_query, {
                        "concept1": item["name"],
                        "concept2": related["name"],
                        "strength": related.get("strength", 1.0)
                    })
    
    async def search_knowledge_graph(self, query: str, context: Dict = None) -> List[Dict]:
        """Search knowledge graph for relevant information."""
        cypher_query = """
        MATCH (c:Concept)
        WHERE c.name CONTAINS $query OR c.description CONTAINS $query OR c.content CONTAINS $query
        
        // Find related concepts
        OPTIONAL MATCH (c)-[r:RELATES_TO]->(related:Concept)
        
        RETURN c.name as concept,
               c.description as description,
               c.content as content,
               c.category as category,
               collect({name: related.name, strength: r.strength}) as related_concepts
        ORDER BY 
            CASE 
                WHEN c.name CONTAINS $query THEN 3
                WHEN c.description CONTAINS $query THEN 2
                ELSE 1
            END DESC
        LIMIT 10
        """
        return await self.execute_query(cypher_query, {"query": query})
    
    # Analytics and insights
    async def get_customer_analytics(self, customer_id: str) -> Dict:
        """Get comprehensive customer analytics."""
        query = """
        MATCH (c:Customer {id: $customer_id})
        
        // Booking patterns
        OPTIONAL MATCH (c)-[:BOOKED]->(a:Appointment)
        WITH c, count(a) as total_appointments,
             collect(a.start_time) as appointment_times
        
        // Service preferences
        OPTIONAL MATCH (c)-[p:PREFERS]->(s:Service)
        WITH c, total_appointments, appointment_times,
             collect({service: s.name, strength: p.strength, count: p.count}) as preferences
        
        // Staff relationships
        OPTIONAL MATCH (c)-[w:WORKED_WITH]->(staff:Staff)
        WITH c, total_appointments, appointment_times, preferences,
             collect({staff: staff.name, satisfaction: w.satisfaction, count: w.count}) as staff_relationships
        
        RETURN {
            customer_id: c.id,
            total_appointments: total_appointments,
            preferences: preferences,
            staff_relationships: staff_relationships,
            booking_frequency: size(appointment_times)
        } as analytics
        """
        result = await self.execute_query(query, {"customer_id": customer_id})
        return result[0]["analytics"] if result else {}
    
    async def get_business_insights(self) -> Dict:
        """Get overall business insights from the graph."""
        query = """
        // Popular services
        MATCH (s:Service)<-[:FOR_SERVICE]-(a:Appointment)
        WITH s, count(a) as bookings
        ORDER BY bookings DESC
        LIMIT 5
        
        WITH collect({service: s.name, bookings: bookings}) as popular_services
        
        // Staff performance
        MATCH (staff:Staff)<-[:ASSIGNED_TO]-(a:Appointment)
        OPTIONAL MATCH (c:Customer)-[w:WORKED_WITH]->(staff)
        WITH popular_services, staff, count(a) as appointments, avg(w.satisfaction) as avg_satisfaction
        ORDER BY appointments DESC, avg_satisfaction DESC
        LIMIT 5
        
        WITH popular_services, collect({staff: staff.name, appointments: appointments, satisfaction: avg_satisfaction}) as top_staff
        
        // Customer segments
        MATCH (c:Customer)-[p:PREFERS]->(s:Service)
        WITH popular_services, top_staff, s.category as category, count(c) as customers
        ORDER BY customers DESC
        LIMIT 5
        
        RETURN {
            popular_services: popular_services,
            top_staff: top_staff,
            customer_segments: collect({category: category, customers: customers})
        } as insights
        """
        result = await self.execute_query(query)
        return result[0]["insights"] if result else {}
    
    # Health check
    async def health_check(self) -> bool:
        """Check Neo4j database health."""
        try:
            await self.execute_query("RETURN 1 as health")
            return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False


# Global graph database instance
graph_db = GraphDatabase()


async def get_graph_db() -> GraphDatabase:
    """Dependency for FastAPI to get graph database instance."""
    return graph_db


async def init_graph_database():
    """Initialize graph database connection and schema."""
    await graph_db.connect()
    await graph_db.create_schema()
    logger.info("Graph database initialized")


async def close_graph_database():
    """Close graph database connection."""
    await graph_db.close()