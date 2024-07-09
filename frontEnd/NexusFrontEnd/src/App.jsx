import React from "react";
import Sidebar from "./components/Sidebar/Sidebar";
import Mane from "./components/Main/Mane";
import Signup from "./components/auth/sign-up";
import { assets  } from "../src/assets/assets";

const url=assets.API_URL;
const App = () => {
  return (
    <>
      <Sidebar />
      <Mane />
    </>
  );
};

export default App;
