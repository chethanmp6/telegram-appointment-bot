#!/usr/bin/env python3
"""
Script to populate Neo4j graph database with spa-related data.
This script creates nodes and relationships for spa services, staff, customers, and preferences.
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.core.graph_db import GraphDatabase
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpaGraphPopulator:
    """Populate Neo4j graph database with spa data."""
    
    def __init__(self):
        """Initialize the Neo4j graph database connection."""
        self.graph_db = GraphDatabase()
        
    async def connect(self):
        """Connect to Neo4j database."""
        await self.graph_db.connect()
        logger.info("Connected to Neo4j database")
        
    async def close(self):
        """Close Neo4j database connection."""
        await self.graph_db.close()
        logger.info("Closed Neo4j database connection")
        
    async def clear_database(self):
        """Clear all nodes and relationships (for development)."""
        query = "MATCH (n) DETACH DELETE n"
        await self.graph_db.execute_query(query)
        logger.info("Cleared all nodes and relationships")
        
    async def create_service_categories(self):
        """Create service category nodes."""
        categories = [
            {
                "name": "Massage Therapy",
                "description": "Various massage treatments for relaxation and therapeutic benefits",
                "color": "#4CAF50"
            },
            {
                "name": "Facial Treatments",
                "description": "Skincare treatments for face and neck area",
                "color": "#FF9800"
            },
            {
                "name": "Body Treatments",
                "description": "Full body treatments including scrubs and wraps",
                "color": "#9C27B0"
            },
            {
                "name": "Wellness Treatments",
                "description": "Holistic wellness and mental health treatments",
                "color": "#2196F3"
            },
            {
                "name": "Spa Packages",
                "description": "Combined treatment packages for complete spa experience",
                "color": "#FF5722"
            }
        ]
        
        for category in categories:
            query = """
            MERGE (c:ServiceCategory {name: $name})
            ON CREATE SET c.description = $description,
                         c.color = $color,
                         c.created_at = datetime()
            """
            await self.graph_db.execute_query(query, category)
            logger.info(f"Created service category: {category['name']}")
            
    async def create_services(self):
        """Create service nodes with properties."""
        services = [
            {
                "id": "massage-001",
                "name": "Swedish Massage",
                "category": "Massage Therapy",
                "description": "Classic full-body massage for relaxation",
                "duration": 60,
                "price": 120.0,
                "difficulty": "easy",
                "popularity": 0.9,
                "benefits": ["stress_reduction", "improved_circulation", "muscle_relaxation"],
                "contraindications": ["recent_surgery", "severe_inflammation"]
            },
            {
                "id": "massage-002",
                "name": "Deep Tissue Massage",
                "category": "Massage Therapy",
                "description": "Therapeutic massage for muscle knots and tension",
                "duration": 75,
                "price": 150.0,
                "difficulty": "advanced",
                "popularity": 0.8,
                "benefits": ["pain_relief", "muscle_knot_removal", "improved_mobility"],
                "contraindications": ["blood_clots", "recent_injuries"]
            },
            {
                "id": "massage-003",
                "name": "Hot Stone Massage",
                "category": "Massage Therapy",
                "description": "Relaxing massage with heated stones",
                "duration": 90,
                "price": 180.0,
                "difficulty": "intermediate",
                "popularity": 0.7,
                "benefits": ["deep_relaxation", "improved_circulation", "stress_relief"],
                "contraindications": ["pregnancy", "diabetes", "high_blood_pressure"]
            },
            {
                "id": "facial-001",
                "name": "Signature Hydrating Facial",
                "category": "Facial Treatments",
                "description": "Customized facial for skin hydration",
                "duration": 60,
                "price": 100.0,
                "difficulty": "easy",
                "popularity": 0.8,
                "benefits": ["deep_cleansing", "hydration", "improved_skin_texture"],
                "contraindications": ["active_acne_treatment", "recent_chemical_peels"]
            },
            {
                "id": "facial-002",
                "name": "Anti-Aging Facial",
                "category": "Facial Treatments",
                "description": "Advanced facial targeting signs of aging",
                "duration": 75,
                "price": 150.0,
                "difficulty": "advanced",
                "popularity": 0.6,
                "benefits": ["reduced_fine_lines", "improved_skin_elasticity", "brighter_complexion"],
                "contraindications": ["pregnancy", "active_skin_conditions"]
            },
            {
                "id": "body-001",
                "name": "Full Body Scrub",
                "category": "Body Treatments",
                "description": "Exfoliating treatment for smooth skin",
                "duration": 45,
                "price": 80.0,
                "difficulty": "easy",
                "popularity": 0.7,
                "benefits": ["smooth_skin", "improved_texture", "enhanced_circulation"],
                "contraindications": ["sunburn", "open_wounds"]
            },
            {
                "id": "body-002",
                "name": "Detox Body Wrap",
                "category": "Body Treatments",
                "description": "Purifying treatment for detoxification",
                "duration": 60,
                "price": 120.0,
                "difficulty": "intermediate",
                "popularity": 0.5,
                "benefits": ["detoxification", "skin_tightening", "improved_circulation"],
                "contraindications": ["pregnancy", "high_blood_pressure", "claustrophobia"]
            },
            {
                "id": "wellness-001",
                "name": "Aromatherapy Session",
                "category": "Wellness Treatments",
                "description": "Essential oil therapy for well-being",
                "duration": 30,
                "price": 60.0,
                "difficulty": "easy",
                "popularity": 0.6,
                "benefits": ["stress_reduction", "mood_enhancement", "better_sleep"],
                "contraindications": ["severe_allergies", "asthma"]
            },
            {
                "id": "wellness-002",
                "name": "Meditation Session",
                "category": "Wellness Treatments",
                "description": "Guided meditation for mental well-being",
                "duration": 45,
                "price": 70.0,
                "difficulty": "easy",
                "popularity": 0.4,
                "benefits": ["stress_reduction", "mental_clarity", "improved_focus"],
                "contraindications": ["severe_mental_health_conditions"]
            }
        ]
        
        for service in services:
            query = """
            MERGE (s:Service {id: $id})
            ON CREATE SET s.name = $name,
                         s.description = $description,
                         s.duration = $duration,
                         s.price = $price,
                         s.difficulty = $difficulty,
                         s.popularity = $popularity,
                         s.benefits = $benefits,
                         s.contraindications = $contraindications,
                         s.created_at = datetime()
            """
            await self.graph_db.execute_query(query, service)
            
            # Create relationship to category
            category_query = """
            MATCH (s:Service {id: $service_id})
            MATCH (c:ServiceCategory {name: $category})
            MERGE (s)-[:BELONGS_TO]->(c)
            """
            await self.graph_db.execute_query(category_query, {
                "service_id": service["id"],
                "category": service["category"]
            })
            
            logger.info(f"Created service: {service['name']}")
            
    async def create_staff_members(self):
        """Create staff nodes with specializations."""
        staff_members = [
            {
                "id": "staff-001",
                "name": "Sarah Thompson",
                "email": "sarah.thompson@spa.com",
                "role": "Senior Massage Therapist",
                "experience_years": 8,
                "specializations": ["Swedish Massage", "Deep Tissue Massage", "Hot Stone Massage"],
                "certifications": ["Licensed Massage Therapist", "Deep Tissue Specialist"],
                "rating": 4.9,
                "availability_hours": 40
            },
            {
                "id": "staff-002",
                "name": "Michael Chen",
                "email": "michael.chen@spa.com",
                "role": "Massage Therapist",
                "experience_years": 5,
                "specializations": ["Swedish Massage", "Aromatherapy Session"],
                "certifications": ["Licensed Massage Therapist", "Aromatherapy Certified"],
                "rating": 4.7,
                "availability_hours": 35
            },
            {
                "id": "staff-003",
                "name": "Emma Rodriguez",
                "email": "emma.rodriguez@spa.com",
                "role": "Esthetician",
                "experience_years": 6,
                "specializations": ["Signature Hydrating Facial", "Anti-Aging Facial"],
                "certifications": ["Licensed Esthetician", "Anti-Aging Specialist"],
                "rating": 4.8,
                "availability_hours": 38
            },
            {
                "id": "staff-004",
                "name": "James Wilson",
                "email": "james.wilson@spa.com",
                "role": "Body Treatment Specialist",
                "experience_years": 4,
                "specializations": ["Full Body Scrub", "Detox Body Wrap"],
                "certifications": ["Body Treatment Certified"],
                "rating": 4.6,
                "availability_hours": 32
            },
            {
                "id": "staff-005",
                "name": "Lisa Park",
                "email": "lisa.park@spa.com",
                "role": "Wellness Coach",
                "experience_years": 7,
                "specializations": ["Meditation Session", "Aromatherapy Session"],
                "certifications": ["Certified Wellness Coach", "Meditation Instructor"],
                "rating": 4.9,
                "availability_hours": 30
            }
        ]
        
        for staff in staff_members:
            query = """
            MERGE (st:Staff {id: $id})
            ON CREATE SET st.name = $name,
                         st.email = $email,
                         st.role = $role,
                         st.experience_years = $experience_years,
                         st.certifications = $certifications,
                         st.rating = $rating,
                         st.availability_hours = $availability_hours,
                         st.created_at = datetime()
            """
            await self.graph_db.execute_query(query, staff)
            
            # Create relationships to services they can perform
            for specialization in staff["specializations"]:
                service_query = """
                MATCH (st:Staff {id: $staff_id})
                MATCH (s:Service {name: $service_name})
                MERGE (st)-[:CAN_PERFORM]->(s)
                """
                await self.graph_db.execute_query(service_query, {
                    "staff_id": staff["id"],
                    "service_name": specialization
                })
            
            logger.info(f"Created staff member: {staff['name']}")
            
    async def create_sample_customers(self):
        """Create sample customer nodes with preferences."""
        customers = [
            {
                "id": "customer-001",
                "name": "Alice Johnson",
                "email": "alice.johnson@email.com",
                "phone": "+1234567890",
                "age_group": "30-40",
                "pressure_preference": "medium",
                "temperature_preference": "warm",
                "music_preference": "classical",
                "aromatherapy_preference": True,
                "visit_frequency": "monthly",
                "total_visits": 12,
                "favorite_services": ["Swedish Massage", "Signature Hydrating Facial"],
                "budget_range": "medium"
            },
            {
                "id": "customer-002",
                "name": "Bob Smith",
                "email": "bob.smith@email.com",
                "phone": "+1234567891",
                "age_group": "40-50",
                "pressure_preference": "firm",
                "temperature_preference": "hot",
                "music_preference": "nature_sounds",
                "aromatherapy_preference": False,
                "visit_frequency": "weekly",
                "total_visits": 24,
                "favorite_services": ["Deep Tissue Massage", "Hot Stone Massage"],
                "budget_range": "high"
            },
            {
                "id": "customer-003",
                "name": "Carol Davis",
                "email": "carol.davis@email.com",
                "phone": "+1234567892",
                "age_group": "25-35",
                "pressure_preference": "light",
                "temperature_preference": "cool",
                "music_preference": "ambient",
                "aromatherapy_preference": True,
                "visit_frequency": "bi-weekly",
                "total_visits": 18,
                "favorite_services": ["Aromatherapy Session", "Meditation Session"],
                "budget_range": "low"
            },
            {
                "id": "customer-004",
                "name": "David Wilson",
                "email": "david.wilson@email.com",
                "phone": "+1234567893",
                "age_group": "35-45",
                "pressure_preference": "medium",
                "temperature_preference": "warm",
                "music_preference": "jazz",
                "aromatherapy_preference": False,
                "visit_frequency": "monthly",
                "total_visits": 8,
                "favorite_services": ["Full Body Scrub", "Swedish Massage"],
                "budget_range": "medium"
            },
            {
                "id": "customer-005",
                "name": "Eva Martinez",
                "email": "eva.martinez@email.com",
                "phone": "+1234567894",
                "age_group": "45-55",
                "pressure_preference": "firm",
                "temperature_preference": "hot",
                "music_preference": "classical",
                "aromatherapy_preference": True,
                "visit_frequency": "bi-weekly",
                "total_visits": 15,
                "favorite_services": ["Anti-Aging Facial", "Detox Body Wrap"],
                "budget_range": "high"
            }
        ]
        
        for customer in customers:
            query = """
            MERGE (c:Customer {id: $id})
            ON CREATE SET c.name = $name,
                         c.email = $email,
                         c.phone = $phone,
                         c.age_group = $age_group,
                         c.pressure_preference = $pressure_preference,
                         c.temperature_preference = $temperature_preference,
                         c.music_preference = $music_preference,
                         c.aromatherapy_preference = $aromatherapy_preference,
                         c.visit_frequency = $visit_frequency,
                         c.total_visits = $total_visits,
                         c.budget_range = $budget_range,
                         c.created_at = datetime()
            """
            await self.graph_db.execute_query(query, customer)
            
            # Create relationships to favorite services
            for service_name in customer["favorite_services"]:
                service_query = """
                MATCH (c:Customer {id: $customer_id})
                MATCH (s:Service {name: $service_name})
                MERGE (c)-[:PREFERS]->(s)
                """
                await self.graph_db.execute_query(service_query, {
                    "customer_id": customer["id"],
                    "service_name": service_name
                })
            
            logger.info(f"Created customer: {customer['name']}")
            
    async def create_service_relationships(self):
        """Create relationships between services (complementary, alternative, etc.)."""
        relationships = [
            # Complementary services
            ("Swedish Massage", "Aromatherapy Session", "COMPLEMENTS", {"strength": 0.8}),
            ("Deep Tissue Massage", "Hot Stone Massage", "COMPLEMENTS", {"strength": 0.7}),
            ("Signature Hydrating Facial", "Full Body Scrub", "COMPLEMENTS", {"strength": 0.6}),
            ("Anti-Aging Facial", "Detox Body Wrap", "COMPLEMENTS", {"strength": 0.5}),
            ("Meditation Session", "Aromatherapy Session", "COMPLEMENTS", {"strength": 0.9}),
            
            # Alternative services (similar benefits)
            ("Swedish Massage", "Deep Tissue Massage", "ALTERNATIVE", {"strength": 0.6}),
            ("Signature Hydrating Facial", "Anti-Aging Facial", "ALTERNATIVE", {"strength": 0.7}),
            ("Full Body Scrub", "Detox Body Wrap", "ALTERNATIVE", {"strength": 0.5}),
            ("Aromatherapy Session", "Meditation Session", "ALTERNATIVE", {"strength": 0.8}),
            
            # Sequential services (good to do together)
            ("Full Body Scrub", "Swedish Massage", "SEQUENTIAL", {"strength": 0.8}),
            ("Detox Body Wrap", "Aromatherapy Session", "SEQUENTIAL", {"strength": 0.7}),
            ("Meditation Session", "Deep Tissue Massage", "SEQUENTIAL", {"strength": 0.6}),
        ]
        
        for service1, service2, relationship, properties in relationships:
            query = f"""
            MATCH (s1:Service {{name: $service1}})
            MATCH (s2:Service {{name: $service2}})
            MERGE (s1)-[r:{relationship}]->(s2)
            ON CREATE SET r += $properties
            """
            await self.graph_db.execute_query(query, {
                "service1": service1,
                "service2": service2,
                "properties": properties
            })
            
            logger.info(f"Created relationship: {service1} -{relationship}-> {service2}")
            
    async def create_sample_appointments(self):
        """Create sample appointment history."""
        appointments = [
            {
                "id": "appt-001",
                "customer_id": "customer-001",
                "service_name": "Swedish Massage",
                "staff_id": "staff-001",
                "date": "2024-01-15",
                "status": "completed",
                "rating": 5,
                "notes": "Very relaxing, customer loved it"
            },
            {
                "id": "appt-002",
                "customer_id": "customer-002",
                "service_name": "Deep Tissue Massage",
                "staff_id": "staff-001",
                "date": "2024-01-16",
                "status": "completed",
                "rating": 4,
                "notes": "Good pressure, helped with back pain"
            },
            {
                "id": "appt-003",
                "customer_id": "customer-003",
                "service_name": "Aromatherapy Session",
                "staff_id": "staff-002",
                "date": "2024-01-17",
                "status": "completed",
                "rating": 5,
                "notes": "Perfect for stress relief"
            },
            {
                "id": "appt-004",
                "customer_id": "customer-004",
                "service_name": "Full Body Scrub",
                "staff_id": "staff-004",
                "date": "2024-01-18",
                "status": "completed",
                "rating": 4,
                "notes": "Skin feels amazing"
            },
            {
                "id": "appt-005",
                "customer_id": "customer-005",
                "service_name": "Anti-Aging Facial",
                "staff_id": "staff-003",
                "date": "2024-01-19",
                "status": "completed",
                "rating": 5,
                "notes": "Noticeable improvement in skin texture"
            }
        ]
        
        for appointment in appointments:
            query = """
            MERGE (a:Appointment {id: $id})
            ON CREATE SET a.date = date($date),
                         a.status = $status,
                         a.rating = $rating,
                         a.notes = $notes,
                         a.created_at = datetime()
            """
            await self.graph_db.execute_query(query, appointment)
            
            # Create relationships
            customer_query = """
            MATCH (c:Customer {id: $customer_id})
            MATCH (a:Appointment {id: $appointment_id})
            MERGE (c)-[:BOOKED]->(a)
            """
            await self.graph_db.execute_query(customer_query, {
                "customer_id": appointment["customer_id"],
                "appointment_id": appointment["id"]
            })
            
            service_query = """
            MATCH (s:Service {name: $service_name})
            MATCH (a:Appointment {id: $appointment_id})
            MERGE (a)-[:FOR_SERVICE]->(s)
            """
            await self.graph_db.execute_query(service_query, {
                "service_name": appointment["service_name"],
                "appointment_id": appointment["id"]
            })
            
            staff_query = """
            MATCH (st:Staff {id: $staff_id})
            MATCH (a:Appointment {id: $appointment_id})
            MERGE (st)-[:PERFORMED]->(a)
            """
            await self.graph_db.execute_query(staff_query, {
                "staff_id": appointment["staff_id"],
                "appointment_id": appointment["id"]
            })
            
            logger.info(f"Created appointment: {appointment['id']}")
            
    async def create_indexes(self):
        """Create indexes for better query performance."""
        indexes = [
            "CREATE INDEX service_name_idx IF NOT EXISTS FOR (s:Service) ON (s.name)",
            "CREATE INDEX service_id_idx IF NOT EXISTS FOR (s:Service) ON (s.id)",
            "CREATE INDEX customer_id_idx IF NOT EXISTS FOR (c:Customer) ON (c.id)",
            "CREATE INDEX customer_email_idx IF NOT EXISTS FOR (c:Customer) ON (c.email)",
            "CREATE INDEX staff_id_idx IF NOT EXISTS FOR (st:Staff) ON (st.id)",
            "CREATE INDEX staff_name_idx IF NOT EXISTS FOR (st:Staff) ON (st.name)",
            "CREATE INDEX appointment_id_idx IF NOT EXISTS FOR (a:Appointment) ON (a.id)",
            "CREATE INDEX appointment_date_idx IF NOT EXISTS FOR (a:Appointment) ON (a.date)",
            "CREATE INDEX category_name_idx IF NOT EXISTS FOR (sc:ServiceCategory) ON (sc.name)"
        ]
        
        for index in indexes:
            await self.graph_db.execute_query(index)
            logger.info(f"Created index: {index}")
            
    async def verify_population(self):
        """Verify that the data was populated correctly."""
        queries = [
            ("Services", "MATCH (s:Service) RETURN count(s) as count"),
            ("Staff", "MATCH (st:Staff) RETURN count(st) as count"),
            ("Customers", "MATCH (c:Customer) RETURN count(c) as count"),
            ("Appointments", "MATCH (a:Appointment) RETURN count(a) as count"),
            ("Service Categories", "MATCH (sc:ServiceCategory) RETURN count(sc) as count"),
            ("Service Relationships", "MATCH (s1:Service)-[r]->(s2:Service) RETURN count(r) as count"),
            ("Customer Preferences", "MATCH (c:Customer)-[:PREFERS]->(s:Service) RETURN count(*) as count"),
            ("Staff Specializations", "MATCH (st:Staff)-[:CAN_PERFORM]->(s:Service) RETURN count(*) as count")
        ]
        
        verification_results = {}
        for name, query in queries:
            result = await self.graph_db.execute_query(query)
            count = result[0]["count"] if result else 0
            verification_results[name] = count
            logger.info(f"{name}: {count}")
            
        return verification_results
        
    async def test_recommendation_queries(self):
        """Test some recommendation queries."""
        queries = [
            {
                "name": "Services similar to Swedish Massage",
                "query": """
                MATCH (s:Service {name: 'Swedish Massage'})-[:ALTERNATIVE|COMPLEMENTS]-(similar:Service)
                RETURN similar.name as service, similar.price as price
                ORDER BY similar.popularity DESC
                """
            },
            {
                "name": "Staff who can perform Deep Tissue Massage",
                "query": """
                MATCH (st:Staff)-[:CAN_PERFORM]->(s:Service {name: 'Deep Tissue Massage'})
                RETURN st.name as staff, st.rating as rating, st.experience_years as experience
                ORDER BY st.rating DESC
                """
            },
            {
                "name": "Customers who prefer relaxation services",
                "query": """
                MATCH (c:Customer)-[:PREFERS]->(s:Service)-[:BELONGS_TO]->(sc:ServiceCategory)
                WHERE sc.name IN ['Massage Therapy', 'Wellness Treatments']
                RETURN c.name as customer, collect(s.name) as preferred_services
                """
            },
            {
                "name": "Most popular service combinations",
                "query": """
                MATCH (s1:Service)-[r:COMPLEMENTS]->(s2:Service)
                RETURN s1.name as service1, s2.name as service2, r.strength as strength
                ORDER BY r.strength DESC
                """
            }
        ]
        
        test_results = {}
        for test in queries:
            result = await self.graph_db.execute_query(test["query"])
            test_results[test["name"]] = result[:3]  # Top 3 results
            logger.info(f"Test query '{test['name']}': {len(result)} results")
            
        return test_results

async def main():
    """Main function to populate Neo4j graph database."""
    populator = SpaGraphPopulator()
    
    try:
        # Connect to database
        await populator.connect()
        
        # Clear existing data (development only)
        logger.info("Clearing existing data...")
        await populator.clear_database()
        
        # Create nodes and relationships
        logger.info("Creating service categories...")
        await populator.create_service_categories()
        
        logger.info("Creating services...")
        await populator.create_services()
        
        logger.info("Creating staff members...")
        await populator.create_staff_members()
        
        logger.info("Creating sample customers...")
        await populator.create_sample_customers()
        
        logger.info("Creating service relationships...")
        await populator.create_service_relationships()
        
        logger.info("Creating sample appointments...")
        await populator.create_sample_appointments()
        
        logger.info("Creating indexes...")
        await populator.create_indexes()
        
        # Verify population
        logger.info("Verifying population...")
        verification = await populator.verify_population()
        
        # Test queries
        logger.info("Testing recommendation queries...")
        test_results = await populator.test_recommendation_queries()
        
        # Print results
        print("\n" + "="*50)
        print("✅ NEO4J POPULATION SUMMARY")
        print("="*50)
        
        print("\n📊 Node and Relationship Counts:")
        for item, count in verification.items():
            print(f"  {item}: {count}")
        
        print("\n🔍 Sample Query Results:")
        for query_name, results in test_results.items():
            print(f"\n  {query_name}:")
            for result in results[:2]:  # Show top 2 results
                print(f"    {result}")
        
        print("\n🎉 Neo4j graph database populated successfully!")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error populating Neo4j database: {e}")
        raise
    finally:
        await populator.close()

if __name__ == "__main__":
    asyncio.run(main())