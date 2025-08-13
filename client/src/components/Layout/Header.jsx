import { Bars3Icon, UserCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import toast from 'react-hot-toast';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import authService from '../../services/auth.service';
import { logout, selectIsAuthenticated, selectUser } from '../../store/authSlice';

const Header = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const user = useSelector(selectUser);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authService.logout();
      dispatch(logout());
      toast.success('Logged out successfully');
      navigate('/');
    } catch (error) {
      dispatch(logout());
      navigate('/');
    }
  };

  const navigation = [
    { name: 'Home', href: '/', show: true },
    { name: 'Dashboard', href: '/dashboard', show: isAuthenticated },
    { name: 'Admin', href: '/admin', show: user?.role === 'admin' },
  ];

  return (
    <header className="bg-white shadow-sm">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" aria-label="Top">
        <div className="flex w-full items-center justify-between py-6">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <span className="text-2xl font-bold text-primary-600">Enterprise</span>
            </Link>
            <div className="hidden ml-10 space-x-8 lg:block">
              {navigation.map((link) =>
                link.show ? (
                  <Link
                    key={link.name}
                    to={link.href}
                    className="text-base font-medium text-gray-700 hover:text-primary-600"
                  >
                    {link.name}
                  </Link>
                ) : null
              )}
            </div>
          </div>
          <div className="ml-10 space-x-4 flex items-center">
            {isAuthenticated ? (
              <>
                <div className="hidden lg:flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <UserCircleIcon className="h-6 w-6 text-gray-400" />
                    <span className="text-sm font-medium text-gray-700">{user?.name}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="btn-secondary text-sm"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <div className="hidden lg:flex items-center space-x-4">
                <Link to="/login" className="btn-secondary text-sm">
                  Login
                </Link>
                <Link to="/register" className="btn-primary text-sm">
                  Register
                </Link>
              </div>
            )}
            <div className="lg:hidden">
              <button
                type="button"
                className="text-gray-700 hover:text-gray-900"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                <span className="sr-only">Open menu</span>
                {mobileMenuOpen ? (
                  <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                ) : (
                  <Bars3Icon className="h-6 w-6" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
        </div>
        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-gray-200">
            <div className="space-y-1">
              {navigation.map((link) =>
                link.show ? (
                  <Link
                    key={link.name}
                    to={link.href}
                    className="block py-2 text-base font-medium text-gray-700 hover:text-primary-600"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {link.name}
                  </Link>
                ) : null
              )}
              {isAuthenticated ? (
                <>
                  <div className="pt-4 pb-2 border-t border-gray-200">
                    <div className="flex items-center space-x-2 py-2">
                      <UserCircleIcon className="h-6 w-6 text-gray-400" />
                      <span className="text-sm font-medium text-gray-700">{user?.name}</span>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left py-2 text-base font-medium text-gray-700 hover:text-primary-600"
                    >
                      Logout
                    </button>
                  </div>
                </>
              ) : (
                <div className="pt-4 space-y-2 border-t border-gray-200">
                  <Link
                    to="/login"
                    className="block py-2 text-base font-medium text-gray-700 hover:text-primary-600"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="block py-2 text-base font-medium text-gray-700 hover:text-primary-600"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
