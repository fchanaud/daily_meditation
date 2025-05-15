"""
Simple test script to verify Supabase connection.
Run this with: python test_supabase.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Print the Python version
print(f"Python version: {sys.version}")

# Check for environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(f"Supabase URL found: {'Yes' if supabase_url else 'No'}")
print(f"Supabase Key found: {'Yes' if supabase_key else 'No'}")

# Try to import and initialize Supabase
try:
    from supabase import create_client, Client
    
    print("Successfully imported Supabase package")
    
    # Try different potential package formats
    try:
        client = create_client(supabase_url, supabase_key)
        print("Successfully created Supabase client with direct call")
    except Exception as e1:
        print(f"Error with direct client creation: {e1}")
        
        try:
            # Try alternative import pattern
            import supabase
            print(f"Supabase version: {supabase.__version__ if hasattr(supabase, '__version__') else 'unknown'}")
            client = supabase.create_client(supabase_url, supabase_key)
            print("Successfully created Supabase client with package namespace")
        except Exception as e2:
            print(f"Error with namespace client creation: {e2}")
    
    # Try to query a table
    if 'client' in locals():
        try:
            # Try both query styles
            try:
                response = client.table("meditation_sessions").select("*").limit(1).execute()
                print(f"Successfully queried database using .table() method: {response}")
            except Exception as table_error:
                print(f"Table method error: {table_error}")
                
                try:
                    response = client.from_("meditation_sessions").select("*").limit(1).execute()
                    print(f"Successfully queried database using .from_() method: {response}")
                except Exception as from_error:
                    print(f"From method error: {from_error}")
        except Exception as query_error:
            print(f"Query error: {query_error}")
    
except ImportError as import_error:
    print(f"Failed to import Supabase package: {import_error}")
    
print("Supabase test completed") 