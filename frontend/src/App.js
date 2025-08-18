import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard Home Component
const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [expiringCerts, setExpiringCerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [summaryRes, expiringRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary`),
        axios.get(`${API}/certifications/expiring`)
      ]);
      setSummary(summaryRes.data);
      setExpiringCerts(expiringRes.data);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Training Dashboard</h1>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-700">Total Drivers</h3>
          <p className="text-3xl font-bold text-blue-600">{summary?.total_drivers || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-700">Training Modules</h3>
          <p className="text-3xl font-bold text-green-600">{summary?.total_training_modules || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-700">Completion Rate</h3>
          <p className="text-3xl font-bold text-purple-600">{summary?.overall_completion_rate || 0}%</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-700">Recent Completions</h3>
          <p className="text-3xl font-bold text-orange-600">{summary?.recent_completions || 0}</p>
        </div>
      </div>

      {/* Alerts */}
      {(summary?.drivers_with_expired_certifications > 0 || summary?.drivers_with_expiring_certifications > 0) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-3">🚨 Certification Alerts</h3>
          <div className="space-y-2">
            {summary?.drivers_with_expired_certifications > 0 && (
              <p className="text-red-700">
                <span className="font-semibold">{summary.drivers_with_expired_certifications}</span> drivers have expired certifications
              </p>
            )}
            {summary?.drivers_with_expiring_certifications > 0 && (
              <p className="text-orange-700">
                <span className="font-semibold">{summary.drivers_with_expiring_certifications}</span> drivers have certifications expiring within 30 days
              </p>
            )}
          </div>
        </div>
      )}

      {/* Expiring Certifications */}
      {expiringCerts.length > 0 && (
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Expiring Certifications</h3>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 font-semibold text-gray-700">Driver</th>
                    <th className="text-left py-2 font-semibold text-gray-700">Certification</th>
                    <th className="text-left py-2 font-semibold text-gray-700">Expiry Date</th>
                    <th className="text-left py-2 font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {expiringCerts.map((cert, index) => (
                    <tr key={index} className="border-b border-gray-100">
                      <td className="py-3 text-gray-900">{cert.driver_name}</td>
                      <td className="py-3 text-gray-700">{cert.certification_name}</td>
                      <td className="py-3 text-gray-700">{new Date(cert.expiry_date).toLocaleDateString()}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          cert.status === 'expired' ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'
                        }`}>
                          {cert.status === 'expired' ? 'Expired' : 'Expiring Soon'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Drivers Management Component
const DriversManagement = () => {
  const [drivers, setDrivers] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDrivers();
  }, []);

  const fetchDrivers = async () => {
    try {
      const response = await axios.get(`${API}/drivers`);
      setDrivers(response.data);
    } catch (error) {
      console.error("Error fetching drivers:", error);
    } finally {
      setLoading(false);
    }
  };

  const AddDriverForm = () => {
    const [formData, setFormData] = useState({
      employee_id: '',
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      hire_date: '',
      license_number: '',
      license_class: 'CLASS_A',
      license_expiry: '',
      date_of_birth: '',
      address: '',
      emergency_contact_name: '',
      emergency_contact_phone: ''
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/drivers`, formData);
        setShowAddForm(false);
        fetchDrivers();
        setFormData({
          employee_id: '',
          first_name: '',
          last_name: '',
          email: '',
          phone: '',
          hire_date: '',
          license_number: '',
          license_class: 'CLASS_A',
          license_expiry: '',
          date_of_birth: '',
          address: '',
          emergency_contact_name: '',
          emergency_contact_phone: ''
        });
      } catch (error) {
        console.error("Error creating driver:", error);
        alert("Error creating driver. Please check all fields.");
      }
    };

    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">Add New Driver</h3>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Employee ID"
            value={formData.employee_id}
            onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="text"
            placeholder="First Name"
            value={formData.first_name}
            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="text"
            placeholder="Last Name"
            value={formData.last_name}
            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="tel"
            placeholder="Phone"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="date"
            placeholder="Hire Date"
            value={formData.hire_date}
            onChange={(e) => setFormData({...formData, hire_date: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="text"
            placeholder="License Number"
            value={formData.license_number}
            onChange={(e) => setFormData({...formData, license_number: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <select
            value={formData.license_class}
            onChange={(e) => setFormData({...formData, license_class: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          >
            <option value="CLASS_A">Class A</option>
            <option value="CLASS_B">Class B</option>
            <option value="CLASS_C">Class C</option>
            <option value="CDL_A">CDL Class A</option>
            <option value="CDL_B">CDL Class B</option>
          </select>
          <input
            type="date"
            placeholder="License Expiry"
            value={formData.license_expiry}
            onChange={(e) => setFormData({...formData, license_expiry: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="date"
            placeholder="Date of Birth"
            value={formData.date_of_birth}
            onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="text"
            placeholder="Address"
            value={formData.address}
            onChange={(e) => setFormData({...formData, address: e.target.value})}
            className="p-2 border border-gray-300 rounded md:col-span-2"
            required
          />
          <input
            type="text"
            placeholder="Emergency Contact Name"
            value={formData.emergency_contact_name}
            onChange={(e) => setFormData({...formData, emergency_contact_name: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <input
            type="tel"
            placeholder="Emergency Contact Phone"
            value={formData.emergency_contact_phone}
            onChange={(e) => setFormData({...formData, emergency_contact_phone: e.target.value})}
            className="p-2 border border-gray-300 rounded"
            required
          />
          <div className="md:col-span-2 flex gap-4">
            <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              Add Driver
            </button>
            <button 
              type="button" 
              onClick={() => setShowAddForm(false)}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Drivers Management</h1>
        <button 
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          {showAddForm ? 'Cancel' : 'Add New Driver'}
        </button>
      </div>

      {showAddForm && <AddDriverForm />}

      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 font-semibold text-gray-700">Employee ID</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Name</th>
                  <th className="text-left py-3 font-semibold text-gray-700">License</th>
                  <th className="text-left py-3 font-semibold text-gray-700">License Expiry</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Hire Date</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {drivers.map((driver) => (
                  <tr key={driver.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 text-gray-900">{driver.employee_id}</td>
                    <td className="py-3 text-gray-900">{driver.first_name} {driver.last_name}</td>
                    <td className="py-3 text-gray-700">{driver.license_class} - {driver.license_number}</td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        new Date(driver.license_expiry) < new Date() 
                          ? 'bg-red-100 text-red-800'
                          : new Date(driver.license_expiry) < new Date(Date.now() + 30*24*60*60*1000)
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {new Date(driver.license_expiry).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="py-3 text-gray-700">{new Date(driver.hire_date).toLocaleDateString()}</td>
                    <td className="py-3">
                      <Link 
                        to={`/drivers/${driver.id}`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {drivers.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No drivers found. Add your first driver to get started.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Training Management Component
const TrainingManagement = () => {
  const [modules, setModules] = useState([]);
  const [progress, setProgress] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAssignForm, setShowAssignForm] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [modulesRes, progressRes, driversRes] = await Promise.all([
        axios.get(`${API}/training-modules`),
        axios.get(`${API}/training-progress`),
        axios.get(`${API}/drivers`)
      ]);
      setModules(modulesRes.data);
      setProgress(progressRes.data);
      setDrivers(driversRes.data);
    } catch (error) {
      console.error("Error fetching training data:", error);
    } finally {
      setLoading(false);
    }
  };

  const initializeDefaultModules = async () => {
    try {
      await axios.post(`${API}/training-modules/initialize-defaults`);
      fetchData();
    } catch (error) {
      console.error("Error initializing modules:", error);
    }
  };

  const AssignTrainingForm = () => {
    const [selectedDriver, setSelectedDriver] = useState('');
    const [selectedModule, setSelectedModule] = useState('');

    const handleAssign = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/training-progress`, {
          driver_id: selectedDriver,
          module_id: selectedModule
        });
        setShowAssignForm(false);
        fetchData();
        setSelectedDriver('');
        setSelectedModule('');
      } catch (error) {
        console.error("Error assigning training:", error);
        alert("Error assigning training. This assignment may already exist.");
      }
    };

    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">Assign Training</h3>
        <form onSubmit={handleAssign} className="space-y-4">
          <select
            value={selectedDriver}
            onChange={(e) => setSelectedDriver(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded"
            required
          >
            <option value="">Select Driver</option>
            {drivers.map(driver => (
              <option key={driver.id} value={driver.id}>
                {driver.first_name} {driver.last_name} ({driver.employee_id})
              </option>
            ))}
          </select>
          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded"
            required
          >
            <option value="">Select Training Module</option>
            {modules.map(module => (
              <option key={module.id} value={module.id}>
                {module.name} ({module.duration_hours}h)
              </option>
            ))}
          </select>
          <div className="flex gap-4">
            <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              Assign Training
            </button>
            <button 
              type="button" 
              onClick={() => setShowAssignForm(false)}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Training Management</h1>
        <div className="flex gap-4">
          {modules.length === 0 && (
            <button 
              onClick={initializeDefaultModules}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Initialize Default Modules
            </button>
          )}
          <button 
            onClick={() => setShowAssignForm(!showAssignForm)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            {showAssignForm ? 'Cancel' : 'Assign Training'}
          </button>
        </div>
      </div>

      {showAssignForm && <AssignTrainingForm />}

      {/* Training Modules */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Available Training Modules</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {modules.map((module) => (
              <div key={module.id} className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900">{module.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{module.description}</p>
                <div className="mt-3 space-y-1">
                  <p className="text-xs text-gray-500">Duration: {module.duration_hours} hours</p>
                  <p className="text-xs text-gray-500">Required Score: {module.required_score}%</p>
                  <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                    module.is_mandatory ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                  }`}>
                    {module.is_mandatory ? 'Mandatory' : 'Optional'}
                  </span>
                </div>
              </div>
            ))}
          </div>
          {modules.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No training modules found. Initialize default modules to get started.
            </div>
          )}
        </div>
      </div>

      {/* Training Progress */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Training Progress</h3>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 font-semibold text-gray-700">Driver</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Module</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Status</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Score</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Completion Date</th>
                </tr>
              </thead>
              <tbody>
                {progress.map((prog) => {
                  const driver = drivers.find(d => d.id === prog.driver_id);
                  const module = modules.find(m => m.id === prog.module_id);
                  return (
                    <tr key={prog.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 text-gray-900">
                        {driver ? `${driver.first_name} ${driver.last_name}` : 'Unknown Driver'}
                      </td>
                      <td className="py-3 text-gray-700">{module ? module.name : 'Unknown Module'}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          prog.status === 'completed' ? 'bg-green-100 text-green-800' :
                          prog.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                          prog.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {prog.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 text-gray-700">{prog.score || 'N/A'}</td>
                      <td className="py-3 text-gray-700">
                        {prog.completion_date ? new Date(prog.completion_date).toLocaleDateString() : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {progress.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No training assignments found. Assign training to drivers to track progress.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Driver Details Component
const DriverDetails = () => {
  const location = useLocation();
  const driverId = location.pathname.split('/').pop();
  const [driverData, setDriverData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDriverData();
  }, [driverId]);

  const fetchDriverData = async () => {
    try {
      const response = await axios.get(`${API}/analytics/driver-progress/${driverId}`);
      setDriverData(response.data);
    } catch (error) {
      console.error("Error fetching driver data:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateTrainingProgress = async (progressId, updates) => {
    try {
      await axios.put(`${API}/training-progress/${progressId}`, updates);
      fetchDriverData(); // Refresh data
    } catch (error) {
      console.error("Error updating progress:", error);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  if (!driverData) {
    return <div className="text-center py-8 text-gray-500">Driver not found.</div>;
  }

  const { driver, training_stats, progress_details, certifications } = driverData;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/drivers" className="text-blue-600 hover:text-blue-800">← Back to Drivers</Link>
        <h1 className="text-3xl font-bold text-gray-900">
          {driver.first_name} {driver.last_name}
        </h1>
      </div>

      {/* Driver Info */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">Driver Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Employee ID</p>
            <p className="font-medium">{driver.employee_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Email</p>
            <p className="font-medium">{driver.email}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Phone</p>
            <p className="font-medium">{driver.phone}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">License</p>
            <p className="font-medium">{driver.license_class} - {driver.license_number}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">License Expiry</p>
            <p className="font-medium">{new Date(driver.license_expiry).toLocaleDateString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Hire Date</p>
            <p className="font-medium">{new Date(driver.hire_date).toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      {/* Training Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h4 className="text-sm font-semibold text-gray-600">Completion Rate</h4>
          <p className="text-2xl font-bold text-green-600">{training_stats.completion_rate}%</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h4 className="text-sm font-semibold text-gray-600">Completed</h4>
          <p className="text-2xl font-bold text-blue-600">{training_stats.completed}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h4 className="text-sm font-semibold text-gray-600">In Progress</h4>
          <p className="text-2xl font-bold text-orange-600">{training_stats.in_progress}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h4 className="text-sm font-semibold text-gray-600">Average Score</h4>
          <p className="text-2xl font-bold text-purple-600">{training_stats.average_score}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h4 className="text-sm font-semibold text-gray-600">Not Started</h4>
          <p className="text-2xl font-bold text-gray-600">{training_stats.not_started}</p>
        </div>
      </div>

      {/* Training Progress Details */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Training Progress</h3>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {progress_details.map((prog) => (
              <div key={prog.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-gray-900">{prog.module_name}</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Status: <span className={`font-medium ${
                        prog.status === 'completed' ? 'text-green-600' :
                        prog.status === 'in_progress' ? 'text-blue-600' :
                        prog.status === 'failed' ? 'text-red-600' :
                        'text-gray-600'
                      }`}>
                        {prog.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </p>
                    {prog.score && <p className="text-sm text-gray-600">Score: {prog.score}%</p>}
                    {prog.completion_date && (
                      <p className="text-sm text-gray-600">
                        Completed: {new Date(prog.completion_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {prog.status === 'not_started' && (
                      <button 
                        onClick={() => updateTrainingProgress(prog.id, { status: 'in_progress' })}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        Start
                      </button>
                    )}
                    {prog.status === 'in_progress' && (
                      <>
                        <button 
                          onClick={() => {
                            const score = prompt("Enter score (0-100):");
                            if (score && !isNaN(score) && score >= 0 && score <= 100) {
                              updateTrainingProgress(prog.id, { 
                                status: 'completed', 
                                score: parseInt(score) 
                              });
                            }
                          }}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                        >
                          Complete
                        </button>
                        <button 
                          onClick={() => updateTrainingProgress(prog.id, { status: 'failed' })}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          Mark Failed
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {progress_details.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No training assigned to this driver yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Reports Component
const Reports = () => {
  const [complianceReport, setComplianceReport] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await axios.get(`${API}/analytics/compliance-report`);
      setComplianceReport(response.data);
    } catch (error) {
      console.error("Error fetching reports:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Compliance Reports</h1>

      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Driver Compliance Status</h3>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 font-semibold text-gray-700">Driver</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Mandatory Training</th>
                  <th className="text-left py-3 font-semibold text-gray-700">License Status</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Expired Certs</th>
                  <th className="text-left py-3 font-semibold text-gray-700">Compliance</th>
                </tr>
              </thead>
              <tbody>
                {complianceReport.map((report, index) => (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 text-gray-900">
                      {report.driver.first_name} {report.driver.last_name}
                    </td>
                    <td className="py-3 text-gray-700">{report.mandatory_training_completion}</td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        report.license_status === 'Expired' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {report.license_status}
                      </span>
                    </td>
                    <td className="py-3 text-gray-700">{report.expired_certifications}</td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        report.compliance_status === 'Compliant' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {report.compliance_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {complianceReport.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No compliance data available. Add drivers and assign training to generate reports.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/drivers', label: 'Drivers', icon: '👥' },
    { path: '/training', label: 'Training', icon: '📚' },
    { path: '/reports', label: 'Reports', icon: '📈' },
  ];

  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex space-x-8">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm ${
                location.pathname === item.path
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <main className="max-w-7xl mx-auto py-6 px-4">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/drivers" element={<DriversManagement />} />
              <Route path="/drivers/:id" element={<DriverDetails />} />
              <Route path="/training" element={<TrainingManagement />} />
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;