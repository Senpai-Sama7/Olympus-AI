import {
  ChartBarIcon,
  CubeIcon,
  ShieldCheckIcon,
  TrashIcon,
  UsersIcon
} from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import Header from '../components/Layout/Header';
import api from '../services/api';

const AdminPage = () => {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({
    users: { total: 0, byRole: {} },
    products: { totalProducts: 0, avgPrice: 0, totalValue: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchData();
  }, [page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [usersResponse, statsResponse] = await Promise.all([
        api.get(`/admin/users?page=${page}&limit=10`),
        api.get('/admin/stats')
      ]);

      setUsers(usersResponse.data.data.users);
      setTotalPages(usersResponse.data.data.pagination.pages);
      setStats(statsResponse.data.data.stats);
    } catch (error) {
      toast.error('Failed to fetch admin data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user? This will also delete all their products.')) {
      return;
    }

    try {
      await api.delete(`/admin/users/${userId}`);
      toast.success('User deleted successfully');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to delete user');
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.put(`/admin/users/${userId}/role`, { role: newRole });
      toast.success('User role updated successfully');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to update role');
    }
  };

  const statCards = [
    {
      name: 'Total Users',
      value: stats.users.total,
      icon: UsersIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Total Products',
      value: stats.products.totalProducts,
      icon: CubeIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Average Price',
      value: `$${stats.products.avgPrice?.toFixed(2) || '0.00'}`,
      icon: ChartBarIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'Total Value',
      value: `$${stats.products.totalValue?.toFixed(2) || '0.00'}`,
      icon: ChartBarIcon,
      color: 'bg-yellow-500',
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Admin Header */}
        <div className="px-4 py-6 sm:px-0">
          <div className="flex items-center">
            <ShieldCheckIcon className="h-8 w-8 text-primary-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          </div>
          <p className="mt-2 text-gray-600">
            Manage users and monitor system statistics
          </p>
        </div>

        {/* Stats Grid */}
        <div className="mt-8 px-4 sm:px-0">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {statCards.map((stat) => (
              <div key={stat.name} className="card">
                <div className="card-body">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className={`${stat.color} rounded-md p-3`}>
                        <stat.icon className="h-6 w-6 text-white" />
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          {stat.name}
                        </dt>
                        <dd className="text-2xl font-semibold text-gray-900">
                          {stat.value}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Role Distribution */}
        <div className="mt-8 px-4 sm:px-0">
          <h2 className="text-lg font-medium text-gray-900 mb-4">User Distribution</h2>
          <div className="card">
            <div className="card-body">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-500">Regular Users:</span>
                  <span className="ml-2 text-lg font-semibold">{stats.users.byRole?.user || 0}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Admins:</span>
                  <span className="ml-2 text-lg font-semibold">{stats.users.byRole?.admin || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="mt-8 px-4 sm:px-0">
          <h2 className="text-lg font-medium text-gray-900 mb-4">All Users</h2>
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Joined
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user._id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {user.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <select
                          value={user.role}
                          onChange={(e) => handleRoleChange(user._id, e.target.value)}
                          className="text-sm rounded-md border-gray-300 focus:border-primary-500 focus:ring-primary-500"
                        >
                          <option value="user">User</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.createdAt).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleDeleteUser(user._id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center mt-4 gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="flex items-center px-4">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminPage;
