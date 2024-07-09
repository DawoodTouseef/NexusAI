import React, { useState } from "react";
import { Link } from "react-router-dom"; // Import Link from React Router
import "./Styles.css";

const FormValidationExample = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    profileImage: null,
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value, files } = e.target;

    if (name === "profileImage") {
      setFormData({
        ...formData,
        profileImage: files[0],
      });
    } else {
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = {};

    if (!formData.username.trim()) {
      validationErrors.username = "Username is required";
    }

    if (!formData.email.trim()) {
      validationErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      validationErrors.email = "Email is not valid";
    }

    if (!formData.password.trim()) {
      validationErrors.password = "Password is required";
    } else if (formData.password.length < 6) {
      validationErrors.password = "Password should be at least 6 characters";
    }

    if (formData.confirmPassword !== formData.password) {
      validationErrors.confirmPassword = "Passwords do not match";
    }

    if (!formData.profileImage) {
      validationErrors.profileImage = "Profile image is required";
    } else {
      const allowedExtensions = ["jpg", "jpeg", "png", "gif"];
      const fileExtension = formData.profileImage.name
        .split(".")
        .pop()
        .toLowerCase();
      if (!allowedExtensions.includes(fileExtension)) {
        validationErrors.profileImage =
          "Only JPG, JPEG, PNG, and GIF files are allowed";
      }
    }

    setErrors(validationErrors);

    if (Object.keys(validationErrors).length === 0) {
      alert("Form Submitted successfully");
      // Proceed with form submission logic (e.g., API call)
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Username:</label>
        <input
          type="text"
          name="username"
          placeholder="Username"
          autoComplete="off"
          onChange={handleChange}
        />
        {errors.username && <span>{errors.username}</span>}
      </div>
      <div>
        <label>Email:</label>
        <input
          type="email"
          name="email"
          placeholder="example@gmail.com"
          autoComplete="off"
          onChange={handleChange}
        />
        {errors.email && <span>{errors.email}</span>}
      </div>
      <div>
        <label>Password:</label>
        <input
          type="password"
          name="password"
          placeholder="******"
          onChange={handleChange}
        />
        {errors.password && <span>{errors.password}</span>}
      </div>
      <div>
        <label>Confirm Password:</label>
        <input
          type="password"
          name="confirmPassword"
          placeholder="******"
          onChange={handleChange}
        />
        {errors.confirmPassword && <span>{errors.confirmPassword}</span>}
      </div>
      <div>
        <label>Profile Image:</label>
        <input
          type="file"
          name="profileImage"
          onChange={handleChange}
          accept="image/jpeg, image/png, image/gif"
        />
        {errors.profileImage && <span>{errors.profileImage}</span>}
      </div>
      <button type="submit">Submit</button>
      <p>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </form>
  );
};

export default FormValidationExample;
