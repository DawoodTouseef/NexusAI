import React, { useState ,useContext} from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import "./sign-in.css";
import envCompatible from "vite-plugin-env-compatible";
import { assets  } from "../../assets/assets";
import { Context } from "../../context/Context";


// Access the environment variable
const url = assets.API_URL;

const SignIn = () => {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });
  const {
    setAuthenticated,
  } = useContext(Context);
  const [username, setUsername] = useState("");

  const [errors, setErrors] = useState({});

  const submit = async (e) => {
    e.preventDefault();
    const user = {
      username: username,
      password: formData.password,
    };
    try {
      // Create the POST request
      const { data } = await axios.post(`${url}/token/`, user, {
        headers: { "Content-Type": "application/json" },
      });
      // Initialize the access & refresh token in localStorage.
      localStorage.clear();
      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);
      localStorage.setItem("isAuthenticate",true)
      axios.defaults.headers.common[
        "Authorization"
      ] = `Bearer ${data["access"]}`;
      window.location.href = "/";
    } catch (error) {
      // Handle errors here
      console.error("There was an error logging in:", error);
      localStorage.setItem("isAuthenticate",false)
      setErrors({
        submit:
          "Failed to sign in. Please check your credentials and try again.",
      });
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = {};
    if (!username.trim()) {
      validationErrors.username = "Username is required";
    }

    if (!formData.password.trim()) {
      validationErrors.password = "Password is required";
    }

    setErrors(validationErrors);

    if (Object.keys(validationErrors).length === 0) {
      submit(e); // Call the submit function if there are no validation errors
    }
  };

  return (
    <div className="signin-container">
      <form onSubmit={handleSubmit} className="signin-form">
        <h2>Sign In</h2>
        <div className="form-group">
          <label>Username:</label>
          <input
            type="text"
            name="Username"
            placeholder="username"
            autoComplete="off"
            // value={formData.email}
            onChange={(e) => {
              setUsername(e.target.value);
            }}
          />
          {errors.username && <span>{errors.username}</span>}
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input
            type="password"
            name="password"
            placeholder="******"
            value={formData.password}
            onChange={handleChange}
          />
          {errors.password && (
            <span className="error-message">{errors.password}</span>
          )}
        </div>
        {errors.submit && (
          <span className="error-message">{errors.submit}</span>
        )}
        <button type="submit" className="submit-btn">
          Submit
        </button>
        <p className="signup-link">
          Don't have an account? <Link to="/sign-up">Sign up</Link>
        </p>
      </form>
    </div>
  );
};

export default SignIn;
