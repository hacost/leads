import unittest
import os
import sqlite3
import pandas as pd
from scraper import GoogleMapsScraper

class TestScraperSystem(unittest.TestCase):
    
    def setUp(self):
        # Clean environment
        self.files = ["leads.db", "leads_google_maps.xlsx", "leads_pending_lookup.xlsx", "leads_micro.xlsx", "leads_corporate.xlsx"]
        for f in self.files:
            if os.path.exists(f):
                os.remove(f)
        
        self.scraper = GoogleMapsScraper()

    def test_01_segmentation_logic(self):
        print("\n[TEST] Verifying Segmentation & Export...")
        
        # Mock Data Injection (Simulating extracted results)
        self.scraper.results = [
            # 1. Micro Lead (High Stars, Low Reviews, No Chain)
            {
                "name": "Tacos Don Pepe",
                "phone": "555-001",
                "stars": 4.8,
                "reviews": 15, # <= 20
                "zone": "Test",
                "source": "Map"
            },
            # 2. Corporate Lead (Chain Name)
            {
                "name": "OXXO Centro",
                "phone": "555-002",
                "stars": 3.5,
                "reviews": 10,
                "zone": "Test",
                "source": "Map"
            },
             # 3. Corporate Lead (High Reviews > 20)
            {
                "name": "Super Mercado Gigante",
                "phone": "555-003",
                "stars": 4.2,
                "reviews": 25, # > 20
                "zone": "Test",
                "source": "Map"
            },
            # 4. Pending Lead (No Phone) - Should NOT be in Micro/Corp/Master
            {
                "name": "Mystery Shop",
                "phone": "N/A", # No phone
                "stars": 5.0,
                "reviews": 5,
                "zone": "Test",
                "source": "Map"
            }
        ]
        
        # Run Save Logic
        self.scraper.save_data()
        
        # --- VERIFY MICRO ---
        self.assertTrue(os.path.exists("leads_micro.xlsx"), "Micro file not created")
        df_micro = pd.read_excel("leads_micro.xlsx")
        self.assertIn("Tacos Don Pepe", df_micro['name'].values, "Micro lead missing from Micro file")
        self.assertNotIn("OXXO Centro", df_micro['name'].values, "Chain OXXO found in Micro file")
        self.assertNotIn("Mystery Shop", df_micro['name'].values, "Pending lead (No Phone) found in Micro file!")
        
        # --- VERIFY CORPORATE ---
        self.assertTrue(os.path.exists("leads_corporate.xlsx"), "Corporate file not created")
        df_corp = pd.read_excel("leads_corporate.xlsx")
        self.assertIn("OXXO Centro", df_corp['name'].values, "Chain OXXO missing from Corp file")
        self.assertIn("Super Mercado Gigante", df_corp['name'].values, "High review lead missing from Corp file")
        self.assertNotIn("Mystery Shop", df_corp['name'].values, "Pending lead (No Phone) found in Corp file!")
        
        # --- VERIFY PENDING ---
        self.assertTrue(os.path.exists("leads_pending_lookup.xlsx"), "Pending file not created")
        df_pending = pd.read_excel("leads_pending_lookup.xlsx", keep_default_na=False)
        self.assertIn("Mystery Shop", df_pending['name'].values, "Pending lead missing")
        # Ensure it has N/A populated (Fixed defect)
        row = df_pending[df_pending['name'] == "Mystery Shop"].iloc[0]
        self.assertEqual(row['email'], "N/A", "Email should be N/A for pending lead")

    def test_02_column_structure(self):
        print("\n[TEST] Verifying Excel Columns...")
        # Create dummy data and save
        self.scraper.results = [{"name": "A", "phone": "1", "zone": "Z"}]
        self.scraper.save_data()
        
        df = pd.read_excel("leads_google_maps.xlsx")
        columns = list(df.columns)
        expected_start = ['source', 'name', 'phone', 'email', 'address', 'website', 'map_url', 'zone', 'stars', 'reviews']
        
        # Check if expected columns are present and in order (ignoring extra pandas cols if any)
        self.assertEqual(columns[:10], expected_start, f"Column order mismatch.\nExpected: {expected_start}\nGot: {columns[:10]}")

    def test_03_database_integrity(self):
        print("\n[TEST] Verifying Database Integrity...")
        
        lead = {
            "name": "Unique Business",
            "zone": "Zone A",
            "phone": "123",
            "stars": 5.0,
            "reviews": 10
        }
        
        # Insert Twice
        self.scraper.results = [lead]
        self.scraper.save_to_db() # 1st Insert
        
        self.scraper.results = [lead] 
        self.scraper.save_to_db() # 2nd Insert (Duplicate)
        
        # Check Count
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute("SELECT count(*) FROM leads WHERE name='Unique Business'")
        count = c.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1, f"Database has {count} records for same business. Constraints failed!")

    def test_04_default_values(self):
        print("\n[TEST] Verifying Default Values (N/A)...")
        # Simulating a lead where extraction failed or data was missing
        # The scraper logic fills defaults usually during extraction, 
        # but save_data ALSO has a safety net. We test the safety net here.
        incomplete_lead = {
            "name": "Ghost Shop",
            "zone": "Zone X",
            # Missing phone, email, website, address, stars, reviews
        }
        
        self.scraper.results = [incomplete_lead]
        self.scraper.save_data()
        
        df = pd.read_excel("leads_pending_lookup.xlsx", keep_default_na=False) # Should go to pending because phone is missing
        row = df[df['name'] == "Ghost Shop"].iloc[0]
        
        # Verify Defaults
        self.assertEqual(row['phone'], "N/A", "Phone should default to N/A")
        self.assertEqual(row['email'], "N/A", "Email should default to N/A")
        self.assertEqual(row['website'], "N/A", "Website should default to N/A")
        # Stars/Reviews default to 0 in save_data logic
        self.assertEqual(row['stars'], 0, "Stars should default to 0")
        self.assertEqual(row['reviews'], 0, "Reviews should default to 0")

    def test_05_closed_business_logic(self):
        print("\n[TEST] Verifying Closed Business Logic...")
        # Since we extracted the logic to a static method, we can unit test it directly!
        
        # 1. Test Closed Cases
        self.assertTrue(GoogleMapsScraper.is_business_closed("Status: Permanently closed"), "Should detect Permanently closed")
        self.assertTrue(GoogleMapsScraper.is_business_closed("Cerrado temporalmente por reformas"), "Should detect Cerrado temporalmente")
        self.assertTrue(GoogleMapsScraper.is_business_closed("This place is Temporarily closed"), "Should detect Temporarily closed")
        
        # 2. Test Open Cases
        self.assertFalse(GoogleMapsScraper.is_business_closed("Open now"), "Should not detect Open as closed")
        self.assertFalse(GoogleMapsScraper.is_business_closed("Abierto las 24 horas"), "Should not detect Abierto as closed")
        self.assertFalse(GoogleMapsScraper.is_business_closed(""), "Empty string is not closed")

    def tearDown(self):
        # print("Cleaning up...")
        pass

if __name__ == '__main__':
    unittest.main()
