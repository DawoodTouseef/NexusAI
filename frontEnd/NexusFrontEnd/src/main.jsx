import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
import ContextProvider from "./context/Context.jsx";
import { createBrowserRouter, RouterProvider} from "react-router-dom";
import FormValidationExample from "./components/auth/sign-up.jsx";
import SignIn from "./components/auth/sign-in.jsx";
import DyanamicMain  from "./components/Main/APPMAIN.jsx";
import Sidebar from "./components/Sidebar/Sidebar.jsx";


const Logout = () => {
  localStorage.clear();
  window.location.href = "/";
};
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
  {
    path:"app/:title_id",
    element:<>
    <Sidebar></Sidebar>
    <DyanamicMain></DyanamicMain>
    </>
  },
  {
    path:"/logout",
    element:<Logout/>
  },
]);

ReactDOM.createRoot(document.getElementById("root")).render(
  <ContextProvider>
    <RouterProvider router={router} />
  </ContextProvider>
);
