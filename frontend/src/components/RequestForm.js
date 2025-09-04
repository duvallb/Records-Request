import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { ArrowLeft, FileText, Send } from 'lucide-react';
import { toast } from 'sonner';

const RequestForm = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    request_type: '',
    case_number: '',
    priority: 'medium',
    // Body camera specific fields
    incident_date: '',
    incident_time: '',
    incident_location: '',
    officer_names: ''
  });
  const [costAcknowledged, setCostAcknowledged] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { API, user } = useContext(AuthContext);
  const navigate = useNavigate();

  // Check if user has special privileges (law department, attorney, court, other police departments)
  const isSpecialRequester = user && (
    user.role === 'admin' || 
    user.role === 'staff' ||
    user.email?.includes('@law.') ||
    user.email?.includes('@court.') ||
    user.email?.includes('@attorney.') ||
    user.email?.includes('@police.') ||
    user.email?.includes('pd.com') ||
    user.email?.includes('law.com')
  );

  const requestTypes = [
    { value: 'incident_report', label: 'Incident Report' },
    { value: 'police_report', label: 'Police Report' },
    { value: 'body_cam_footage', label: 'Body Camera Footage' },
    { value: 'case_file', label: 'Case File' },
    { value: 'other', label: 'Other' }
  ];

  const priorities = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'urgent', label: 'Urgent' }
  ];

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSelectChange = (name, value) => {
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleCaseNumberChange = (e) => {
    let value = e.target.value.toUpperCase();
    
    // Remove any non-alphanumeric characters except hyphens
    value = value.replace(/[^A-Z0-9-]/g, '');
    
    // Format as ##-######
    if (value.length > 2 && value.charAt(2) !== '-') {
      value = value.slice(0, 2) + '-' + value.slice(2);
    }
    
    // Limit to 9 characters (##-######)
    if (value.length > 9) {
      value = value.slice(0, 9);
    }
    
    setFormData({
      ...formData,
      case_number: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Additional validation for body camera footage requests
      if (formData.request_type === 'body_cam_footage') {
        if (!costAcknowledged) {
          const errorMsg = 'Please acknowledge the cost requirements for body camera footage requests.';
          setError(errorMsg);
          toast.error(errorMsg);
          setLoading(false);
          return;
        }
        
        if (!formData.incident_date || !formData.incident_time || !formData.incident_location || !formData.officer_names) {
          const errorMsg = 'Please fill in all required fields for body camera footage requests (Date, Time, Location, Officer names).';
          setError(errorMsg);
          toast.error(errorMsg);
          setLoading(false);
          return;
        }
      }

      // Prepare submission data
      const submissionData = {
        ...formData,
        cost_acknowledged: costAcknowledged
      };

      const response = await axios.post(`${API}/requests`, submissionData);
      toast.success('Request submitted successfully!');
      navigate(`/request/${response.data.id}`);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to submit request. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/dashboard')}
            className="mb-4 text-slate-600 hover:text-blue-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          
          <div className="text-center fade-in">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-3 rounded-full">
                <FileText className="w-8 h-8 text-white" />
              </div>
            </div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2">Submit Records Request</h1>
            <p className="text-slate-600">Request access to police department records</p>
          </div>
        </div>

        {/* Form */}
        <Card className="glass slide-in shadow-2xl border-0 max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl text-center">New Request</CardTitle>
            <CardDescription className="text-center">
              Please provide detailed information about the records you're requesting
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertDescription className="text-red-700">{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="title" className="text-sm font-medium text-slate-700">
                  Request Title *
                </Label>
                <Input
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Brief description of your request"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="request_type" className="text-sm font-medium text-slate-700">
                  Request Type *
                </Label>
                <Select 
                  value={formData.request_type} 
                  onValueChange={(value) => handleSelectChange('request_type', value)}
                >
                  <SelectTrigger className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Select type of records" />
                  </SelectTrigger>
                  <SelectContent>
                    {requestTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                {/* Body Camera Footage Cost Acknowledgment and Details */}
                {formData.request_type === 'body_cam_footage' && (
                  <div className="space-y-4">
                    {/* Detailed Body Camera Request Form */}
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <h4 className="text-sm font-semibold text-blue-800 mb-3">Body Camera Footage Request Details</h4>
                      <p className="text-sm text-blue-700 mb-4">
                        I am requesting body camera footage from the following incident:
                      </p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="incident_date" className="text-sm font-medium text-blue-800">
                            Date *
                          </Label>
                          <Input
                            id="incident_date"
                            name="incident_date"
                            type="date"
                            value={formData.incident_date}
                            onChange={handleInputChange}
                            className="border-blue-200 focus:border-blue-500 focus:ring-blue-500"
                            required
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label htmlFor="incident_time" className="text-sm font-medium text-blue-800">
                            Time *
                          </Label>
                          <Input
                            id="incident_time"
                            name="incident_time"
                            type="time"
                            value={formData.incident_time}
                            onChange={handleInputChange}
                            className="border-blue-200 focus:border-blue-500 focus:ring-blue-500"
                            required
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2 mt-4">
                        <Label htmlFor="incident_location" className="text-sm font-medium text-blue-800">
                          Location *
                        </Label>
                        <Input
                          id="incident_location"
                          name="incident_location"
                          value={formData.incident_location}
                          onChange={handleInputChange}
                          className="border-blue-200 focus:border-blue-500 focus:ring-blue-500"
                          placeholder="Street address, intersection, or specific location"
                          required
                        />
                      </div>
                      
                      <div className="space-y-2 mt-4">
                        <Label htmlFor="officer_names" className="text-sm font-medium text-blue-800">
                          Officer(s) *
                        </Label>
                        <Input
                          id="officer_names"
                          name="officer_names"
                          value={formData.officer_names}
                          onChange={handleInputChange}
                          className="border-blue-200 focus:border-blue-500 focus:ring-blue-500"
                          placeholder="Officer names or badge numbers"
                          required
                        />
                      </div>
                      
                      <div className="bg-blue-100 p-3 rounded-lg mt-4">
                        <p className="text-xs text-blue-700 leading-relaxed">
                          <strong>Please note:</strong> I understand that footage may be subject to redaction for privacy and ongoing investigation concerns.
                        </p>
                      </div>
                    </div>

                    {/* Cost Acknowledgment with Checkbox */}
                    <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
                      <h4 className="text-sm font-semibold text-amber-800 mb-2">COST ACKNOWLEDGMENT</h4>
                      <p className="text-sm text-amber-800 mb-3">
                        I acknowledge that a deposit of $75 is required for body camera footage requests and understand that the total cost will not exceed $750.
                      </p>
                      <p className="text-xs text-amber-700 leading-relaxed mb-4">
                        <strong>Video Records Notice:</strong> Request inspection or copies of video records (BWC, dash‑cam, fixed) and, if needed, certification docs. Governed by ORC §149.43 and HB 315.
                      </p>
                      
                      {/* Checkbox for acknowledgment */}
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          id="cost_acknowledged"
                          checked={costAcknowledged}
                          onChange={(e) => setCostAcknowledged(e.target.checked)}
                          className="mt-1 h-4 w-4 text-amber-600 focus:ring-amber-500 border-amber-300 rounded"
                          required
                        />
                        <Label htmlFor="cost_acknowledged" className="text-sm text-amber-800 font-medium cursor-pointer">
                          I acknowledge and agree to the cost requirements and legal notices above. *
                        </Label>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Case Number Field */}
              <div className="space-y-2">
                <Label htmlFor="case_number" className="text-sm font-medium text-slate-700">
                  Case Number (if applicable)
                </Label>
                <Input
                  id="case_number"
                  name="case_number"
                  value={formData.case_number}
                  onChange={handleCaseNumberChange}
                  className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Format: 24-123456"
                  maxLength={9}
                />
                <p className="text-xs text-slate-500">
                  Enter case number in format: ##-###### (e.g., 24-123456)
                </p>
              </div>

              {/* Priority Level - Only for Special Requesters */}
              {isSpecialRequester && (
                <div className="space-y-2">
                  <Label htmlFor="priority" className="text-sm font-medium text-slate-700">
                    Priority Level
                  </Label>
                  <Select 
                    value={formData.priority} 
                    onValueChange={(value) => handleSelectChange('priority', value)}
                  >
                    <SelectTrigger className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500">
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      {priorities.map((priority) => (
                        <SelectItem key={priority.value} value={priority.value}>
                          {priority.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    Available for law department, attorneys, courts, and law enforcement
                  </p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="description" className="text-sm font-medium text-slate-700">
                  Detailed Description *
                </Label>
                <Textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  className="min-h-[120px] border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Provide specific details about the records you're requesting, including dates, case numbers, officer names, locations, or any other relevant information that will help us locate the records."
                  required
                />
              </div>

              {/* Payment Information */}
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <h4 className="text-sm font-medium text-green-800 mb-2">Payment Information</h4>
                <div className="text-sm text-green-700 space-y-2">
                  <p className="font-medium mb-2">Accepted Payment Methods:</p>
                  <ul className="space-y-1 ml-4">
                    <li>• <strong>Cash:</strong> Pay in person at the Records Division</li>
                    <li>• <strong>Check:</strong> Pay in person or mail to Records Division</li>
                  </ul>
                  <p className="text-xs text-green-600 mt-2">
                    <strong>Note:</strong> Credit/debit card payments are not currently accepted.
                  </p>
                  <p className="text-xs text-green-600">
                    Fees vary based on request type and processing requirements. You will be notified of exact costs before processing.
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h4 className="text-sm font-medium text-blue-800 mb-2">Important Information</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Processing time varies based on request complexity and availability</li>
                  <li>• You will receive updates on your request status via email</li>
                  <li>• Some records may be partially redacted for privacy or ongoing investigations</li>
                  <li>• Fees may apply for copying and processing services</li>
                </ul>
              </div>

              <div className="flex gap-4 pt-4">
                <Button 
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/dashboard')}
                  className="flex-1 h-12"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="flex-1 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center gap-2">
                      <div className="spinner"></div>
                      Submitting...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Send className="w-4 h-4" />
                      Submit Request
                    </div>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Help Section */}
        <div className="mt-12 max-w-2xl mx-auto">
          <Card className="glass border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="text-lg">Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-600">
              <p>
                <strong>For technical support:</strong> Contact the IT department at records@shakerpd.com
              </p>
              <p>
                <strong>For questions about specific records:</strong> Call the Records Division at (216) 491-1220
              </p>
              <p>
                <strong>Processing time:</strong> Most requests are processed within 5-10 business days
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default RequestForm;