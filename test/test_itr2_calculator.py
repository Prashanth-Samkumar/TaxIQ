import unittest
from tools.schemas import ITR2Input, ITR2Result
from tools.itr2_calculator import calculate_itr2_tax

class TestITR2Calculator(unittest.TestCase):
    def test_karan_profile_rebate_exclusion(self):
        """Test Case 1: Karan — Salary 8L, STCG Equity 1L (Rebate 87A exclusion check)"""
        karan = ITR2Input(
            gross_salary=800000,
            age=30,
            cg_stcg_equity=100000
        )
        results = calculate_itr2_tax(karan, regime="new")
        result = results["new"]
        
        # Salary 8L, STCG Equity 1L. Total Income 9L.
        # Standard deduction 75,000. Taxable Normal Income 7.25L.
        # Slab tax under New Regime: 5% of 3.25L = 16,250.
        # STCG Equity tax: 20% of 1L = 20,000.
        # Total income is 9L (<= 12L limit for 87A).
        # Normal tax (16,250) is fully rebated. STCG tax (20,000) CANNOT be rebated.
        # Cess = 20,000 * 0.04 = 800. Total tax = 20,800.
        self.assertEqual(result.rebate_87a, 16250.0)
        self.assertEqual(result.total_tax_liability, 20800.0)

    def test_high_income_surcharge_capping(self):
        """Test Case 2: High Income — Salary 2.5 Cr, STCG Equity 60 Lakhs (Surcharge capping check)"""
        high_inc = ITR2Input(
            gross_salary=25000000,
            age=45,
            cg_stcg_equity=6000000
        )
        results = calculate_itr2_tax(high_inc, regime="both")
        
        self.assertIn("new", results)
        new_res = results["new"]
        # Verify New Regime Surcharge logic:
        # gross_salary = 2.5Cr. Standard deduction = 75k. Taxable Normal = 24,925,000.
        # Slabs tax:
        # 4-8L (20k), 8-12L (40k), 12-16L (60k), 16-20L (80k), 20-24L (1L), Above 24L (30% of 22,525,000 = 6,757,500).
        # Total normal tax = 7,057,500.
        # STCG Equity tax = 6,000,000 * 20% = 1,200,000.
        # Total income is 3.1Cr, which is in (2Cr, 5Cr] bracket (25% normal surcharge rate).
        # Surcharge on normal: 7,057,500 * 25% = 1,764,375.
        # Surcharge on STCG Equity (capped at 15%): 1,200,000 * 15% = 180,000.
        # Total surcharge = 1,764,375 + 180,000 = 1,944,375.
        # Cess = (total tax (8,257,500) + surcharge (1,944,375)) * 4% = 408,075.
        # Total tax liability = 8,257,500 + 1,944,375 + 408,075 = 10,609,950.
        self.assertEqual(new_res.surcharge, 1944375.0)
        self.assertEqual(new_res.total_tax_liability, 10609950.0)

    def test_amit_surcharge_marginal_relief(self):
        """Test Case 3: Amit — Salary 51.25L, no investments (Surcharge marginal relief at 50L)"""
        amit = ITR2Input(
            gross_salary=5125000,
            age=35
        )
        results = calculate_itr2_tax(amit, regime="new")
        result = results["new"]
        # Taxable normal = 5,050,000. Slabs tax = 1,095,000.
        # Surcharge (normal 10%) = 109,500. Total tax + surcharge = 1,204,500.
        # Tax at threshold 50L: taxable = 5,000,000. Slabs tax = 1,080,000. Surcharge = 0.
        # Excess income = 5,050,000 - 5,000,000 = 50,000.
        # Max allowed = 1,080,000 + 50,000 = 1,130,000.
        # Actual (1,204,500) > Max (1,130,000), so relief applies.
        # Relief = 1,204,500 - 1,130,000 = 74,500.
        # Surcharge final = 109,500 - 74,500 = 35,000.
        # Cess = (1,095,000 + 35,000) * 0.04 = 45,200.
        # Total tax liability = 1,095,000 + 35,000 + 45,200 = 1,175,200.
        self.assertEqual(result.surcharge, 35000.0)
        self.assertEqual(result.total_tax_liability, 1175200.0)

if __name__ == "__main__":
    unittest.main()
