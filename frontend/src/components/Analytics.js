import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import { 
  TrendingUp, 
  Clock, 
  Users, 
  FileText, 
  Activity,
  Download,
  Calendar,
  Target
} from 'lucide-react';
import { Button } from './ui/button';
import axios from 'axios';
import { toast } from 'sonner';

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { API } = useContext(AuthContext);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      const response = await axios.get(`${API}/analytics/dashboard`);
      setAnalyticsData(response.data);
    } catch (error) {
      toast.error('Failed to load analytics data');
      console.error('Analytics fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportData = async (format) => {
    try {
      let endpoint = '';
      let filename = '';
      
      if (format === 'csv') {
        endpoint = `${API}/export/requests/csv`;
        filename = 'requests_export.csv';
      }
      
      const response = await axios.get(endpoint, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`Data exported successfully as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export data');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-slate-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-12">
        <Activity className="w-16 h-16 mx-auto mb-4 text-slate-300" />
        <h3 className="text-lg font-medium mb-2">No Analytics Data</h3>
        <p className="text-slate-600">Unable to load analytics data at this time.</p>
      </div>
    );
  }

  // Chart colors
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316'];

  // Prepare data for charts
  const statusData = Object.entries(analyticsData.requests_by_status).map(([key, value]) => ({
    name: key.replace('_', ' ').toUpperCase(),
    value: value
  }));

  const typeData = Object.entries(analyticsData.requests_by_type).map(([key, value]) => ({
    name: key.replace('_', ' ').toUpperCase(),
    value: value
  }));

  const priorityData = Object.entries(analyticsData.requests_by_priority).map(([key, value]) => ({
    name: key.toUpperCase(),
    value: value
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Analytics Dashboard</h1>
          <p className="text-slate-600 mt-1">Comprehensive insights and performance metrics</p>
        </div>
        
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => exportData('csv')}
            className="flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 p-3 rounded-full">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Total Requests</p>
                <p className="text-2xl font-bold text-slate-800">{analyticsData.total_requests}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="bg-green-100 p-3 rounded-full">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Completion Rate</p>
                <p className="text-2xl font-bold text-slate-800">
                  {analyticsData.total_requests > 0 
                    ? Math.round((analyticsData.requests_by_status.completed || 0) / analyticsData.total_requests * 100)
                    : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="bg-amber-100 p-3 rounded-full">
                <Clock className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Avg Resolution Time</p>
                <p className="text-2xl font-bold text-slate-800">
                  {Math.round(analyticsData.average_resolution_time || 0)}h
                </p>
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
                <p className="text-sm text-slate-600">Active Staff</p>
                <p className="text-2xl font-bold text-slate-800">{analyticsData.staff_workload.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="workload">Workload</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Request Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Request Status Distribution</CardTitle>
                <CardDescription>Current status of all requests</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Request Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Request Type Distribution</CardTitle>
                <CardDescription>Types of records requested</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={typeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Priority Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Priority Level Distribution</CardTitle>
              <CardDescription>Request priority breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={priorityData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" />
                  <Tooltip />
                  <Bar dataKey="value" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Monthly Request Trends</CardTitle>
              <CardDescription>Request volume over the last 12 months</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={analyticsData.monthly_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#3B82F6" 
                    fill="#3B82F6" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span className="font-medium">Average Resolution Time</span>
                  <span className="text-2xl font-bold text-blue-600">
                    {Math.round(analyticsData.average_resolution_time || 0)} hours
                  </span>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span className="font-medium">Completion Rate</span>
                  <span className="text-2xl font-bold text-green-600">
                    {analyticsData.total_requests > 0 
                      ? Math.round((analyticsData.requests_by_status.completed || 0) / analyticsData.total_requests * 100)
                      : 0}%
                  </span>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span className="font-medium">Pending Requests</span>
                  <span className="text-2xl font-bold text-amber-600">
                    {analyticsData.requests_by_status.pending || 0}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response Time Goals</CardTitle>
                <CardDescription>Target vs actual performance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Standard Requests (48h target)</span>
                    <span className="text-sm">
                      {analyticsData.average_resolution_time <= 48 ? '✅' : '⚠️'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        analyticsData.average_resolution_time <= 48 ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{ 
                        width: `${Math.min((analyticsData.average_resolution_time / 48) * 100, 100)}%` 
                      }}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Urgent Requests (24h target)</span>
                    <span className="text-sm">
                      {analyticsData.average_resolution_time <= 24 ? '✅' : '⚠️'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        analyticsData.average_resolution_time <= 24 ? 'bg-green-500' : 'bg-amber-500'
                      }`}
                      style={{ 
                        width: `${Math.min((analyticsData.average_resolution_time / 24) * 100, 100)}%` 
                      }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="workload" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Staff Workload Distribution</CardTitle>
              <CardDescription>Assignment and completion statistics by staff member</CardDescription>
            </CardHeader>
            <CardContent>
              {analyticsData.staff_workload.length > 0 ? (
                <div className="space-y-4">
                  {analyticsData.staff_workload.map((staff, index) => (
                    <div key={index} className="p-4 bg-slate-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{staff.name}</span>
                        <div className="flex items-center gap-4 text-sm text-slate-600">
                          <span>Assigned: {staff.assigned}</span>
                          <span>Completed: {staff.completed}</span>
                          <span>
                            Rate: {staff.assigned > 0 ? Math.round((staff.completed / staff.assigned) * 100) : 0}%
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ 
                            width: `${staff.assigned > 0 ? (staff.completed / staff.assigned) * 100 : 0}%` 
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Users className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>No staff workload data available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Analytics;