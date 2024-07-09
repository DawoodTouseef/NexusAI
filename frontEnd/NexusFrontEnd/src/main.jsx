import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
import ContextProvider from "./context/Context.jsx";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import FormValidationExample from "./components/auth/sign-up.jsx";
import SignIn from "./components/auth/sign-in.jsx";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/sign-up",
    element: <FormValidationExample></FormValidationExample>,
  },
  {
    path: "/login",
    element: <SignIn></SignIn>,
  },
]);

ReactDOM.createRoot(document.getElementById("root")).render(
  <ContextProvider>
    <RouterProvider router={router} />
  </ContextProvider>
);
