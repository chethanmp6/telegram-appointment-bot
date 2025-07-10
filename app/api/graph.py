"""Graph database API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging

from app.core.graph_db import get_graph_db, GraphDatabase
from app.models.schemas import GraphQuery, GraphResponse, GraphNode, GraphRelationship

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=GraphResponse)
async def execute_graph_query(
    query_request: GraphQuery,
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Execute a custom Cypher query."""
    try:
        results = await graph_db.execute_query(
            query_request.query, 
            query_request.parameters
        )
        
        return GraphResponse(data=results)
        
    except Exception as e:
        logger.error(f"Graph query execution failed: {e}")
        raise HTTPException(status_code=500, detail="Query execution failed")


@router.get("/customers/{customer_id}/preferences")
async def get_customer_preferences(
    customer_id: str,
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Get customer preferences and patterns."""
    try:
        preferences = await graph_db.get_customer_preferences(customer_id)
        return preferences
    except Exception as e:
        logger.error(f"Failed to get customer preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")


@router.get("/customers/{customer_id}/recommendations")
async def get_customer_recommendations(
    customer_id: str,
    limit: int = Query(5, ge=1, le=20),
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Get service recommendations for a customer."""
    try:
        recommendations = await graph_db.get_service_recommendations(customer_id, limit)
        return {"customer_id": customer_id, "recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/services/{service_id}/staff")
async def get_staff_recommendations(
    service_id: str,
    customer_id: Optional[str] = Query(None),
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Get staff recommendations for a service."""
    try:
        staff_recs = await graph_db.get_staff_recommendations(service_id, customer_id)
        return {
            "service_id": service_id,
            "customer_id": customer_id,
            "staff_recommendations": staff_recs
        }
    except Exception as e:
        logger.error(f"Failed to get staff recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get staff recommendations")


@router.post("/customers/{customer_id}/preferences")
async def update_customer_preferences(
    customer_id: str,
    service_id: str,
    satisfaction: float = Query(1.0, ge=0, le=1),
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Update customer preferences based on interaction."""
    try:
        result = await graph_db.update_customer_preferences(
            customer_id, service_id, satisfaction
        )
        return {"status": "updated", "result": result}
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.post("/services/relationships")
async def create_service_relationships(
    services_data: List[Dict[str, Any]],
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Create service nodes and relationships."""
    try:
        await graph_db.create_service_relationships(services_data)
        return {"status": "created", "services_count": len(services_data)}
    except Exception as e:
        logger.error(f"Failed to create service relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to create relationships")


@router.post("/services/{service_id}/complements")
async def create_service_complements(
    service_id: str,
    complement_ids: List[str],
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Create complement relationships between services."""
    try:
        await graph_db.create_service_complements(service_id, complement_ids)
        return {
            "status": "created",
            "service_id": service_id,
            "complements": complement_ids
        }
    except Exception as e:
        logger.error(f"Failed to create complements: {e}")
        raise HTTPException(status_code=500, detail="Failed to create complements")


@router.post("/appointments")
async def create_appointment_graph(
    appointment_data: Dict[str, Any],
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Create appointment node and relationships in graph."""
    try:
        result = await graph_db.create_appointment_node(appointment_data)
        return {"status": "created", "appointment": result}
    except Exception as e:
        logger.error(f"Failed to create appointment graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")


@router.post("/appointments/{appointment_id}/feedback")
async def update_appointment_feedback(
    appointment_id: str,
    customer_id: str,
    staff_id: str,
    satisfaction: float = Query(..., ge=0, le=1),
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Update appointment feedback and relationships."""
    try:
        result = await graph_db.update_appointment_feedback(
            appointment_id, customer_id, staff_id, satisfaction
        )
        return {"status": "updated", "result": result}
    except Exception as e:
        logger.error(f"Failed to update feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to update feedback")


@router.post("/knowledge")
async def create_knowledge_graph(
    knowledge_data: List[Dict[str, Any]],
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Create knowledge graph from business information."""
    try:
        await graph_db.create_knowledge_graph(knowledge_data)
        return {"status": "created", "concepts_count": len(knowledge_data)}
    except Exception as e:
        logger.error(f"Failed to create knowledge graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to create knowledge graph")


@router.get("/knowledge/search")
async def search_knowledge_graph(
    query: str,
    context: Optional[str] = Query(None),
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Search knowledge graph for relevant concepts."""
    try:
        context_dict = {"context": context} if context else None
        results = await graph_db.search_knowledge_graph(query, context_dict)
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"Knowledge graph search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/analytics/customer/{customer_id}")
async def get_customer_analytics(
    customer_id: str,
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Get comprehensive customer analytics from graph."""
    try:
        analytics = await graph_db.get_customer_analytics(customer_id)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get customer analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/analytics/business")
async def get_business_insights(
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Get overall business insights from graph analysis."""
    try:
        insights = await graph_db.get_business_insights()
        return insights
    except Exception as e:
        logger.error(f"Failed to get business insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get insights")


@router.get("/schema")
async def get_graph_schema(
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Get graph database schema information."""
    try:
        # Get node labels and relationship types
        schema_query = """
        CALL db.labels() YIELD label
        WITH collect(label) as labels
        CALL db.relationshipTypes() YIELD relationshipType
        WITH labels, collect(relationshipType) as relationships
        RETURN labels, relationships
        """
        
        result = await graph_db.execute_query(schema_query)
        
        if result:
            return {
                "node_labels": result[0].get("labels", []),
                "relationship_types": result[0].get("relationships", [])
            }
        else:
            return {"node_labels": [], "relationship_types": []}
            
    except Exception as e:
        logger.error(f"Failed to get schema: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schema")


@router.get("/statistics")
async def get_graph_statistics(
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Get graph database statistics."""
    try:
        stats_query = """
        MATCH (n)
        WITH labels(n) as labels
        UNWIND labels as label
        WITH label, count(*) as count
        RETURN label, count
        ORDER BY count DESC
        """
        
        node_counts = await graph_db.execute_query(stats_query)
        
        # Get relationship counts
        rel_query = """
        MATCH ()-[r]->()
        WITH type(r) as relType
        RETURN relType, count(*) as count
        ORDER BY count DESC
        """
        
        rel_counts = await graph_db.execute_query(rel_query)
        
        # Get total counts
        total_query = """
        MATCH (n)
        WITH count(n) as nodeCount
        MATCH ()-[r]->()
        RETURN nodeCount, count(r) as relCount
        """
        
        totals = await graph_db.execute_query(total_query)
        
        return {
            "total_nodes": totals[0]["nodeCount"] if totals else 0,
            "total_relationships": totals[0]["relCount"] if totals else 0,
            "node_counts": {item["label"]: item["count"] for item in node_counts},
            "relationship_counts": {item["relType"]: item["count"] for item in rel_counts}
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.post("/schema/initialize")
async def initialize_graph_schema(
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Initialize graph database schema."""
    try:
        await graph_db.create_schema()
        return {"status": "schema_initialized"}
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize schema")


@router.get("/health")
async def graph_health_check(
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Check graph database health."""
    try:
        is_healthy = await graph_db.health_check()
        
        # Get basic connectivity info
        version_query = "CALL dbms.components() YIELD versions RETURN versions"
        try:
            version_result = await graph_db.execute_query(version_query)
            version_info = version_result[0] if version_result else {}
        except Exception:
            version_info = {}
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "connected": is_healthy,
            "version_info": version_info
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


@router.delete("/data")
async def clear_graph_data(
    confirm: bool = Query(False, description="Confirmation required"),
    graph_db: GraphDatabase = Depends(get_graph_db)
):
    """Clear all data from graph database (dangerous operation)."""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Confirmation required. Add ?confirm=true to clear all data."
        )
    
    try:
        # Delete all relationships first
        await graph_db.execute_write_query("MATCH ()-[r]->() DELETE r")
        
        # Then delete all nodes
        await graph_db.execute_write_query("MATCH (n) DELETE n")
        
        return {"status": "data_cleared", "warning": "All graph data has been deleted"}
        
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear data")