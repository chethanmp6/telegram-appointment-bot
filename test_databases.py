#!/usr/bin/env python3
"""
Test script to verify both ChromaDB and Neo4j databases are populated correctly.
"""

import asyncio
import chromadb
from app.core.graph_db import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chromadb():
    """Test ChromaDB spa knowledge base."""
    print("\n" + "="*50)
    print("🔍 TESTING CHROMADB")
    print("="*50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host='localhost', port=8001)
        
        # Get collection
        collection = client.get_collection("spa_knowledge_base")
        
        # Test queries
        test_queries = [
            "Swedish massage benefits",
            "facial treatments",
            "booking policy",
            "wellness packages",
            "aromatherapy"
        ]
        
        for query in test_queries:
            results = collection.query(query_texts=[query], n_results=2)
            print(f"\n🔍 Query: '{query}'")
            print(f"   Results: {len(results['documents'][0])}")
            
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                print(f"   {i+1}. {metadata['type'].upper()}: {metadata['title']}")
                print(f"      Preview: {doc[:80]}...")
                
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")

async def test_neo4j():
    """Test Neo4j graph database."""
    print("\n" + "="*50)
    print("🕸️  TESTING NEO4J")
    print("="*50)
    
    try:
        # Connect to Neo4j
        graph_db = GraphDatabase()
        await graph_db.connect()
        
        # Test queries
        test_queries = [
            {
                "name": "Service Recommendations",
                "query": """
                MATCH (s:Service {name: 'Swedish Massage'})-[:COMPLEMENTS|ALTERNATIVE]-(rec:Service)
                RETURN rec.name as service, rec.price as price, rec.duration as duration
                ORDER BY rec.popularity DESC
                LIMIT 3
                """
            },
            {
                "name": "Staff Expertise",
                "query": """
                MATCH (st:Staff)-[:CAN_PERFORM]->(s:Service)
                RETURN st.name as staff, st.rating as rating, collect(s.name) as services
                ORDER BY st.rating DESC
                LIMIT 3
                """
            },
            {
                "name": "Customer Preferences",
                "query": """
                MATCH (c:Customer)-[:PREFERS]->(s:Service)
                RETURN c.name as customer, c.pressure_preference as pressure, 
                       collect(s.name) as preferred_services
                LIMIT 3
                """
            },
            {
                "name": "Popular Service Combinations",
                "query": """
                MATCH (s1:Service)-[r:COMPLEMENTS]->(s2:Service)
                RETURN s1.name as service1, s2.name as service2, r.strength as strength
                ORDER BY r.strength DESC
                LIMIT 3
                """
            }
        ]
        
        for test in test_queries:
            results = await graph_db.execute_query(test["query"])
            print(f"\n🔍 Query: {test['name']}")
            print(f"   Results: {len(results)}")
            
            for i, result in enumerate(results[:2]):  # Show top 2
                print(f"   {i+1}. {dict(result)}")
                
        await graph_db.close()
        
    except Exception as e:
        print(f"❌ Neo4j test failed: {e}")

async def test_integration():
    """Test integration between databases."""
    print("\n" + "="*50)
    print("🔗 TESTING INTEGRATION")
    print("="*50)
    
    try:
        # Test ChromaDB search for service info
        client = chromadb.HttpClient(host='localhost', port=8001)
        collection = client.get_collection("spa_knowledge_base")
        
        # Search for Swedish massage in ChromaDB
        chroma_results = collection.query(
            query_texts=["Swedish massage"], 
            n_results=1
        )
        
        print("📚 ChromaDB Knowledge:")
        if chroma_results['documents'][0]:
            doc = chroma_results['documents'][0][0]
            metadata = chroma_results['metadatas'][0][0]
            print(f"   Found: {metadata['title']}")
            print(f"   Type: {metadata['type']}")
            print(f"   Preview: {doc[:100]}...")
        
        # Search for Swedish massage in Neo4j
        graph_db = GraphDatabase()
        await graph_db.connect()
        
        neo4j_results = await graph_db.execute_query("""
        MATCH (s:Service {name: 'Swedish Massage'})
        OPTIONAL MATCH (s)-[:COMPLEMENTS]-(comp:Service)
        RETURN s.name as service, s.price as price, s.duration as duration,
               collect(comp.name) as complementary_services
        """)
        
        print("\n🕸️  Neo4j Relationships:")
        if neo4j_results:
            result = neo4j_results[0]
            print(f"   Service: {result['service']}")
            print(f"   Price: ${result['price']}")
            print(f"   Duration: {result['duration']} minutes")
            print(f"   Complements: {result['complementary_services']}")
            
        await graph_db.close()
        
        print("\n✅ Integration test shows both databases working together!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

async def main():
    """Run all database tests."""
    print("🧪 TESTING SPA APPOINTMENT MANAGER DATABASES")
    print("="*60)
    
    await test_chromadb()
    await test_neo4j()
    await test_integration()
    
    print("\n" + "="*60)
    print("✅ DATABASE TESTING COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())