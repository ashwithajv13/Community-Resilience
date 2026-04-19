#!/usr/bin/env python
"""Test Community Platform APIs"""
import urllib.request
import json
import time

BASE = "http://localhost:5000/api/community"

def api_call(method, path, data=None):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    
    if data:
        req.data = json.dumps(data).encode()
    
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("=" * 50)
print("Community Platform API Test")
print("=" * 50)

# Test 1: Create group
print("\n1. Creating community group...")
result = api_call("POST", "/groups", {
    "name": "Downtown Resilience Network",
    "location": "Downtown Ward 5",
    "description": "Building disaster preparedness",
    "leader_id": "alice_001"
})
print(f"   {result}")

# Test 2: Get groups
print("\n2. Getting all groups...")
result = api_call("GET", "/groups")
print(f"   Found {result.get('count', 0)} groups")

# Test 3: Post knowledge tip
print("\n3. Posting knowledge tip...")
result = api_call("POST", "/knowledge", {
    "group_id": 1,
    "user_id": "bob_001",
    "category": "earthquake",
    "title": "Drop, Cover, Hold!",
    "content": "During earthquake: Drop to hands and knees. Cover head and neck. Hold on to something sturdy."
})
print(f"   {result}")

# Test 4: Register resource
print("\n4. Registering resource...")
result = api_call("POST", "/resources", {
    "group_id": 1,
    "user_id": "carol_001",
    "resource_type": "shelter",
    "description": "Community Center shelter for 50 people",
    "quantity": 50,
    "location": "123 Main St"
})
print(f"   {result}")

# Test 5: Get resources
print("\n5. Getting available resources...")
result = api_call("GET", "/resources")
print(f"   Found {len(result.get('resources', []))} resources")

# Test 6: Schedule training
print("\n6. Scheduling training...")
result = api_call("POST", "/training", {
    "group_id": 1,
    "organizer_id": "alice_001",
    "title": "First Aid Workshop",
    "category": "first_aid",
    "description": "Learn basic first aid and CPR",
    "scheduled_date": "2026-05-15"
})
print(f"   {result}")

# Test 7: Post recovery request
print("\n7. Posting recovery request...")
result = api_call("POST", "/recovery", {
    "group_id": 1,
    "user_id": "david_001",
    "category": "mental_health",
    "description": "Seeking mental health support",
    "priority": "high"
})
print(f"   {result}")

# Test 8: Get activity
print("\n8. Getting community activity...")
result = api_call("GET", "/activity")
activities = result.get('activity', [])
print(f"   Activity log has {len(activities)} entries")
for activity in activities[:5]:
    print(f"      - {activity['activity_type']}: {activity['details']}")

print("\n✅ All API tests completed!")
print("=" * 50)
