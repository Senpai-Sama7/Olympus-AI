import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import ErrorBoundary from './components/ErrorBoundary';
import Router from './router/Router';
import authService from './services/auth.service';
import { logout, selectAuth, setLoading, setUser } from './store/authSlice';

function App() {
  const dispatch = useDispatch();
  const { token } = useSelector(selectAuth);

  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const response = await authService.getMe();
          dispatch(setUser(response.data.user));
        } catch (error) {
          dispatch(logout());
        }
      } else {
        dispatch(setLoading(false));
      }
    };

    loadUser();
  }, [dispatch, token]);

  return (
    <ErrorBoundary>
      <Router />
    </ErrorBoundary>
  );
}

export default App;
