#!/usr/bin/env python3
"""
Test script for AI Agent functionality
"""
import os
import sys
from database import SessionLocal
from controllers.ai_agent import (
    extract_search_intent, 
    search_lodgings, 
    search_restaurants,
    search_experiences,
    search_producers,
    search_products,
    search_companies
)

def test_intent_detection():
    """Test intent detection"""
    print("\n=== Testing Intent Detection ===")
    test_messages = [
        "Quais alojamentos há em Inhassoro?",
        "Onde posso comer em Sofala?",
        "Quais tours posso fazer?",
        "Onde compro produtos locais?",
        "Quais empresas há em Niassa?",
        "Oi, como vai?",
    ]
    
    for msg in test_messages:
        intent, params = extract_search_intent(msg)
        print(f"Message: {msg}")
        print(f"  Intent: {intent} | Params: {params}\n")

def test_database_queries():
    """Test database queries"""
    print("\n=== Testing Database Queries ===")
    db = SessionLocal()
    
    try:
        # Test each search function
        print("\n1. Testing search_lodgings...")
        lodgings = search_lodgings(db, query="", limit=5)
        print(f"   Found {len(lodgings)} lodgings")
        if lodgings:
            print(f"   Example: {lodgings[0]['name']}")
        
        print("\n2. Testing search_restaurants...")
        restaurants = search_restaurants(db, query="", limit=5)
        print(f"   Found {len(restaurants)} restaurants")
        if restaurants:
            print(f"   Example: {restaurants[0]['name']}")
        
        print("\n3. Testing search_experiences...")
        experiences = search_experiences(db, query="", limit=5)
        print(f"   Found {len(experiences)} experiences")
        if experiences:
            print(f"   Example: {experiences[0]['name']}")
        
        print("\n4. Testing search_producers...")
        producers = search_producers(db, query="", limit=5)
        print(f"   Found {len(producers)} producers")
        if producers:
            print(f"   Example: {producers[0]['name']}")
        
        print("\n5. Testing search_products...")
        products = search_products(db, query="", limit=5)
        print(f"   Found {len(products)} products")
        if products:
            print(f"   Example: {products[0]['name']}")
        
        print("\n6. Testing search_companies...")
        companies = search_companies(db, query="", limit=5)
        print(f"   Found {len(companies)} companies")
        if companies:
            print(f"   Example: {companies[0]['name']}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_intent_detection()
    test_database_queries()
    print("\n=== Tests Complete ===")
