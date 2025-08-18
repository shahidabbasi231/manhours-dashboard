#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

class TruckDriverTrainingAPITester:
    def __init__(self, base_url="https://expense-analytics-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            'drivers': [],
            'modules': [],
            'progress': [],
            'certifications': []
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200) -> tuple[bool, Dict]:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
            
            if not success:
                response_data["status_code"] = response.status_code
                response_data["expected_status"] = expected_status
            
            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_api_root(self):
        """Test API root endpoint"""
        success, data = self.make_request('GET', '')
        return self.log_test("API Root", success, f"- {data.get('message', '')}")

    def test_dashboard_summary(self):
        """Test dashboard summary endpoint"""
        success, data = self.make_request('GET', 'dashboard/summary')
        if success:
            required_fields = ['total_drivers', 'active_drivers', 'total_training_modules', 
                             'overall_completion_rate', 'recent_completions']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                success = False
                details = f"- Missing fields: {missing_fields}"
            else:
                details = f"- Total drivers: {data['total_drivers']}, Modules: {data['total_training_modules']}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Dashboard Summary", success, details)

    def test_initialize_training_modules(self):
        """Test initializing default training modules"""
        success, data = self.make_request('POST', 'training-modules/initialize-defaults')
        if success:
            details = f"- {data.get('message', 'Modules initialized')}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Initialize Training Modules", success, details)

    def test_get_training_modules(self):
        """Test getting training modules"""
        success, data = self.make_request('GET', 'training-modules')
        if success:
            if isinstance(data, list):
                self.created_resources['modules'] = data
                details = f"- Found {len(data)} modules"
                if len(data) > 0:
                    details += f", First module: {data[0].get('name', 'Unknown')}"
            else:
                success = False
                details = f"- Expected list, got: {type(data)}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Get Training Modules", success, details)

    def test_create_driver(self):
        """Test creating a new driver"""
        test_driver = {
            "employee_id": f"TEST{datetime.now().strftime('%H%M%S')}",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@test.com",
            "phone": "555-0123",
            "hire_date": "2024-01-15",
            "license_number": "DL123456789",
            "license_class": "CDL Class A",
            "license_expiry": "2025-12-31",
            "date_of_birth": "1985-05-15",
            "address": "123 Test Street, Test City, TC 12345",
            "emergency_contact_name": "Jane Smith",
            "emergency_contact_phone": "555-0124"
        }
        
        success, data = self.make_request('POST', 'drivers', test_driver, 200)
        if success:
            self.created_resources['drivers'].append(data)
            details = f"- Created driver: {data.get('first_name')} {data.get('last_name')} (ID: {data.get('id')})"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Create Driver", success, details)

    def test_get_drivers(self):
        """Test getting all drivers"""
        success, data = self.make_request('GET', 'drivers')
        if success:
            if isinstance(data, list):
                # Store existing drivers for other tests if we don't have any created ones
                if not self.created_resources['drivers'] and len(data) > 0:
                    self.created_resources['drivers'] = data
                details = f"- Found {len(data)} drivers"
                if len(data) > 0:
                    details += f", First driver: {data[0].get('first_name')} {data[0].get('last_name')}"
            else:
                success = False
                details = f"- Expected list, got: {type(data)}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Get Drivers", success, details)

    def test_get_driver_by_id(self):
        """Test getting a specific driver by ID"""
        if not self.created_resources['drivers']:
            return self.log_test("Get Driver by ID", False, "- No drivers available to test")
        
        driver_id = self.created_resources['drivers'][0]['id']
        success, data = self.make_request('GET', f'drivers/{driver_id}')
        if success:
            details = f"- Retrieved driver: {data.get('first_name')} {data.get('last_name')}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Get Driver by ID", success, details)

    def test_assign_training(self):
        """Test assigning training to a driver"""
        if not self.created_resources['drivers'] or not self.created_resources['modules']:
            return self.log_test("Assign Training", False, "- No drivers or modules available")
        
        assignment_data = {
            "driver_id": self.created_resources['drivers'][0]['id'],
            "module_id": self.created_resources['modules'][0]['id']
        }
        
        success, data = self.make_request('POST', 'training-progress', assignment_data)
        if success:
            self.created_resources['progress'].append(data)
            details = f"- Assigned training to driver (Progress ID: {data.get('id')})"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Assign Training", success, details)

    def test_get_training_progress(self):
        """Test getting training progress"""
        success, data = self.make_request('GET', 'training-progress')
        if success:
            if isinstance(data, list):
                details = f"- Found {len(data)} progress records"
            else:
                success = False
                details = f"- Expected list, got: {type(data)}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Get Training Progress", success, details)

    def test_update_training_progress(self):
        """Test updating training progress"""
        if not self.created_resources['progress']:
            return self.log_test("Update Training Progress", False, "- No progress records available")
        
        progress_id = self.created_resources['progress'][0]['id']
        update_data = {
            "status": "in_progress",
            "start_date": date.today().isoformat()
        }
        
        success, data = self.make_request('PUT', f'training-progress/{progress_id}', update_data)
        if success:
            details = f"- Updated progress status to: {data.get('status')}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Update Training Progress", success, details)

    def test_create_certification(self):
        """Test creating a certification"""
        if not self.created_resources['drivers']:
            return self.log_test("Create Certification", False, "- No drivers available")
        
        cert_data = {
            "driver_id": self.created_resources['drivers'][0]['id'],
            "certification_name": "DOT Physical",
            "certification_type": "Medical",
            "issue_date": "2024-08-01",
            "expiry_date": "2025-08-25",  # Expiring soon for testing
            "issuing_authority": "DOT Medical Examiner",
            "certificate_number": f"DOT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        success, data = self.make_request('POST', 'certifications', cert_data)
        if success:
            self.created_resources['certifications'].append(data)
            details = f"- Created certification: {data.get('certification_name')} (ID: {data.get('id')})"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Create Certification", success, details)

    def test_get_certifications(self):
        """Test getting certifications"""
        success, data = self.make_request('GET', 'certifications')
        if success:
            if isinstance(data, list):
                details = f"- Found {len(data)} certifications"
            else:
                success = False
                details = f"- Expected list, got: {type(data)}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Get Certifications", success, details)

    def test_get_expiring_certifications(self):
        """Test getting expiring certifications"""
        success, data = self.make_request('GET', 'certifications/expiring')
        if success:
            if isinstance(data, list):
                details = f"- Found {len(data)} expiring certifications"
                if len(data) > 0:
                    details += f", First cert: {data[0].get('certification_name', 'Unknown')}"
            else:
                success = False
                details = f"- Expected list, got: {type(data)}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Get Expiring Certifications", success, details)

    def test_driver_analytics(self):
        """Test driver analytics endpoint"""
        if not self.created_resources['drivers']:
            return self.log_test("Driver Analytics", False, "- No drivers available")
        
        driver_id = self.created_resources['drivers'][0]['id']
        success, data = self.make_request('GET', f'analytics/driver-progress/{driver_id}')
        if success:
            required_fields = ['driver', 'training_stats', 'progress_details', 'certifications']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                success = False
                details = f"- Missing fields: {missing_fields}"
            else:
                stats = data.get('training_stats', {})
                details = f"- Completion rate: {stats.get('completion_rate', 0)}%, Total assigned: {stats.get('total_assigned', 0)}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Driver Analytics", success, details)

    def test_compliance_report(self):
        """Test compliance report endpoint"""
        success, data = self.make_request('GET', 'analytics/compliance-report')
        if success:
            if isinstance(data, list):
                details = f"- Found {len(data)} compliance records"
                if len(data) > 0:
                    first_record = data[0]
                    details += f", First driver compliance: {first_record.get('compliance_status', 'Unknown')}"
            else:
                success = False
                details = f"- Expected list, got: {type(data)}"
        else:
            details = f"- Error: {data}"
        
        return self.log_test("Compliance Report", success, details)

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚛 Starting Truck Driver Training API Tests")
        print("=" * 60)
        
        # Basic connectivity
        self.test_api_root()
        
        # Initialize system
        self.test_initialize_training_modules()
        self.test_get_training_modules()
        
        # Driver management
        self.test_create_driver()
        self.test_get_drivers()
        self.test_get_driver_by_id()
        
        # Training management
        self.test_assign_training()
        self.test_get_training_progress()
        self.test_update_training_progress()
        
        # Certification management
        self.test_create_certification()
        self.test_get_certifications()
        self.test_get_expiring_certifications()
        
        # Analytics and reporting
        self.test_dashboard_summary()
        self.test_driver_analytics()
        self.test_compliance_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend API is working correctly.")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} test(s) failed. Please check the backend implementation.")
            return 1

def main():
    """Main test execution"""
    tester = TruckDriverTrainingAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())