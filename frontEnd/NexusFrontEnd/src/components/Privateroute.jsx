// PrivateRoute.js
import { Route, useNavigate} from 'react-router-dom';

const PrivateRoute = ({ component: Component, isAuthenticated, ...rest }) => {
    const navigate=useNavigate()
  return (
    <Route
      {...rest}
      render={props =>
        isAuthenticated ? (
          <Component {...props} />
        ) : (
         <>
         {navigate('/login')}
         </>
        )
      }
    />
  );
};

export default PrivateRoute;
