import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Shield, 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Plus, 
  Bell,
  User,
  LogOut,
  Users,
  Settings,
  Search
} from 'lucide-react';
import { toast } from 'sonner';

const Dashboard = () => {
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  const { user, logout, API } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [requestsRes, statsRes, notificationsRes] = await Promise.all([
        axios.get(`${API}/requests`),
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/notifications`)
      ]);

      setRequests(requestsRes.data);
      setStats(statsRes.data);
      setNotifications(notificationsRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'pending': { variant: 'destructive', label: 'Pending' },
      'assigned': { variant: 'default', label: 'Assigned' },
      'in_progress': { variant: 'secondary', label: 'In Progress' },
      'completed': { variant: 'success', label: 'Completed' },
      'denied': { variant: 'destructive', label: 'Denied' }
    };

    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
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

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const handleRequestClick = (requestId) => {
    navigate(`/request/${requestId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="glass border-b border-white/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-800">Records Portal</h1>
                <p className="text-sm text-slate-600 capitalize">{user?.role} Dashboard</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="relative">
                <Bell className="w-5 h-5 text-slate-600 cursor-pointer hover:text-blue-600 transition-colors" />
                {notifications.filter(n => !n.is_read).length > 0 && (
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                    {notifications.filter(n => !n.is_read).length}
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-2 text-slate-700">
                <User className="w-4 h-4" />
                <span className="text-sm font-medium">{user?.full_name}</span>
              </div>
              
              <Button 
                onClick={handleLogout}
                variant="ghost"
                size="sm"
                className="text-slate-600 hover:text-red-600"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-96">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="requests">Requests</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="glass border-0 shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="bg-blue-100 p-3 rounded-full">
                      <FileText className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Total Requests</p>
                      <p className="text-2xl font-bold text-slate-800">{stats.total_requests || 0}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass border-0 shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="bg-amber-100 p-3 rounded-full">
                      <Clock className="w-6 h-6 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Pending</p>
                      <p className="text-2xl font-bold text-slate-800">{stats.pending_requests || 0}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass border-0 shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="bg-green-100 p-3 rounded-full">
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Completed</p>
                      <p className="text-2xl font-bold text-slate-800">{stats.completed_requests || 0}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {user?.role === 'admin' && (
                <Card className="glass border-0 shadow-lg hover:shadow-xl transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="bg-purple-100 p-3 rounded-full">
                        <Users className="w-6 h-6 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Total Users</p>
                        <p className="text-2xl font-bold text-slate-800">{stats.total_users || 0}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Quick Actions */}
            <Card className="glass border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common tasks and shortcuts</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button 
                    onClick={() => navigate('/request/new')}
                    className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 h-12"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    New Request
                  </Button>
                  
                  <Button variant="outline" className="h-12">
                    <Search className="w-4 h-4 mr-2" />
                    Search Records
                  </Button>
                  
                  <Button variant="outline" className="h-12">
                    <Settings className="w-4 h-4 mr-2" />
                    Settings
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Recent Requests */}
            <Card className="glass border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Recent Requests</CardTitle>
                <CardDescription>Your latest records requests</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {requests.slice(0, 5).map((request) => (
                    <div 
                      key={request.id}
                      className="flex items-center justify-between p-4 rounded-lg border border-slate-200 hover:border-blue-300 cursor-pointer transition-colors"
                      onClick={() => handleRequestClick(request.id)}
                    >
                      <div className="flex-1">
                        <h4 className="font-medium text-slate-800">{request.title}</h4>
                        <p className="text-sm text-slate-600 mt-1">
                          {formatDate(request.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        {getStatusBadge(request.status)}
                        <Badge variant="outline">{request.request_type.replace('_', ' ')}</Badge>
                      </div>
                    </div>
                  ))}
                  
                  {requests.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p>No requests yet</p>
                      <Button 
                        onClick={() => navigate('/request/new')}
                        className="mt-3"
                        variant="outline"
                      >
                        Create your first request
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="requests" className="space-y-6">
            <Card className="glass border-0 shadow-lg">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>All Requests</CardTitle>
                  <CardDescription>Manage and track your records requests</CardDescription>
                </div>
                <Button 
                  onClick={() => navigate('/request/new')}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Request
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {requests.map((request) => (
                    <div 
                      key={request.id}
                      className="p-6 rounded-lg border border-slate-200 hover:border-blue-300 cursor-pointer transition-all hover:shadow-md"
                      onClick={() => handleRequestClick(request.id)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-slate-800 mb-1">{request.title}</h3>
                          <p className="text-slate-600 mb-2">{request.description}</p>
                          <p className="text-sm text-slate-500">
                            Submitted on {formatDate(request.created_at)}
                          </p>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {getStatusBadge(request.status)}
                          <Badge variant="outline">{request.request_type.replace('_', ' ')}</Badge>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-slate-500">
                        <span>Priority: {request.priority}</span>
                        {request.assigned_staff_id && (
                          <span>• Assigned to staff</span>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {requests.length === 0 && (
                    <div className="text-center py-12 text-slate-500">
                      <FileText className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                      <h3 className="text-lg font-medium mb-2">No requests found</h3>
                      <p className="mb-4">Create your first records request to get started</p>
                      <Button 
                        onClick={() => navigate('/request/new')}
                        className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        New Request
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-6">
            <Card className="glass border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Notifications</CardTitle>
                <CardDescription>Stay updated on your requests and system updates</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {notifications.map((notification) => (
                    <div 
                      key={notification.id}
                      className={`p-4 rounded-lg border transition-colors ${
                        notification.is_read 
                          ? 'border-slate-200 bg-slate-50' 
                          : 'border-blue-200 bg-blue-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-slate-800">{notification.title}</h4>
                          <p className="text-slate-600 mt-1">{notification.message}</p>
                          <p className="text-sm text-slate-500 mt-2">
                            {formatDate(notification.created_at)}
                          </p>
                        </div>
                        {!notification.is_read && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {notifications.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      <Bell className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p>No notifications</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="profile" className="space-y-6">
            <Card className="glass border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Your account details and settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center gap-6">
                  <div className="bg-gradient-to-r from-blue-600 to-indigo-600 w-16 h-16 rounded-full flex items-center justify-center">
                    <span className="text-white text-xl font-semibold">
                      {user?.full_name?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-slate-800">{user?.full_name}</h3>
                    <p className="text-slate-600">{user?.email}</p>
                    <Badge variant="outline" className="mt-2 capitalize">{user?.role}</Badge>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-sm font-medium text-slate-700">Account Type</Label>
                    <p className="mt-1 text-slate-800 capitalize">{user?.role}</p>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-slate-700">Member Since</Label>
                    <p className="mt-1 text-slate-800">{formatDate(user?.created_at)}</p>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-slate-700">Status</Label>
                    <p className="mt-1 text-green-600">Active</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;