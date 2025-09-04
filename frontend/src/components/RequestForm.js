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
    priority: 'medium'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { API } = useContext(AuthContext);
  const navigate = useNavigate();

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API}/requests`, formData);
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
                
                {/* Video Records Legal Notice */}
                {formData.request_type === 'body_cam_footage' && (
                  <div className="bg-amber-50 p-3 rounded-lg border border-amber-200 mt-2">
                    <p className="text-xs text-amber-800 leading-relaxed">
                      <strong>Video Records Notice:</strong> Request inspection or copies of video records (BWC, dash‑cam, fixed) and, if needed, certification docs. Governed by ORC §149.43 and HB 315.
                    </p>
                  </div>
                )}
              </div>

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
              </div>

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
              <CardTitle className="text-lg">Need Help?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-600">
              <p>
                <strong>For technical support:</strong> Contact the IT department at records@police.gov
              </p>
              <p>
                <strong>For questions about specific records:</strong> Call the Records Division at (555) 123-4567
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