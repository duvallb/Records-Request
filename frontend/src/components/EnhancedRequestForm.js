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
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ArrowLeft, FileText, Send, Calendar, MapPin, User, Hash } from 'lucide-react';
import { toast } from 'sonner';
import FileManager from './FileManager';

const EnhancedRequestForm = () => {
  const [currentTab, setCurrentTab] = useState('basic');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    request_type: '',
    priority: 'medium',
    // Additional fields for enhanced form
    incident_date: '',
    incident_location: '',
    case_number: '',
    officer_names: '',
    vehicle_info: '',
    additional_details: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdRequestId, setCreatedRequestId] = useState(null);
  
  const { API } = useContext(AuthContext);
  const navigate = useNavigate();

  // Request templates
  const requestTemplates = {
    police_report: {
      title: 'Police Report Request',
      description: 'I am requesting a copy of a police report for the following incident:\n\nDate of Incident: [DATE]\nLocation: [LOCATION]\nCase/Report Number: [NUMBER]\nReason for Request: [REASON]\n\nPlease provide a certified copy of the complete report including any supplemental reports.',
      priority: 'medium'
    },
    incident_report: {
      title: 'Incident Report Request', 
      description: 'I need a copy of an incident report for:\n\nDate: [DATE]\nLocation: [LOCATION]\nNature of Incident: [DESCRIPTION]\nInvolved Parties: [NAMES]\n\nThis report is needed for [PURPOSE].',
      priority: 'medium'
    },
    body_cam_footage: {
      title: 'Body Camera Footage Request',
      description: 'I am requesting body camera footage from the following incident:\n\nDate: [DATE]\nTime: [TIME]\nLocation: [LOCATION]\nOfficer(s): [NAMES]\nCase Number: [NUMBER]\n\nPlease note: I understand that footage may be subject to redaction for privacy and ongoing investigation concerns.',
      priority: 'high'
    },
    case_file: {
      title: 'Case File Request',
      description: 'I am requesting access to case file materials for:\n\nCase Number: [NUMBER]\nDate Range: [DATES]\nType of Case: [TYPE]\nSpecific Documents Needed: [LIST]\n\nI understand that active investigation materials may not be available.',
      priority: 'medium'
    }
  };

  const requestTypes = [
    { value: 'incident_report', label: 'Incident Report' },
    { value: 'police_report', label: 'Police Report' },
    { value: 'body_cam_footage', label: 'Body Camera Footage' },
    { value: 'case_file', label: 'Case File' },
    { value: 'other', label: 'Other' }
  ];

  const priorities = [
    { value: 'low', label: 'Low - General inquiry' },
    { value: 'medium', label: 'Medium - Standard request' },
    { value: 'high', label: 'High - Legal/Court deadline' },
    { value: 'urgent', label: 'Urgent - Immediate need' }
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

    // Auto-fill template if available
    if (name === 'request_type' && requestTemplates[value]) {
      const template = requestTemplates[value];
      setFormData(prev => ({
        ...prev,
        [name]: value,
        title: template.title,
        description: template.description,
        priority: template.priority
      }));
    }
  };

  const validateBasicInfo = () => {
    if (!formData.title || !formData.description || !formData.request_type) {
      setError('Please fill in all required fields');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (currentTab === 'basic' && !validateBasicInfo()) {
      return;
    }
    
    if (currentTab === 'basic') {
      setCurrentTab('details');
    } else if (currentTab === 'details') {
      setCurrentTab('review');
    }
  };

  const handlePrevious = () => {
    if (currentTab === 'details') {
      setCurrentTab('basic');
    } else if (currentTab === 'review') {
      setCurrentTab('details');
    }
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      // Combine all form data for description
      let enhancedDescription = formData.description;
      
      if (formData.incident_date || formData.incident_location || formData.case_number) {
        enhancedDescription += '\n\nAdditional Information:\n';
        if (formData.incident_date) enhancedDescription += `Date of Incident: ${formData.incident_date}\n`;
        if (formData.incident_location) enhancedDescription += `Location: ${formData.incident_location}\n`;
        if (formData.case_number) enhancedDescription += `Case/Report Number: ${formData.case_number}\n`;
        if (formData.officer_names) enhancedDescription += `Officer(s) Involved: ${formData.officer_names}\n`;
        if (formData.vehicle_info) enhancedDescription += `Vehicle Information: ${formData.vehicle_info}\n`;
        if (formData.additional_details) enhancedDescription += `Additional Details: ${formData.additional_details}\n`;
      }

      const submitData = {
        title: formData.title,
        description: enhancedDescription,
        request_type: formData.request_type,
        priority: formData.priority
      };

      const response = await axios.post(`${API}/requests`, submitData);
      setCreatedRequestId(response.data.id);
      toast.success('Request submitted successfully!');
      setCurrentTab('files');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to submit request. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = () => {
    navigate(`/request/${createdRequestId}`);
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
            <p className="text-slate-600">Complete the form below to request access to police department records</p>
          </div>
        </div>

        {/* Multi-step Form */}
        <Card className="glass slide-in shadow-2xl border-0">
          <CardContent className="p-8">
            <Tabs value={currentTab} onValueChange={setCurrentTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic" disabled={createdRequestId}>Basic Info</TabsTrigger>
                <TabsTrigger value="details" disabled={!formData.title || createdRequestId}>Details</TabsTrigger>
                <TabsTrigger value="review" disabled={!formData.title || createdRequestId}>Review</TabsTrigger>
                <TabsTrigger value="files" disabled={!createdRequestId}>Files</TabsTrigger>
              </TabsList>

              {/* Basic Information */}
              <TabsContent value="basic" className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold mb-2">Basic Request Information</h3>
                  <p className="text-slate-600">Tell us what type of records you need</p>
                </div>

                {error && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertDescription className="text-red-700">{error}</AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="md:col-span-2">
                    <Label htmlFor="request_type" className="text-sm font-medium text-slate-700">
                      Request Type *
                    </Label>
                    <Select 
                      value={formData.request_type} 
                      onValueChange={(value) => handleSelectChange('request_type', value)}
                    >
                      <SelectTrigger className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2">
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
                  </div>

                  <div className="md:col-span-2">
                    <Label htmlFor="title" className="text-sm font-medium text-slate-700">
                      Request Title *
                    </Label>
                    <Input
                      id="title"
                      name="title"
                      value={formData.title}
                      onChange={handleInputChange}
                      className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                      placeholder="Brief description of your request"
                      required
                    />
                  </div>

                  <div className="md:col-span-2">
                    <Label htmlFor="priority" className="text-sm font-medium text-slate-700">
                      Priority Level
                    </Label>
                    <Select 
                      value={formData.priority} 
                      onValueChange={(value) => handleSelectChange('priority', value)}
                    >
                      <SelectTrigger className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2">
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

                  <div className="md:col-span-2">
                    <Label htmlFor="description" className="text-sm font-medium text-slate-700">
                      Detailed Description *
                    </Label>
                    <Textarea
                      id="description"
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      className="min-h-[120px] border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                      placeholder="Provide specific details about the records you're requesting..."
                      required
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleNext} className="bg-gradient-to-r from-blue-600 to-indigo-600">
                    Next: Add Details
                  </Button>
                </div>
              </TabsContent>

              {/* Additional Details */}
              <TabsContent value="details" className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold mb-2">Additional Details</h3>
                  <p className="text-slate-600">Help us locate the records more quickly (optional)</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="incident_date" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Incident Date
                    </Label>
                    <Input
                      id="incident_date"
                      name="incident_date"
                      type="date"
                      value={formData.incident_date}
                      onChange={handleInputChange}
                      className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                    />
                  </div>

                  <div>
                    <Label htmlFor="case_number" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                      <Hash className="w-4 h-4" />
                      Case/Report Number
                    </Label>
                    <Input
                      id="case_number"
                      name="case_number"
                      value={formData.case_number}
                      onChange={handleInputChange}
                      className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                      placeholder="If known"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <Label htmlFor="incident_location" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      Incident Location
                    </Label>
                    <Input
                      id="incident_location"
                      name="incident_location"
                      value={formData.incident_location}
                      onChange={handleInputChange}
                      className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                      placeholder="Street address or intersection"
                    />
                  </div>

                  <div>
                    <Label htmlFor="officer_names" className="text-sm font-medium text-slate-700 flex items-center gap-2">
                      <User className="w-4 h-4" />
                      Officer Names
                    </Label>
                    <Input
                      id="officer_names"
                      name="officer_names"
                      value={formData.officer_names}
                      onChange={handleInputChange}
                      className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                      placeholder="If known"
                    />
                  </div>

                  <div>
                    <Label htmlFor="vehicle_info" className="text-sm font-medium text-slate-700">
                      Vehicle Information
                    </Label>
                    <Input
                      id="vehicle_info"
                      name="vehicle_info"
                      value={formData.vehicle_info}
                      onChange={handleInputChange}
                      className="h-12 border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                      placeholder="License plate, make, model"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <Label htmlFor="additional_details" className="text-sm font-medium text-slate-700">
                      Additional Details
                    </Label>
                    <Textarea
                      id="additional_details"
                      name="additional_details"
                      value={formData.additional_details}
                      onChange={handleInputChange}
                      className="min-h-[80px] border-slate-200 focus:border-blue-500 focus:ring-blue-500 mt-2"
                      placeholder="Any other relevant information that might help locate the records"
                    />
                  </div>
                </div>

                <div className="flex justify-between pt-4">
                  <Button variant="outline" onClick={handlePrevious}>
                    Previous
                  </Button>
                  <Button onClick={handleNext} className="bg-gradient-to-r from-blue-600 to-indigo-600">
                    Review Request
                  </Button>
                </div>
              </TabsContent>

              {/* Review */}
              <TabsContent value="review" className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold mb-2">Review Your Request</h3>
                  <p className="text-slate-600">Please review the information before submitting</p>
                </div>

                <div className="space-y-6 bg-slate-50 p-6 rounded-lg">
                  <div>
                    <h4 className="font-semibold text-slate-800 mb-2">Request Summary</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Type:</span> {requestTypes.find(t => t.value === formData.request_type)?.label}
                      </div>
                      <div>
                        <span className="font-medium">Priority:</span> {formData.priority}
                      </div>
                      <div className="md:col-span-2">
                        <span className="font-medium">Title:</span> {formData.title}
                      </div>
                    </div>
                  </div>

                  {(formData.incident_date || formData.incident_location || formData.case_number) && (
                    <div>
                      <h4 className="font-semibold text-slate-800 mb-2">Additional Information</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        {formData.incident_date && (
                          <div><span className="font-medium">Date:</span> {formData.incident_date}</div>
                        )}
                        {formData.case_number && (
                          <div><span className="font-medium">Case Number:</span> {formData.case_number}</div>
                        )}
                        {formData.incident_location && (
                          <div className="md:col-span-2"><span className="font-medium">Location:</span> {formData.incident_location}</div>
                        )}
                        {formData.officer_names && (
                          <div className="md:col-span-2"><span className="font-medium">Officers:</span> {formData.officer_names}</div>
                        )}
                      </div>
                    </div>
                  )}

                  <div>
                    <h4 className="font-semibold text-slate-800 mb-2">Description</h4>
                    <p className="text-sm text-slate-700 whitespace-pre-wrap">{formData.description}</p>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">Before Submitting</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Ensure all information is accurate and complete</li>
                    <li>• You will receive email notifications about status updates</li>
                    <li>• Processing time varies based on request complexity</li>
                    <li>• You can add supporting documents after submission</li>
                  </ul>
                </div>

                <div className="flex justify-between pt-4">
                  <Button variant="outline" onClick={handlePrevious}>
                    Previous
                  </Button>
                  <Button 
                    onClick={handleSubmit}
                    disabled={loading}
                    className="bg-gradient-to-r from-blue-600 to-indigo-600"
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
              </TabsContent>

              {/* File Upload */}
              <TabsContent value="files" className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold mb-2">Upload Supporting Documents</h3>
                  <p className="text-slate-600">Add any supporting documents to your request (optional)</p>
                </div>

                {createdRequestId && (
                  <FileManager 
                    requestId={createdRequestId}
                    onFilesUpdate={() => {}}
                  />
                )}

                <div className="text-center pt-6">
                  <Button 
                    onClick={handleFinish}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8"
                  >
                    View My Request
                  </Button>
                  
                  <p className="text-sm text-slate-500 mt-3">
                    You can always add more files later from the request detail page
                  </p>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EnhancedRequestForm;