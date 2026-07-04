import unittest
from tools.schemas import UserProfile
from tools.deduction_checker import calculate_hra_exemption, check_deductions

class TestDeductionChecker(unittest.TestCase):
    def test_calculate_hra_exemption_metro(self):
        # 50% of basic is the cap for metro
        profile = UserProfile(
            name="Test Metro",
            age=30,
            city="Chennai",
            is_metro=True,
            gross_salary=1000000,
            basic_salary=400000,
            hra_received=200000,
            rent_paid_monthly=15000  # Annual rent = 1,80,000
        )
        # 1. HRA received = 2,00,000
        # 2. Rent - 10% basic = 1,80,000 - 40,000 = 1,40,000
        # 3. 50% of basic = 2,00,000
        # Min is 1,40,000
        exemption = calculate_hra_exemption(profile)
        self.assertEqual(exemption, 140000)

    def test_calculate_hra_exemption_non_metro(self):
        # 40% of basic is the cap for non-metro
        profile = UserProfile(
            name="Test Non-Metro",
            age=30,
            city="Pune",
            is_metro=False,
            gross_salary=1000000,
            basic_salary=400000,
            hra_received=200000,
            rent_paid_monthly=20000  # Annual rent = 2,40,000
        )
        # 1. HRA received = 2,00,000
        # 2. Rent - 10% basic = 2,40,000 - 40,000 = 2,00,000
        # 3. 40% of basic = 1,60,000
        # Min is 1,60,000
        exemption = calculate_hra_exemption(profile)
        self.assertEqual(exemption, 160000)

    def test_calculate_hra_exemption_no_rent(self):
        profile = UserProfile(
            name="No Rent",
            age=30,
            city="Chennai",
            is_metro=True,
            gross_salary=1000000,
            basic_salary=400000,
            hra_received=200000,
            rent_paid_monthly=0
        )
        exemption = calculate_hra_exemption(profile)
        self.assertEqual(exemption, 0)

    def test_rahul_profile(self):
        """Original Test Case 1: Rahul — missing many deductions"""
        rahul = UserProfile(
            name="Rahul",
            age=26,
            city="Chennai",
            is_metro=True,
            gross_salary=1200000,
            basic_salary=480000,
            hra_received=240000,
            rent_paid_monthly=15000,
            epf_contribution=57600,
            ppf_contribution=50000,
            savings_account_interest=5000,
            tds_deducted=50000
        )
        report = check_deductions(rahul)
        
        self.assertEqual(report.user_name, "Rahul")
        self.assertEqual(report.total_utilized_deductions, 294600.0) # 50K standard + 107.6K 80C + 132K HRA + 5K 80TTA
        self.assertGreater(report.total_remaining_deductions, 0)
        self.assertIn("80D: No self health insurance. Buy a policy to claim up to Rs. 25,000 deduction.", report.missed_opportunities)
        self.assertIn("80D: No parent health insurance. Buy a policy to claim up to Rs. 25,000 deduction.", report.missed_opportunities)
        self.assertIn("80CCD1B: No NPS investment. Invest up to Rs. 50,000 for additional deduction OVER AND ABOVE 80C limit.", report.missed_opportunities)

    def test_amit_profile(self):
        """Original Test Case 2: Amit — fully optimized"""
        amit = UserProfile(
            name="Amit",
            age=35,
            city="Mumbai",
            is_metro=True,
            gross_salary=1800000,
            basic_salary=720000,
            hra_received=360000,
            rent_paid_monthly=30000,
            epf_contribution=86400,
            ppf_contribution=63600,
            life_insurance_premium=0,
            self_health_insurance=25000,
            parent_health_insurance=50000,
            are_parents_senior_citizen=True,
            nps_contribution=50000,
            home_loan_interest=200000,
            home_loan_principal=100000,
            has_home_loan=True,
            savings_account_interest=8000,
            tds_deducted=150000
        )
        report = check_deductions(amit)
        
        self.assertEqual(report.user_name, "Amit")
        # Check standard deduction, 80C, 80D, 80CCD1B, 24B, 80TTA, HRA
        # HRA Exemption = Min(3.6L, 3.6L - 72K = 2.88L, 3.6L) = 2.88L
        # Utilized 80C = 1.5L
        # Utilized 80D = 25K + 50K = 75K
        # Utilized NPS = 50K
        # Utilized 24B = 2.0L
        # Utilized 80TTA = 8K
        # Standard deduction = 50K
        # Total = 50K + 2.88L + 1.5L + 75K + 50K + 8K + 2.0L = 8.21L
        self.assertEqual(report.total_utilized_deductions, 821000.0)
        self.assertEqual(report.total_remaining_deductions, 74000.0)
        self.assertEqual(len(report.missed_opportunities), 0)

    def test_satish_profile(self):
        """Original Test Case 3: Satish — 65 years old (Senior Citizen 80TTB check)"""
        satish = UserProfile(
            name="Satish",
            age=65,
            city="Delhi",
            is_metro=True,
            gross_salary=600000,
            savings_account_interest=15000,
            other_income=45000,
            tds_deducted=0
        )
        report = check_deductions(satish)
        
        self.assertEqual(report.user_name, "Satish")
        # Verify 80TTB is present (limit 50,000)
        ttb_items = [item for item in report.items if item.section == "80TTB"]
        self.assertEqual(len(ttb_items), 1)
        self.assertEqual(ttb_items[0].utilized, 50000)

    def test_senior_citizen_80d_limit(self):
        """Test that a senior citizen has a 50k limit for self health insurance"""
        senior = UserProfile(
            name="Senior Self 80D",
            age=65,
            city="Delhi",
            self_health_insurance=40000
        )
        report = check_deductions(senior)
        item_80d = [item for item in report.items if item.section == "80D"][0]
        # Max limit should be 50k self + 25k parent = 75k
        self.assertEqual(item_80d.max_limit, 75000)
        self.assertEqual(item_80d.utilized, 40000)

if __name__ == "__main__":
    unittest.main()
