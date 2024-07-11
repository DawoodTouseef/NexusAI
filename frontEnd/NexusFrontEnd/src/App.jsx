import React ,{useState,useEffect}from "react";
import Sidebar from "./components/Sidebar/Sidebar";
import Mane from "./components/Main/Mane";
import Signup from "./components/auth/sign-up";
import SignIn from "./components/auth/sign-in";
import { assets  } from "../src/assets/assets";
import { getToken, removeTokens, getUserInfoFromToken, isTokenValid } from '../src/utils/auth.jsx';
import PrivateRoute from './components/Privateroute';
import { Router} from 'react-router-dom';
import axiosInstance from './utils/axios';
const Home =({isAuthenticated})=>{
  return(
    <>
    <Sidebar/>
    <Mane isAuthenticated={isAuthenticated}/>
    </>
  );
}

const url=assets.API_URL;
const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    const token = getToken();
    if (token && isTokenValid(token)) {
      setIsAuthenticated(true);
      setUserInfo(getUserInfoFromToken(token));
    } else {
      removeTokens();
      
    }
  }, []);

  const handleLogout = () => {
    removeTokens();
    setIsAuthenticated(false);
  };
  return(
    <>
    {isAuthenticated ? <Home isAuthenticated={isAuthenticated}/>:(<SignIn></SignIn>)}
    </>
  );
};

export default App;
