// auth.jsx
import axiosInstance from './axios';
import { jwtDecode } from 'jwt-decode';

export const getToken = () => {
  return localStorage.getItem('access_token');
};

export const removeTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const getUserInfoFromToken = async(token) => {
  // Decode the JWT token and return user info
  try {
    const decodedToken = jwtDecode(token);
    return decodedToken;
  } catch (error) {
    console.error("Invalid token:", error);
    return null;
  }
};

export const isTokenValid = (token) => {
  // Check if the token is valid
  try {
    const decodedToken = jwtDecode(token);
    const currentTime = Date.now() / 1000;
    return decodedToken.exp > currentTime;
  } catch (error) {
    console.error("Invalid token:", error);
    return false;
  }
};

export const refreshToken = async () => {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return null;
    }

    const response = await axiosInstance.post('/token/refresh/', { refresh: refreshToken });
    const newAccessToken = response.data.access;
    localStorage.setItem('access_token', newAccessToken);
    return newAccessToken;
  } catch (error) {
    console.error('Token refresh error:', error);
    return null;
  }
};
