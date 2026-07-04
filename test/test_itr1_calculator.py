import unittest
from tools.schemas import TaxInput, TaxResult
from tools.itr1_calculator import calculate_tax, calculate_rebate_87a

class TestITR1Calculator(unittest.TestCase):
    def test_rahul_profile(self):
        """Test Case 1: Rahul — Salary 12L, 80C 1L, HRA 60K, 80D 25K"""
        rahul = TaxInput(
            gross_salary=1200000,
            age=26,
            hra_exemption=60000,
            standard_deduction=75000,
            deduction_80c=100000,
            deduction_80d_self=25000,
            tds_deducted=50000
        )
        results = calculate_tax(rahul, regime="both")
        
        self.assertIn("old", results)
        self.assertIn("new", results)
        
        old_res = results["old"]
        new_res = results["new"]
        
        # Verify Old Regime calculations
        # Gross = 12L
        # Deductions = 50K standard + 60K HRA + 100K 80C + 25K 80D = 235K
        # Taxable = 12L - 235K = 965K
        # Slab tax old:
        # Nil up to 2.5L
        # 5% of 2.5L = 12,500
        # 20% of 4.65L = 93,000
        # Total base tax = 1,05,500
        # Cess (4%) = 4,220
        # Total tax = 1,09,720
        self.assertEqual(old_res.taxable_income, 965000)
        self.assertEqual(old_res.total_deductions, 235000)
        self.assertEqual(old_res.total_tax, 109720.0)
        
        # Verify New Regime calculations
        # Gross = 12L
        # Deductions = 75K standard
        # Taxable = 12L - 75K = 1125K (<= 12L, so 87A rebate applies and tax is 0)
        self.assertEqual(new_res.taxable_income, 1125000)
        self.assertEqual(new_res.total_tax, 0.0)

    def test_priya_profile(self):
        """Test Case 2: Priya — Salary 8L, no investments"""
        priya = TaxInput(
            gross_salary=800000,
            age=24,
            tds_deducted=20000
        )
        results = calculate_tax(priya, regime="both")
        
        # New regime taxable = 8L - 75K = 7.25L <= 12L, so rebate 87A applies, total tax = 0
        self.assertEqual(results["new"].total_tax, 0.0)
        # Old regime taxable = 8L - 50K standard = 7.5L
        # Slab tax old: 12,500 (up to 5L) + 20% of 2.5L (50,000) = 62,500
        # Cess = 2,500
        # Total tax = 65,000
        self.assertEqual(results["old"].total_tax, 65000.0)

    def test_amit_profile(self):
        """Test Case 3: Amit — Salary 18L, fully optimized deductions"""
        amit = TaxInput(
            gross_salary=1800000,
            age=35,
            hra_exemption=120000,
            standard_deduction=75000,
            deduction_80c=150000,
            deduction_80d_self=25000,
            deduction_80d_parents=50000,
            are_parents_senior_citizen=True,
            deduction_80ccd1b=50000,
            deduction_24b=200000,
            tds_deducted=150000
        )
        results = calculate_tax(amit, regime="both")
        
        # Standard deduction 50k + HRA 120k + 80C 150k + 80D 75k + 80CCD1B 50k + 24b 200k = 645k
        # Taxable normal old = 18L - 645k = 1155k
        # Taxable normal new = 18L - 75k = 1725k
        self.assertEqual(results["old"].total_deductions, 645000)
        self.assertEqual(results["new"].total_deductions, 75000)
        self.assertEqual(results["old"].taxable_income, 1155000)
        self.assertEqual(results["new"].taxable_income, 1725000)

    def test_vikram_marginal_relief(self):
        """Test Case 4: Vikram — Salary 12.8L, no investments (New Regime marginal relief check)"""
        vikram = TaxInput(
            gross_salary=1280000,
            age=30,
            tds_deducted=0
        )
        results = calculate_tax(vikram, regime="new")
        result = results["new"]
        # Verify: taxable income = 12,05,000. Tax before rebate = 60,750.
        # Excess income over 12L = 5,000. Capped tax = 5,000. Cess = 200. Total tax = 5,200.
        self.assertEqual(result.total_tax, 5200.0)

    def test_sneha_no_marginal_relief(self):
        """Test Case 5: Sneha — Salary 13.5L, no investments (New Regime above marginal relief limit)"""
        sneha = TaxInput(
            gross_salary=1350000,
            age=28,
            tds_deducted=0
        )
        results = calculate_tax(sneha, regime="new")
        result = results["new"]
        # Verify: taxable income = 12,75,000. Tax before rebate = 71,250.
        # Excess income over 12L = 75,000. Slabs tax is less than excess income, so no marginal relief.
        # Cess = 71,250 * 0.04 = 2,850. Total tax = 74,100.
        self.assertEqual(result.total_tax, 74100.0)

    def test_low_salary(self):
        """Test Case 6: Kiran — Salary 30K, no other income (Low income standard deduction cap)"""
        kiran = TaxInput(
            gross_salary=30000,
            age=25,
            tds_deducted=0
        )
        results = calculate_tax(kiran, regime="both")
        
        self.assertEqual(results["old"].total_deductions, 30000.0)
        self.assertEqual(results["new"].total_deductions, 30000.0)
        self.assertEqual(results["old"].taxable_income, 0.0)
        self.assertEqual(results["new"].taxable_income, 0.0)
        self.assertEqual(results["old"].total_tax, 0.0)
        self.assertEqual(results["new"].total_tax, 0.0)

    def test_new_regime_exactly_12l_taxable(self):
        """Test Case 7: Deepa — Salary 12.75L, no investments (Exactly 12L taxable income in New Regime)"""
        deepa = TaxInput(
            gross_salary=1275000,
            age=32,
            tds_deducted=0
        )
        results = calculate_tax(deepa, regime="new")
        result = results["new"]
        self.assertEqual(result.taxable_income, 1200000.0)
        self.assertEqual(result.total_tax, 0.0)

    def test_new_regime_marginal_relief_applies(self):
        """Test Case 8: Rohan — Salary 1,345,588, no investments (Marginal relief crossover - relief applies)"""
        rohan = TaxInput(
            gross_salary=1345588,
            age=30,
            tds_deducted=0
        )
        results = calculate_tax(rohan, regime="new")
        result = results["new"]
        # Taxable income = 1,270,588. Slab tax = 60,000 + 15% of 70,588 = 70,588.20.
        # Excess income = 70,588. Slab tax > Excess income, so relief applies.
        # Capped tax before cess = 70,588. Cess = 70,588 * 0.04 = 2823.52.
        # Total tax = 73,411.52.
        self.assertEqual(round(result.total_tax, 2), 73411.52)

    def test_new_regime_marginal_relief_does_not_apply(self):
        """Test Case 9: Sunita — Salary 1,346,000, no investments (Marginal relief crossover - relief does NOT apply)"""
        sunita = TaxInput(
            gross_salary=1346000,
            age=30,
            tds_deducted=0
        )
        results = calculate_tax(sunita, regime="new")
        result = results["new"]
        # Taxable income = 1,271,000. Slab tax = 60,000 + 15% of 71,000 = 70,650.
        # Excess income = 71,000. Slab tax <= Excess income, so no relief.
        # Cess = 70,650 * 0.04 = 2,826.
        # Total tax = 73,476.
        self.assertEqual(result.total_tax, 73476.0)

    def test_senior_citizen_old_regime(self):
        """Test Case 10: Senior Citizen (65) Old Regime Slab Rates (3L basic exemption)"""
        # Taxable income = 6L - 50K standard deduction = 5.5L
        # Slab tax:
        # Nil up to 3L
        # 5% of 2L = 10,000
        # 20% of 50K = 10,000
        # Base tax = 20,000. Cess = 800. Total = 20,800
        senior = TaxInput(
            gross_salary=600000,
            age=65,
            tds_deducted=0
        )
        results = calculate_tax(senior, regime="old")
        result = results["old"]
        self.assertEqual(result.taxable_income, 550000.0)
        self.assertEqual(result.total_tax, 20800.0)

    def test_super_senior_citizen_old_regime(self):
        """Test Case 11: Super Senior Citizen (85) Old Regime Slab Rates (5L basic exemption)"""
        # Taxable income = 6L - 50K standard deduction = 5.5L
        # Slab tax:
        # Nil up to 5L
        # 20% of 50K = 10,000
        # Base tax = 10,000. Cess = 400. Total = 10,400
        super_senior = TaxInput(
            gross_salary=600000,
            age=85,
            tds_deducted=0
        )
        results = calculate_tax(super_senior, regime="old")
        result = results["old"]
        self.assertEqual(result.taxable_income, 550000.0)
        self.assertEqual(result.total_tax, 10400.0)

if __name__ == "__main__":
    unittest.main()
