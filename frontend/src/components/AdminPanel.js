import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Users, 
  UserPlus, 
  FileText, 
  Settings, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  UserCheck,
  Mail,
  Search
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const AdminPanel = () => {
  const [staff, setStaff] = useState([]);
  const [masterRequests, setMasterRequests] = useState([]);
  const [unassignedRequests, setUnassignedRequests] = useState([]);
  const [allUsers, setAllUsers] = useState([]); // New state for all users
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Staff creation form
  const [newStaffForm, setNewStaffForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'staff'
  });
  const [creatingStaff, setCreatingStaff] = useState(false);

  const { API } = useContext(AuthContext);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      // Use Promise.all but with individual error handling
      const results = await Promise.allSettled([
        axios.get(`${API}/admin/staff-members`),
        axios.get(`${API}/admin/requests-master-list`),
        axios.get(`${API}/admin/unassigned-requests`),
        axios.get(`${API}/admin/users`)
      ]);

      // Handle staff members
      if (results[0].status === 'fulfilled') {
        setStaff(results[0].value.data || []);
      } else {
        console.error('Staff members failed:', results[0].reason);
        setStaff([]);
      }

      // Handle master requests
      if (results[1].status === 'fulfilled') {
        const masterData = results[1].value.data || [];
        console.log('Master requests loaded:', masterData.length);
        setMasterRequests(masterData);
      } else {
        console.error('Master requests failed:', results[1].reason);
        setMasterRequests([]);
        toast.error('Failed to load requests');
      }

      // Handle unassigned requests  
      if (results[2].status === 'fulfilled') {
        setUnassignedRequests(results[2].value.data || []);
      } else {
        console.error('Unassigned requests failed:', results[2].reason);
        setUnassignedRequests([]);
      }

      // Handle all users
      if (results[3].status === 'fulfilled') {
        setAllUsers(results[3].value.data || []);
      } else {
        console.error('All users failed:', results[3].reason);
        setAllUsers([]);
      }

    } catch (error) {
      console.error('General admin data fetch error:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStaff = async (e) => {
    e.preventDefault();
    setCreatingStaff(true);

    try {
      await axios.post(`${API}/admin/create-staff`, newStaffForm);
      toast.success('Staff member created successfully!');
      setNewStaffForm({ full_name: '', email: '', password: '', role: 'staff' });
      fetchAdminData(); // Refresh data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to create staff member';
      toast.error(errorMessage);
    } finally {
      setCreatingStaff(false);
    }
  };

  const handleAssignRequest = async (requestId, staffId) => {
    try {
      await axios.post(`${API}/requests/${requestId}/assign`, {
        request_id: requestId,
        staff_id: staffId
      });
      
      toast.success('Request assigned successfully!');
      fetchAdminData(); // Refresh data
    } catch (error) {
      toast.error('Failed to assign request');
    }
  };

  // New function to update user role
  const handleUpdateUserRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/role`, { role: newRole });
      toast.success(`User role updated to ${newRole}`);
      fetchAdminData(); // Refresh data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to update user role';
      toast.error(errorMessage);
    }
  };

  // New function to update user email
  const handleUpdateUserEmail = async (userId, newEmail) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/email`, { email: newEmail });
      toast.success('User email updated successfully');
      fetchAdminData(); // Refresh data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to update user email';
      toast.error(errorMessage);
    }
  };

  // New function to delete request
  const handleDeleteRequest = async (requestId, requestTitle) => {
    if (!window.confirm(`Are you sure you want to permanently delete the request "${requestTitle}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/requests/${requestId}`);
      toast.success('Request deleted successfully');
      fetchAdminData(); // Refresh data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete request';
      toast.error(errorMessage);
    }
  };

  // New function to cancel request
  const handleCancelRequest = async (requestId, requestTitle) => {
    const reason = window.prompt(`Enter reason for cancelling "${requestTitle}":`);
    if (!reason) {
      return;
    }

    try {
      await axios.put(`${API}/admin/requests/${requestId}/cancel`, { reason });
      toast.success('Request cancelled successfully');
      fetchAdminData(); // Refresh data
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to cancel request';
      toast.error(errorMessage);
    }
  };

  const exportMasterList = async () => {
    try {
      const response = await axios.get(`${API}/export/requests/csv`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'master_requests_list.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Master list exported successfully');
    } catch (error) {
      toast.error('Failed to export master list');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'pending': { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'assigned': { color: 'bg-blue-100 text-blue-800', icon: UserCheck },
      'in_progress': { color: 'bg-purple-100 text-purple-800', icon: Settings },
      'completed': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'denied': { color: 'bg-red-100 text-red-800', icon: AlertTriangle }
    };

    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-800', icon: FileText };
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3" />
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filter requests based on search term
  const filteredRequests = masterRequests.filter(request =>
    request.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    request.requester_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    request.status.toLowerCase().includes(searchTerm.toLowerCase()) ||
    request.request_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-slate-600">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Administrator Panel</h1>
          <p className="text-slate-600 mt-1">Manage staff, assignments, and system overview</p>
        </div>
        
        <Button 
          onClick={exportMasterList}
          className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
        >
          <Download className="w-4 h-4 mr-2" />
          Export Master List
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="staff">Staff Management</TabsTrigger>
          <TabsTrigger value="requests">Master Requests</TabsTrigger>
          <TabsTrigger value="assignments">Assignments</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="bg-blue-100 p-3 rounded-full">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Total Requests</p>
                    <p className="text-2xl font-bold text-slate-800">{masterRequests.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="bg-yellow-100 p-3 rounded-full">
                    <AlertTriangle className="w-6 h-6 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Unassigned</p>
                    <p className="text-2xl font-bold text-slate-800">{unassignedRequests.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="bg-purple-100 p-3 rounded-full">
                    <Users className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Staff Members</p>
                    <p className="text-2xl font-bold text-slate-800">{staff.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="bg-green-100 p-3 rounded-full">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Completed Today</p>
                    <p className="text-2xl font-bold text-slate-800">
                      {masterRequests.filter(r => 
                        r.status === 'completed' && 
                        new Date(r.updated_at).toDateString() === new Date().toDateString()
                      ).length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Requests Requiring Attention</CardTitle>
              <CardDescription>Unassigned and high-priority requests</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {unassignedRequests.slice(0, 5).map((request) => (
                  <div key={request.id} className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <div className="flex-1">
                      <h4 className="font-medium text-slate-800">{request.title}</h4>
                      <p className="text-sm text-slate-600">
                        Submitted by {request.requester_name} on {formatDate(request.created_at)}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {getStatusBadge(request.status)}
                        <Badge variant="outline">{request.priority}</Badge>
                      </div>
                    </div>
                    <Button 
                      size="sm"
                      onClick={() => setActiveTab('assignments')}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Assign Now
                    </Button>
                  </div>
                ))}
                
                {unassignedRequests.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
                    <p>All requests are assigned! Great job.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-6">
          {/* User Management Tab */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                User Management
              </CardTitle>
              <CardDescription>Manage all user accounts, roles, and permissions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {allUsers.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        user.role === 'admin' ? 'bg-red-600' : 
                        user.role === 'staff' ? 'bg-blue-600' : 'bg-green-600'
                      }`}>
                        <span className="text-white font-semibold">
                          {user.full_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-slate-800">{user.full_name}</h4>
                        <p className="text-sm text-slate-600 flex items-center gap-1">
                          <Mail className="w-3 h-3" />
                          {user.email}
                        </p>
                        <p className="text-xs text-slate-500">
                          Created: {formatDate(user.created_at)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="space-y-2">
                        <Label className="text-xs">Role</Label>
                        <Select 
                          value={user.role} 
                          onValueChange={(newRole) => handleUpdateUserRole(user.id, newRole)}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="user">Citizen</SelectItem>
                            <SelectItem value="staff">Staff</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="text-xs">Email</Label>
                        <Input
                          type="email"
                          defaultValue={user.email}
                          className="w-64"
                          onBlur={(e) => {
                            if (e.target.value !== user.email && e.target.value.includes('@')) {
                              handleUpdateUserEmail(user.id, e.target.value);
                            }
                          }}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && e.target.value !== user.email && e.target.value.includes('@')) {
                              handleUpdateUserEmail(user.id, e.target.value);
                            }
                          }}
                        />
                      </div>
                      
                      <Badge 
                        variant="outline" 
                        className={`capitalize ${
                          user.role === 'admin' ? 'border-red-200 text-red-700' : 
                          user.role === 'staff' ? 'border-blue-200 text-blue-700' : 
                          'border-green-200 text-green-700'
                        }`}
                      >
                        {user.role}
                      </Badge>
                    </div>
                  </div>
                ))}
                
                {allUsers.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <Users className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>No users found.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="staff" className="space-y-6">
          {/* Create New Staff */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserPlus className="w-5 h-5" />
                Add New Staff Member
              </CardTitle>
              <CardDescription>Create new staff accounts to handle requests</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateStaff} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      value={newStaffForm.full_name}
                      onChange={(e) => setNewStaffForm({...newStaffForm, full_name: e.target.value})}
                      placeholder="Enter full name"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={newStaffForm.email}
                      onChange={(e) => setNewStaffForm({...newStaffForm, email: e.target.value})}
                      placeholder="Enter email address"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="password">Temporary Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={newStaffForm.password}
                      onChange={(e) => setNewStaffForm({...newStaffForm, password: e.target.value})}
                      placeholder="Enter temporary password"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="role">Role</Label>
                    <Select 
                      value={newStaffForm.role} 
                      onValueChange={(value) => setNewStaffForm({...newStaffForm, role: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="staff">Staff Member</SelectItem>
                        <SelectItem value="admin">Administrator</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <Button 
                  type="submit" 
                  disabled={creatingStaff}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {creatingStaff ? (
                    <div className="flex items-center gap-2">
                      <div className="spinner"></div>
                      Creating...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <UserPlus className="w-4 h-4" />
                      Create Staff Member
                    </div>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Staff List */}
          <Card>
            <CardHeader>
              <CardTitle>Current Staff Members</CardTitle>
              <CardDescription>Overview of all staff members and their workload</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {staff.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center gap-4">
                      <div className="bg-blue-600 w-10 h-10 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold">
                          {member.full_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <h4 className="font-medium text-slate-800">{member.full_name}</h4>
                        <p className="text-sm text-slate-600 flex items-center gap-1">
                          <Mail className="w-3 h-3" />
                          {member.email}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6 text-sm">
                      <div className="text-center">
                        <div className="font-semibold text-slate-800">{member.assigned_requests}</div>
                        <div className="text-slate-500">Assigned</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-green-600">{member.completed_requests}</div>
                        <div className="text-slate-500">Completed</div>
                      </div>
                      <Badge variant="outline" className="capitalize">
                        {member.assigned_requests > 10 ? 'High Load' : 
                         member.assigned_requests > 5 ? 'Medium Load' : 'Low Load'}
                      </Badge>
                    </div>
                  </div>
                ))}
                
                {staff.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <Users className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>No staff members yet. Create your first staff account above.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="requests" className="space-y-6">
          {/* Search and Export */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search requests by title, requester, status, or type..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button onClick={exportMasterList} variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Master Requests List */}
          <Card>
            <CardHeader>
              <CardTitle>Master Requests List</CardTitle>
              <CardDescription>
                Complete overview of all requests with full details
                {searchTerm && ` (${filteredRequests.length} of ${masterRequests.length} requests)`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-slate-50">
                      <th className="text-left p-3 font-medium">Request</th>
                      <th className="text-left p-3 font-medium">Requester</th>
                      <th className="text-left p-3 font-medium">Status</th>
                      <th className="text-left p-3 font-medium">Assigned To</th>
                      <th className="text-left p-3 font-medium">Priority</th>
                      <th className="text-left p-3 font-medium">Created</th>
                      <th className="text-left p-3 font-medium">Activity</th>
                      <th className="text-left p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRequests.map((request) => (
                      <tr key={request.id} className="border-b hover:bg-slate-50">
                        <td className="p-3">
                          <div>
                            <div className="font-medium text-slate-800">{request.title}</div>
                            <div className="text-xs text-slate-500 capitalize">
                              {request.request_type.replace('_', ' ')}
                            </div>
                          </div>
                        </td>
                        <td className="p-3">
                          <div>
                            <div className="font-medium">{request.requester_name}</div>
                            <div className="text-xs text-slate-500">{request.requester_email}</div>
                          </div>
                        </td>
                        <td className="p-3">
                          {getStatusBadge(request.status)}
                        </td>
                        <td className="p-3">
                          {request.assigned_staff_name ? (
                            <div>
                              <div className="font-medium text-green-700">{request.assigned_staff_name}</div>
                              <div className="text-xs text-slate-500">{request.assigned_staff_email}</div>
                            </div>
                          ) : (
                            <span className="text-red-600 text-xs font-medium">UNASSIGNED</span>
                          )}
                        </td>
                        <td className="p-3">
                          <Badge variant="outline" className="capitalize">
                            {request.priority}
                          </Badge>
                        </td>
                        <td className="p-3 text-xs text-slate-500">
                          {formatDate(request.created_at)}
                        </td>
                        <td className="p-3 text-xs text-slate-500">
                          <div>Files: {request.file_count || 0}</div>
                          <div>Messages: {request.message_count || 0}</div>
                        </td>
                        <td className="p-3">
                          <div className="flex gap-2">
                            {request.status !== 'cancelled' && request.status !== 'completed' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleCancelRequest(request.id, request.title)}
                                className="text-yellow-600 hover:text-yellow-700 border-yellow-300 hover:border-yellow-400"
                              >
                                Cancel
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteRequest(request.id, request.title)}
                              className="text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                            >
                              Delete
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {filteredRequests.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>{searchTerm ? 'No requests match your search' : 'No requests found'}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assignments" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Request Assignments</CardTitle>
              <CardDescription>Assign unassigned requests to available staff members</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {unassignedRequests.map((request) => (
                  <div key={request.id} className="p-4 border rounded-lg bg-yellow-50 border-yellow-200">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h4 className="font-semibold text-slate-800 mb-1">{request.title}</h4>
                        <p className="text-slate-600 text-sm mb-2">{request.description.substring(0, 150)}...</p>
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <span>Requester: {request.requester_name}</span>
                          <span>•</span>
                          <span>Priority: {request.priority}</span>
                          <span>•</span>
                          <span>Type: {request.request_type.replace('_', ' ')}</span>
                          <span>•</span>
                          <span>Created: {formatDate(request.created_at)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Label className="text-sm font-medium">Assign to:</Label>
                      <Select onValueChange={(staffId) => handleAssignRequest(request.id, staffId)}>
                        <SelectTrigger className="w-64">
                          <SelectValue placeholder="Select staff member..." />
                        </SelectTrigger>
                        <SelectContent>
                          {staff.map((member) => (
                            <SelectItem key={member.id} value={member.id}>
                              {member.full_name} ({member.assigned_requests} assigned)
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                ))}
                
                {unassignedRequests.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
                    <h3 className="font-medium mb-2">All requests are assigned!</h3>
                    <p>There are no unassigned requests at this time.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Email Configuration Notice */}
      <Alert>
        <Mail className="h-4 w-4" />
        <AlertDescription>
          <strong>Email Configuration:</strong> Email notifications are configured in the backend .env file. 
          Currently showing logged notifications (check server logs). To enable actual email sending, 
          configure SMTP_USERNAME, SMTP_PASSWORD, and other email settings in /app/backend/.env
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default AdminPanel;