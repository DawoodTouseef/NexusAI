import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar/Sidebar";
import Mane from "./components/Main/Mane";
import SignIn from "./components/auth/sign-in";
import { assets } from "../src/assets/assets";
import { getToken, removeTokens, getUserInfoFromToken, isTokenValid, refreshToken } from '../src/utils/auth.jsx';
import axiosInstance from './utils/axios';

const Home = ({ isAuthenticated }) => {
  return (
    <>
      <Sidebar />
      <Mane isAuthenticated={isAuthenticated} />
    </>
  );
}

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  useEffect(() => {
    const token = getToken();
    if (token && isTokenValid(token)) {
      setIsAuthenticated(true);
      localStorage.setItem('isAuthenticated',true);
      setUserInfo(getUserInfoFromToken(token));
    } 
    else if (token && !isTokenValid(token)){
      refreshAuthToken();
    }
    else if(isTokenValid(token)){
        console.log("Token is not valid");
    }
  }, []);

  const refreshAuthToken = async () => {
    try {
      const newToken = await refreshToken();
      if (newToken) {
        setIsAuthenticated(true);
        setUserInfo(getUserInfoFromToken(newToken));
      } else {
        handleLogout();
      }
    } catch (error) {
      handleLogout();
    }
  };

  const handleLogout = () => {
    removeTokens();
    localStorage.setItem('isAuthenticated',false);
    setIsAuthenticated(false);
  };

  useEffect(() => {
    const interceptors = axiosInstance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          const newToken = await refreshToken();
          if (newToken) {
            axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
            return axiosInstance(originalRequest);
          } else {
            handleLogout();
          }
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axiosInstance.interceptors.response.eject(interceptors);
    };
  }, []);
  return (
    <>
      {isAuthenticated ? <Home isAuthenticated={isAuthenticated} /> : <SignIn />}
    </>
  );
};

export default App;
