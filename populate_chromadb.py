#!/usr/bin/env python3
"""
Script to populate ChromaDB with spa knowledge base data.
This script loads spa-related information into ChromaDB for RAG (Retrieval-Augmented Generation) functionality.
"""

import json
import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any
import uuid
from datetime import datetime
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpaKnowledgeBasePopulator:
    """Populate ChromaDB with spa knowledge base data."""
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        """Initialize the ChromaDB client."""
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection_name = "spa_knowledge_base"
        self.collection = None
        
    def setup_collection(self):
        """Create or get the ChromaDB collection."""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(self.collection_name)
            logger.info(f"Found existing collection: {self.collection_name}")
        except Exception:
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Spa services, treatments, policies, and FAQ knowledge base"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def load_spa_data(self, file_path: str) -> Dict[str, Any]:
        """Load spa data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded spa data from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading spa data: {e}")
            raise
    
    def prepare_documents(self, spa_data: Dict[str, Any]) -> tuple:
        """Prepare documents, metadata, and IDs for ChromaDB."""
        documents = []
        metadatas = []
        ids = []
        
        # Process spa services
        for service in spa_data.get("spa_services", []):
            doc_text = self._format_service_document(service)
            documents.append(doc_text)
            metadatas.append({
                "category": service.get("category", "Unknown"),
                "type": "service",
                "title": service.get("title", ""),
                "duration": service.get("duration", ""),
                "price": service.get("price", ""),
                "source": "spa_services"
            })
            ids.append(service.get("id", str(uuid.uuid4())))
        
        # Process spa policies
        for policy in spa_data.get("spa_policies", []):
            doc_text = self._format_policy_document(policy)
            documents.append(doc_text)
            metadatas.append({
                "category": policy.get("category", "Unknown"),
                "type": "policy",
                "title": policy.get("title", ""),
                "source": "spa_policies"
            })
            ids.append(policy.get("id", str(uuid.uuid4())))
        
        # Process spa facilities
        for facility in spa_data.get("spa_facilities", []):
            doc_text = self._format_facility_document(facility)
            documents.append(doc_text)
            metadatas.append({
                "category": facility.get("category", "Unknown"),
                "type": "facility",
                "title": facility.get("title", ""),
                "source": "spa_facilities"
            })
            ids.append(facility.get("id", str(uuid.uuid4())))
        
        # Process spa packages
        for package in spa_data.get("spa_packages", []):
            doc_text = self._format_package_document(package)
            documents.append(doc_text)
            metadatas.append({
                "category": package.get("category", "Unknown"),
                "type": "package",
                "title": package.get("title", ""),
                "duration": package.get("duration", ""),
                "price": package.get("price", ""),
                "source": "spa_packages"
            })
            ids.append(package.get("id", str(uuid.uuid4())))
        
        # Process FAQs
        for faq in spa_data.get("frequently_asked_questions", []):
            doc_text = self._format_faq_document(faq)
            documents.append(doc_text)
            metadatas.append({
                "category": faq.get("category", "Unknown"),
                "type": "faq",
                "question": faq.get("question", ""),
                "source": "frequently_asked_questions"
            })
            ids.append(faq.get("id", str(uuid.uuid4())))
        
        # Process tips and advice
        for tip in spa_data.get("spa_tips_and_advice", []):
            doc_text = self._format_tip_document(tip)
            documents.append(doc_text)
            metadatas.append({
                "category": tip.get("category", "Unknown"),
                "type": "tip",
                "title": tip.get("title", ""),
                "source": "spa_tips_and_advice"
            })
            ids.append(tip.get("id", str(uuid.uuid4())))
        
        return documents, metadatas, ids
    
    def _format_service_document(self, service: Dict[str, Any]) -> str:
        """Format service data into a searchable document."""
        doc_parts = [
            f"Service: {service.get('title', '')}",
            f"Category: {service.get('category', '')}",
            f"Description: {service.get('description', '')}",
            f"Duration: {service.get('duration', '')}",
            f"Price: {service.get('price', '')}",
        ]
        
        if service.get('benefits'):
            doc_parts.append(f"Benefits: {', '.join(service['benefits'])}")
        
        if service.get('preparation'):
            doc_parts.append(f"Preparation: {service['preparation']}")
        
        if service.get('contraindications'):
            doc_parts.append(f"Contraindications: {', '.join(service['contraindications'])}")
        
        return "\n".join(doc_parts)
    
    def _format_policy_document(self, policy: Dict[str, Any]) -> str:
        """Format policy data into a searchable document."""
        return f"Policy: {policy.get('title', '')}\nCategory: {policy.get('category', '')}\nContent: {policy.get('content', '')}"
    
    def _format_facility_document(self, facility: Dict[str, Any]) -> str:
        """Format facility data into a searchable document."""
        return f"Facility: {facility.get('title', '')}\nCategory: {facility.get('category', '')}\nDescription: {facility.get('description', '')}"
    
    def _format_package_document(self, package: Dict[str, Any]) -> str:
        """Format package data into a searchable document."""
        doc_parts = [
            f"Package: {package.get('title', '')}",
            f"Category: {package.get('category', '')}",
            f"Description: {package.get('description', '')}",
            f"Duration: {package.get('duration', '')}",
            f"Price: {package.get('price', '')}",
        ]
        
        if package.get('includes'):
            doc_parts.append(f"Includes: {', '.join(package['includes'])}")
        
        return "\n".join(doc_parts)
    
    def _format_faq_document(self, faq: Dict[str, Any]) -> str:
        """Format FAQ data into a searchable document."""
        return f"FAQ: {faq.get('question', '')}\nCategory: {faq.get('category', '')}\nAnswer: {faq.get('answer', '')}"
    
    def _format_tip_document(self, tip: Dict[str, Any]) -> str:
        """Format tip data into a searchable document."""
        return f"Tip: {tip.get('title', '')}\nCategory: {tip.get('category', '')}\nContent: {tip.get('content', '')}"
    
    def populate_collection(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """Populate the ChromaDB collection with documents."""
        try:
            # Add documents in batches to avoid memory issues
            batch_size = 100
            total_docs = len(documents)
            
            for i in range(0, total_docs, batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metadata = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metadata,
                    ids=batch_ids
                )
                
                logger.info(f"Added batch {i//batch_size + 1}: {len(batch_docs)} documents")
            
            logger.info(f"Successfully populated collection with {total_docs} documents")
            
        except Exception as e:
            logger.error(f"Error populating collection: {e}")
            raise
    
    def verify_population(self) -> Dict[str, Any]:
        """Verify that the data was populated correctly."""
        try:
            # Get collection info
            collection_info = self.collection.get()
            total_count = len(collection_info['ids'])
            
            # Count by type
            type_counts = {}
            for metadata in collection_info['metadatas']:
                doc_type = metadata.get('type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Count by category
            category_counts = {}
            for metadata in collection_info['metadatas']:
                category = metadata.get('category', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            verification_result = {
                'total_documents': total_count,
                'types': type_counts,
                'categories': category_counts,
                'sample_ids': collection_info['ids'][:5]  # First 5 IDs
            }
            
            logger.info(f"Verification complete: {verification_result}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            raise
    
    def test_search(self, query: str = "massage therapy", n_results: int = 3) -> Dict[str, Any]:
        """Test search functionality."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            logger.info(f"Search test for '{query}' returned {len(results['documents'][0])} results")
            
            return {
                'query': query,
                'results_count': len(results['documents'][0]),
                'results': [
                    {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i][:200] + "..." if len(results['documents'][0][i]) > 200 else results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    }
                    for i in range(len(results['documents'][0]))
                ]
            }
            
        except Exception as e:
            logger.error(f"Error during search test: {e}")
            raise

def main():
    """Main function to populate ChromaDB with spa data."""
    try:
        # Initialize populator
        populator = SpaKnowledgeBasePopulator()
        
        # Setup collection
        populator.setup_collection()
        
        # Load spa data
        spa_data = populator.load_spa_data("spa_knowledge_base.json")
        
        # Prepare documents
        documents, metadatas, ids = populator.prepare_documents(spa_data)
        
        # Populate collection
        populator.populate_collection(documents, metadatas, ids)
        
        # Verify population
        verification = populator.verify_population()
        print(f"\n✅ Population Summary:")
        print(f"Total documents: {verification['total_documents']}")
        print(f"Document types: {verification['types']}")
        print(f"Categories: {verification['categories']}")
        
        # Test search
        search_test = populator.test_search("Swedish massage")
        print(f"\n🔍 Search Test Results:")
        print(f"Query: '{search_test['query']}'")
        print(f"Results found: {search_test['results_count']}")
        
        for i, result in enumerate(search_test['results']):
            print(f"\nResult {i+1}:")
            print(f"  ID: {result['id']}")
            print(f"  Type: {result['metadata']['type']}")
            print(f"  Category: {result['metadata']['category']}")
            print(f"  Preview: {result['document'][:100]}...")
        
        print(f"\n🎉 ChromaDB population completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to populate ChromaDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()