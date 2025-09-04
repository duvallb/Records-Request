import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Alert, AlertDescription } from './ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  ArrowLeft, 
  FileText, 
  Clock, 
  User, 
  MessageCircle, 
  Send,
  Calendar,
  AlertCircle,
  Download,
  Settings,
  CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';
import FileManager from './FileManager';

const RequestDetail = () => {
  const [request, setRequest] = useState(null);
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [error, setError] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);
  
  const { id } = useParams();
  const { user, API } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRequestDetails();
    fetchMessages();
    fetchFiles();
  }, [id]);

  const fetchRequestDetails = async () => {
    try {
      const response = await axios.get(`${API}/requests/${id}`);
      setRequest(response.data);
    } catch (error) {
      setError('Failed to load request details');
      toast.error('Failed to load request details');
      console.error('Request fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/messages/${id}`);
      setMessages(response.data);
    } catch (error) {
      console.error('Messages fetch error:', error);
    }
  };

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API}/files/${id}`);
      setFiles(response.data);
    } catch (error) {
      console.error('Files fetch error:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setSendingMessage(true);
    try {
      await axios.post(`${API}/messages`, {
        request_id: id,
        content: newMessage.trim()
      });
      
      setNewMessage('');
      fetchMessages(); // Refresh messages
      toast.success('Message sent successfully');
    } catch (error) {
      toast.error('Failed to send message');
      console.error('Send message error:', error);
    } finally {
      setSendingMessage(false);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    setUpdatingStatus(true);
    try {
      await axios.put(`${API}/requests/${id}/status`, null, {
        params: { new_status: newStatus }
      });
      
      toast.success('Status updated successfully');
      fetchRequestDetails(); // Refresh request data
    } catch (error) {
      toast.error('Failed to update status');
      console.error('Status update error:', error);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const exportRequestAsPDF = async () => {
    try {
      const response = await axios.get(`${API}/export/request/${id}/pdf`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `request_${id.substring(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Request exported as PDF');
    } catch (error) {
      toast.error('Failed to export request');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'pending': { variant: 'destructive', label: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
      'assigned': { variant: 'default', label: 'Assigned', color: 'bg-blue-100 text-blue-800' },
      'in_progress': { variant: 'secondary', label: 'In Progress', color: 'bg-purple-100 text-purple-800' },
      'completed': { variant: 'success', label: 'Completed', color: 'bg-green-100 text-green-800' },
      'denied': { variant: 'destructive', label: 'Denied', color: 'bg-red-100 text-red-800' }
    };

    const config = statusConfig[status] || { variant: 'default', label: status, color: 'bg-gray-100 text-gray-800' };
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatRelativeTime = (dateString) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${Math.floor(diffInHours)} hours ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)} days ago`;
    return formatDate(dateString);
  };

  const canUpdateStatus = () => {
    return user?.role === 'admin' || 
           (user?.role === 'staff' && request?.assigned_staff_id === user?.id);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-slate-600">Loading request details...</p>
        </div>
      </div>
    );
  }

  if (error || !request) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/dashboard')}
            className="mb-4 text-slate-600 hover:text-blue-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          
          <Alert className="border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-red-700">
              {error || 'Request not found'}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
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
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Request Details - Left Column */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="glass border-0 shadow-lg fade-in">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                      <FileText className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-xl">{request.title}</CardTitle>
                      <CardDescription className="mt-1">
                        Request ID: {request.id.substring(0, 8)}...
                      </CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(request.status)}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={exportRequestAsPDF}
                      className="ml-2"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      PDF
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <div>
                  <Label className="text-sm font-medium text-slate-700 mb-2 block">
                    Description
                  </Label>
                  <div className="bg-slate-50 p-4 rounded-lg border">
                    <p className="text-slate-800 whitespace-pre-wrap">{request.description}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-sm font-medium text-slate-700">Request Type</Label>
                    <p className="mt-1 text-slate-800 capitalize">
                      {request.request_type.replace('_', ' ')}
                    </p>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-slate-700">Priority</Label>
                    <p className="mt-1 text-slate-800 capitalize">{request.priority}</p>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-slate-700">Submitted</Label>
                    <p className="mt-1 text-slate-800">{formatDate(request.created_at)}</p>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-slate-700">Last Updated</Label>
                    <p className="mt-1 text-slate-800">{formatDate(request.updated_at)}</p>
                  </div>
                </div>

                {/* Status Management for Staff/Admin */}
                {canUpdateStatus() && (
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <Label className="text-sm font-medium text-blue-800 mb-2 block flex items-center gap-2">
                      <Settings className="w-4 h-4" />
                      Update Status
                    </Label>
                    <div className="flex gap-2">
                      <Select 
                        onValueChange={handleStatusUpdate}
                        disabled={updatingStatus}
                      >
                        <SelectTrigger className="w-48">
                          <SelectValue placeholder="Change status..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="assigned">Assigned</SelectItem>
                          <SelectItem value="in_progress">In Progress</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                          <SelectItem value="denied">Denied</SelectItem>
                        </SelectContent>
                      </Select>
                      {updatingStatus && <div className="spinner"></div>}
                    </div>
                  </div>
                )}

                {request.assigned_staff_id && (
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 text-blue-800">
                      <User className="w-4 h-4" />
                      <span className="font-medium">Assigned to Staff</span>
                    </div>
                    <p className="text-sm text-blue-700 mt-1">
                      This request has been assigned to a staff member for processing.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* File Management */}
            <Card className="glass border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Documents & Files
                </CardTitle>
                <CardDescription>
                  Upload and manage files related to this request
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileManager 
                  requestId={id}
                  files={files}
                  onFilesUpdate={fetchFiles}
                  disabled={request.status === 'completed' || request.status === 'denied'}
                />
              </CardContent>
            </Card>

            {/* Messages Section */}
            <Card className="glass border-0 shadow-lg slide-in">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5" />
                  Communication
                </CardTitle>
                <CardDescription>
                  Messages and updates about this request
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Message List */}
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {messages.map((message) => (
                    <div 
                      key={message.id}
                      className={`p-4 rounded-lg ${
                        message.sender_id === user?.id 
                          ? 'bg-blue-100 ml-8' 
                          : 'bg-slate-100 mr-8'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <span className="font-medium text-slate-800">
                            {message.sender_name}
                          </span>
                          <Badge 
                            variant="outline" 
                            className="ml-2 text-xs capitalize"
                          >
                            {message.sender_role}
                          </Badge>
                        </div>
                        <span className="text-xs text-slate-500">
                          {formatRelativeTime(message.created_at)}
                        </span>
                      </div>
                      <p className="text-slate-700 whitespace-pre-wrap">{message.content}</p>
                    </div>
                  ))}

                  {messages.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      <MessageCircle className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p>No messages yet</p>
                      <p className="text-sm">Start a conversation about this request</p>
                    </div>
                  )}
                </div>

                <Separator />

                {/* New Message Form */}
                <form onSubmit={handleSendMessage} className="space-y-3">
                  <Textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message here..."
                    className="min-h-[80px] border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                    disabled={sendingMessage}
                  />
                  <div className="flex justify-end">
                    <Button 
                      type="submit"
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                      disabled={sendingMessage || !newMessage.trim()}
                    >
                      {sendingMessage ? (
                        <div className="flex items-center gap-2">
                          <div className="spinner"></div>
                          Sending...
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <Send className="w-4 h-4" />
                          Send Message
                        </div>
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Right Column */}
          <div className="space-y-6">
            <Card className="glass border-0 shadow-lg slide-in">
              <CardHeader>
                <CardTitle className="text-lg">Request Timeline</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-800">Request Submitted</p>
                      <p className="text-xs text-slate-500">{formatDate(request.created_at)}</p>
                    </div>
                  </div>
                  
                  {request.assigned_staff_id && (
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-800">Assigned to Staff</p>
                        <p className="text-xs text-slate-500">Processing in progress</p>
                      </div>
                    </div>
                  )}
                  
                  {request.status === 'completed' && (
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-800">Request Completed</p>
                        <p className="text-xs text-slate-500">{formatDate(request.updated_at)}</p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg">Request Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Status
                  </Label>
                  <div className="mt-1">
                    {getStatusBadge(request.status)}
                  </div>
                </div>
                
                <div>
                  <Label className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Priority
                  </Label>
                  <p className="mt-1 text-sm text-slate-800 capitalize">{request.priority}</p>
                </div>
                
                <div>
                  <Label className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Type
                  </Label>
                  <p className="mt-1 text-sm text-slate-800 capitalize">
                    {request.request_type.replace('_', ' ')}
                  </p>
                </div>

                <div>
                  <Label className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                    Files Attached
                  </Label>
                  <p className="mt-1 text-sm text-slate-800">{files.length}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg">Contact Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-slate-600">
                <p>
                  <strong>For technical support:</strong><br />
                  Contact the IT department at records@Shakerpd.com
                </p>
                <p>
                  <strong>For questions about specific records:</strong><br />
                  Call the Records Division at (216) 1220
                </p>
                <p>
                  <strong>Processing time:</strong><br />
                  Most requests are processed within 5-10 business days
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RequestDetail;