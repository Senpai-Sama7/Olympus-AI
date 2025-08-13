import {
  ChartBarIcon,
  CubeIcon,
  CurrencyDollarIcon,
  ShoppingCartIcon
} from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import Header from '../components/Layout/Header';
import ProductList from '../components/Product/ProductList';
import api from '../services/api';
import { selectUser } from '../store/authSlice';

const DashboardPage = () => {
  const user = useSelector(selectUser);
  const [stats, setStats] = useState({
    totalProducts: 0,
    productsByCategory: {},
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get('/users/stats');
      setStats(response.data.data.stats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      name: 'Total Products',
      value: stats.totalProducts,
      icon: CubeIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Electronics',
      value: stats.productsByCategory?.electronics || 0,
      icon: ChartBarIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Clothing',
      value: stats.productsByCategory?.clothing || 0,
      icon: ShoppingCartIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'Other Categories',
      value: Object.values(stats.productsByCategory || {})
        .reduce((sum, val) => sum + val, 0) -
        (stats.productsByCategory?.electronics || 0) -
        (stats.productsByCategory?.clothing || 0),
      icon: CurrencyDollarIcon,
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Welcome Section */}
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg p-8 text-center">
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome back, {user?.name}!
            </h1>
            <p className="mt-2 text-gray-600">
              Here's what's happening with your products today.
            </p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="mt-8 px-4 sm:px-0">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Your Statistics</h2>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
          ) : (
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
          )}
        </div>

        {/* My Products Section */}
        <div className="mt-8 px-4 sm:px-0">
          <h2 className="text-lg font-medium text-gray-900 mb-4">My Products</h2>
          <ProductList />
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
